from datetime import timedelta
from decimal import Decimal, InvalidOperation

from django.core.paginator import Paginator
from django.db.models import Max, Min, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.template.loader import render_to_string
from django.utils import timezone

from cart.bag import Bag

from .models import Brand, Watch, Wishlist

PAGE_SIZE = 8
TAB_BRANDS = ["rolex", "omega", "cartier", "patek-philippe", "audemars-piguet"]
CASE_SIZES = {
    "s": ("Under 37 mm", Q(case_size_mm__lt=37)),
    "m": ("37 – 40 mm", Q(case_size_mm__gte=37, case_size_mm__lt=41)),
    "l": ("41 – 43 mm", Q(case_size_mm__gte=41, case_size_mm__lt=44)),
    "xl": ("44 mm +", Q(case_size_mm__gte=44)),
}
# Unisex watches are shown in both the Men's and Women's edits.
GENDER_FILTERS = {
    "men": [Watch.Gender.MEN, Watch.Gender.UNISEX],
    "women": [Watch.Gender.WOMEN, Watch.Gender.UNISEX],
    "unisex": [Watch.Gender.UNISEX],
}
SORTS = {
    "newest": ("Newest", "-created_at"),
    "price_asc": ("Price: low to high", "price_inr"),
    "price_desc": ("Price: high to low", "-price_inr"),
}


def _wishlist_ids(request):
    if request.user.is_authenticated:
        return set(Wishlist.objects.filter(user=request.user).values_list("watch_id", flat=True))
    return set()


def _card_context(request):
    return {"bag_ids": set(Bag(request).ids), "wishlist_ids": _wishlist_ids(request)}


def _to_decimal(value):
    try:
        return Decimal(value)
    except (InvalidOperation, TypeError):
        return None


def _to_int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def filter_watches(params):
    """Apply the shop filters from a QueryDict. Unknown/invalid values are ignored."""
    qs = Watch.objects.visible()

    q = params.get("q", "").strip()
    if q:
        qs = qs.filter(
            Q(model__icontains=q) | Q(brand__name__icontains=q) | Q(reference_number__icontains=q)
        )
    if brands := params.getlist("brand"):
        qs = qs.filter(brand__slug__in=brands)
    if style := params.get("style"):
        qs = qs.filter(style=style)
    genders = {g for key in params.getlist("gender") for g in GENDER_FILTERS.get(key, [])}
    if genders:
        qs = qs.filter(gender__in=genders)
    if (price_min := _to_decimal(params.get("price_min"))) is not None:
        qs = qs.filter(price_inr__gte=price_min)
    if (price_max := _to_decimal(params.get("price_max"))) is not None:
        qs = qs.filter(price_inr__lte=price_max)
    sizes = [CASE_SIZES[s][1] for s in params.getlist("size") if s in CASE_SIZES]
    if sizes:
        size_q = Q()
        for condition in sizes:
            size_q |= condition
        qs = qs.filter(size_q)
    if movements := params.getlist("movement"):
        qs = qs.filter(movement__in=movements)
    if conditions := params.getlist("condition"):
        qs = qs.filter(condition__in=conditions)
    if (year_min := _to_int(params.get("year_min"))) is not None:
        qs = qs.filter(year__gte=year_min)
    if (year_max := _to_int(params.get("year_max"))) is not None:
        qs = qs.filter(year__lte=year_max)
    if params.get("papers") == "1":
        qs = qs.filter(box_and_papers=True)
    if params.get("available") == "1":
        qs = qs.filter(status=Watch.Status.AVAILABLE)

    sort = params.get("sort", "newest")
    order = SORTS.get(sort, SORTS["newest"])[1]
    return qs.order_by(order, "pk")


def _shop_heading(genders):
    if len(genders) == 1 and genders[0] in GENDER_FILTERS:
        return f"{dict(Watch.Gender.choices)[genders[0]]} watches"
    return "Shop all watches"


