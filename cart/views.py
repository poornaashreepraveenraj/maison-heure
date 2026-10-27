from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from store.models import Watch

from .bag import Bag, holder_key
from .pricing import compute_totals, normalise_promo

WATCH_SOLD_STATUS = 470
WATCH_SOLD_REASON = "Watch Already Sold"


def wants_json(request):
    return request.headers.get("x-requested-with") == "fetch" or "application/json" in request.headers.get("accept", "")


def render_470(request, watches):
    """Site-specific error 470: the watch was sold or reserved by someone else."""
    watches = list(watches)
    if wants_json(request):
        return JsonResponse(
            {
                "error": WATCH_SOLD_REASON,
                "code": WATCH_SOLD_STATUS,
                "message": "Sorry — this watch was just bought or reserved by another collector.",
                "watches": [w.slug for w in watches],
            },
            status=WATCH_SOLD_STATUS,
        )
    response = render(request, "errors/470.html", {"unavailable": watches}, status=WATCH_SOLD_STATUS)
    response.reason_phrase = WATCH_SOLD_REASON
    return response


def bag_detail(request):
    Watch.objects.release_expired()
    bag = Bag(request)
    key = holder_key(request)
    watches = bag.watches()
    available = [w for w in watches if w.can_be_bought_by(key)]
    unavailable = [w for w in watches if not w.can_be_bought_by(key)]
    context = {
        "watches": available,
        "unavailable": unavailable,
        "totals": compute_totals(available, bag.promo_code),
        "promo_code": bag.promo_code,
    }
    return render(request, "cart/bag.html", context)


@require_POST
def bag_add(request, watch_id):
    Watch.objects.release_expired()
    watch = get_object_or_404(Watch.objects.visible(), pk=watch_id)
    if not watch.can_be_bought_by(holder_key(request)):
        return render_470(request, [watch])

    bag = Bag(request)
    bag.add(watch)
    if wants_json(request):
        return JsonResponse({"ok": True, "count": len(bag), "message": f"{watch.title} added to your bag."})
    if request.POST.get("express"):
        return redirect("orders:checkout")
    messages.success(request, f"{watch.title} added to your bag.")
    return redirect("cart:bag")


@require_POST
def bag_remove(request, watch_id):
    bag = Bag(request)
    bag.remove(watch_id)
    if wants_json(request):
        return JsonResponse({"ok": True, "count": len(bag)})
    messages.info(request, "Removed from your bag.")
    return redirect("cart:bag")


@require_POST
def apply_promo(request):
    bag = Bag(request)
    raw = request.POST.get("code", "")
    code = normalise_promo(raw)
    if raw and not code:
        messages.error(request, "That promo code isn't valid.")
    elif code:
        messages.success(request, f"Promo code {code} applied.")
    else:
        messages.info(request, "Promo code removed.")
    bag.promo_code = code
    return redirect("cart:bag")