def home(request):
    Watch.objects.release_expired()
    watches = Watch.objects.visible()
    tab_brands = sorted(Brand.objects.filter(slug__in=TAB_BRANDS), key=lambda b: TAB_BRANDS.index(b.slug))
    styles = []
    for value, label in Watch.Style.choices:
        sample = watches.filter(style=value).first()
        styles.append({"value": value, "label": label, "count": watches.filter(style=value).count(), "sample": sample})
    wearers = []
    for value, label in Watch.Gender.choices:
        in_edit = watches.filter(gender__in=GENDER_FILTERS[value])
        # Show a piece made specifically for that wearer on the tile.
        sample = watches.filter(gender=value, status=Watch.Status.AVAILABLE).order_by("-featured", "pk").first()
        wearers.append({"value": value, "label": label, "count": in_edit.count(), "sample": sample})
    context = {
        "tab_brands": tab_brands,
        "new_in": watches.order_by("-created_at", "pk")[:8],
        "styles": styles,
        "wearers": wearers,
        "brands": Brand.objects.all(),
        **_card_context(request),
    }
    return render(request, "store/home.html", context)


def shop(request):
    Watch.objects.release_expired()
    qs = filter_watches(request.GET)
    page = Paginator(qs, PAGE_SIZE).get_page(request.GET.get("page"))

    # Query string without "page", used by the "Load more" button.
    params = request.GET.copy()
    params.pop("page", None)
    params.pop("partial", None)

    context = {
        "page": page,
        "watches": page.object_list,
        "querystring": params.urlencode(),
        "heading": _shop_heading(request.GET.getlist("gender")),
        **_card_context(request),
    }
    if request.GET.get("partial") == "1":
        return render(request, "store/_cards.html", context)

    bounds = Watch.objects.aggregate(
        price_min=Min("price_inr"), price_max=Max("price_inr"), year_min=Min("year"), year_max=Max("year")
    )
    context.update(
        {
            "brands": Brand.objects.all(),
            "case_sizes": [(key, label) for key, (label, _) in CASE_SIZES.items()],
            "genders": Watch.Gender.choices,
            "movements": Watch.Movement.choices,
            "conditions": Watch.Condition.choices,
            "sorts": [(key, label) for key, (label, _) in SORTS.items()],
            "bounds": {k: int(v) if v is not None else 0 for k, v in bounds.items()},
            "selected": {
                "brand": request.GET.getlist("brand"),
                "size": request.GET.getlist("size"),
                "movement": request.GET.getlist("movement"),
                "condition": request.GET.getlist("condition"),
                "gender": request.GET.getlist("gender"),
            },
            "total": page.paginator.count,
        }
    )
    return render(request, "store/shop.html", context)


def watch_detail(request, slug):
    Watch.objects.release_expired()
    watch = get_object_or_404(Watch.objects.visible(), slug=slug)
    related = (
        Watch.objects.visible()
        .filter(Q(brand=watch.brand) | Q(style=watch.style))
        .exclude(pk=watch.pk)
        .order_by("status", "-featured", "-created_at")[:4]
    )
    today = timezone.localdate()
    context = {
        "watch": watch,
        "related": related,
        "in_bag": watch.pk in Bag(request).ids,
        "in_wishlist": watch.pk in _wishlist_ids(request),
        "delivery_from": today + timedelta(days=2),
        "delivery_to": today + timedelta(days=3),
        **_card_context(request),
    }
    return render(request, "store/watch_detail.html", context)


def about(request):
    return render(request, "store/about.html")


def api_watch_status(request, slug):
    """Live availability for one watch; the product page polls this every 15 seconds."""
    Watch.objects.release_expired()
    watch = get_object_or_404(Watch, slug=slug)
    return JsonResponse({"slug": watch.slug, "status": watch.status, "is_available": bool(watch.is_available)})


def api_watches(request):
    """JSON list of watches, used by the landing-page brand tabs (no page reload)."""
    Watch.objects.release_expired()
    qs = Watch.objects.visible().order_by("-created_at", "pk")
    brand = request.GET.get("brand", "")
    if brand and brand != "all":
        qs = qs.filter(brand__slug=brand)
    if gender := request.GET.get("gender"):
        qs = qs.filter(gender__in=GENDER_FILTERS.get(gender, []))
    limit = min(_to_int(request.GET.get("limit")) or 8, 24)
    watches = list(qs[:limit])
    results = [
        {
            "slug": w.slug,
            "brand": w.brand.name,
            "model": w.model,
            "reference_number": w.reference_number,
            "price_inr": int(w.price_inr),
            "condition": w.get_condition_display(),
            "gender": w.gender,
            "status": w.status,
            "url": w.get_absolute_url(),
            "image": w.primary_image.url if w.primary_image else "",
        }
        for w in watches
    ]
    html = render_to_string("store/_cards.html", {"watches": watches, **_card_context(request)}, request=request)
    return JsonResponse({"count": len(results), "results": results, "html": html})
