from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from cart.bag import Bag, WatchUnavailable
from cart.pricing import DEFAULT_DELIVERY, DELIVERY_OPTIONS, compute_totals
from cart.views import render_470
from support import ratelimit

from .forms import DeliveryForm, ShippingForm, TrackOrderForm
from .models import Address, Order
from .services import place_order, reserve_bag_items

CHECKOUT_KEY = "checkout"
TRACKED_KEY = "tracked_orders"


def _checkout_state(request):
    return request.session.setdefault(CHECKOUT_KEY, {})


def _checkout_context(request, step, watches):
    state = _checkout_state(request)
    totals = compute_totals(watches, Bag(request).promo_code, state.get("delivery", DEFAULT_DELIVERY))
    held_until = min((w.reserved_until for w in watches if w.reserved_until), default=None)
    return {"step": step, "watches": watches, "totals": totals, "held_until": held_until}


def _start_checkout(request):
    """Shared guard for every checkout step: bag not empty, items still holdable."""
    if not Bag(request).ids:
        messages.info(request, "Your bag is empty.")
        return None, redirect("cart:bag")
    try:
        return reserve_bag_items(request), None
    except WatchUnavailable as exc:
        return None, render_470(request, exc.watches)


@login_required
def checkout_shipping(request):
    watches, response = _start_checkout(request)
    if response:
        return response
    state = _checkout_state(request)

    if request.method == "POST":
        form = ShippingForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            save = data.pop("save_address")
            state["shipping"] = data
            request.session.modified = True
            if save:
                request.user.addresses.update(is_default=False)
                Address.objects.create(
                    user=request.user, is_default=True, **{k: v for k, v in data.items() if k != "email"}
                )
            return redirect("orders:checkout_delivery")
    else:
        initial = state.get("shipping")
        if not initial:
            initial = {"email": request.user.email, "name": request.user.get_full_name()}
            address = request.user.addresses.first()
            if address:
                initial.update(
                    name=address.name, phone=address.phone, line1=address.line1, line2=address.line2,
                    city=address.city, state=address.state, pincode=address.pincode,
                )
        form = ShippingForm(initial=initial)

    context = _checkout_context(request, "shipping", watches)
    context["form"] = form
    return render(request, "orders/checkout_shipping.html", context)


@login_required
def checkout_delivery(request):
    watches, response = _start_checkout(request)
    if response:
        return response
    state = _checkout_state(request)
    if "shipping" not in state:
        return redirect("orders:checkout")

    if request.method == "POST":
        form = DeliveryForm(request.POST)
        if form.is_valid():
            state["delivery"] = form.cleaned_data["delivery"]
            request.session.modified = True
            return redirect("orders:checkout_payment")
    else:
        form = DeliveryForm(initial={"delivery": state.get("delivery", DEFAULT_DELIVERY)})

    context = _checkout_context(request, "delivery", watches)
    context.update(form=form, options=DELIVERY_OPTIONS)
    return render(request, "orders/checkout_delivery.html", context)


@login_required
def checkout_payment(request):
    watches, response = _start_checkout(request)
    if response:
        return response
    state = _checkout_state(request)
    if "shipping" not in state:
        return redirect("orders:checkout")
    if "delivery" not in state:
        return redirect("orders:checkout_delivery")

    if request.method == "POST":
        # Demo payment only: no card data is ever collected or stored.
        if request.POST.get("outcome") == "fail":
            messages.error(request, "Payment declined (demo). Your watches are still held for you — try again.")
            return redirect("orders:checkout_payment")
        try:
            order = place_order(request, state["shipping"], state["delivery"])
        except WatchUnavailable as exc:
            return render_470(request, exc.watches)
        request.session.pop(CHECKOUT_KEY, None)
        return redirect("orders:confirmed", reference=order.reference)

    context = _checkout_context(request, "payment", watches)
    context["shipping"] = state["shipping"]
    context["delivery_option"] = DELIVERY_OPTIONS[state["delivery"]]
    return render(request, "orders/checkout_payment.html", context)


def _owned_order(request, reference):
    order = get_object_or_404(Order.objects.prefetch_related("items__watch__brand", "items__watch__images", "events"), reference=reference)
    if not (request.user.is_staff or order.user_id == request.user.pk):
        raise PermissionDenied("This order belongs to another account.")
    return order


@login_required
def order_confirmed(request, reference):
    order = _owned_order(request, reference)
    return render(request, "orders/confirmed.html", {"order": order})


def order_detail(request, reference):
    """Owners and staff can always view; guests only after a successful /track/ lookup."""
    if reference in request.session.get(TRACKED_KEY, []):
        order = get_object_or_404(
            Order.objects.prefetch_related("items__watch__brand", "items__watch__images", "events"), reference=reference
        )
    elif request.user.is_authenticated:
        order = _owned_order(request, reference)
    else:
        return redirect(f"{reverse('orders:track')}?ref={reference}")
    return render(request, "orders/order_detail.html", {"order": order, "timeline": order.timeline()})


@login_required
def my_orders(request):
    orders = request.user.orders.prefetch_related("items__watch__brand", "items__watch__images")
    return render(request, "orders/my_orders.html", {"orders": orders})


def track_order(request):
    if ratelimit.is_limited(request, "track"):
        return ratelimit.too_many_requests(request, "order lookups")

    if request.method == "POST":
        form = TrackOrderForm(request.POST)
        if form.is_valid():
            order = Order.objects.filter(
                reference__iexact=form.cleaned_data["reference"], email__iexact=form.cleaned_data["email"]
            ).first()
            if order:
                tracked = request.session.get(TRACKED_KEY, [])
                if order.reference not in tracked:
                    tracked.append(order.reference)
                request.session[TRACKED_KEY] = tracked[-10:]
                return redirect("orders:detail", reference=order.reference)
            ratelimit.hit(request, "track")
            messages.error(request, "We couldn't find an order with that reference and email. Please check both and try again.")
    else:
        form = TrackOrderForm(initial={"reference": request.GET.get("ref", "")})
    return render(request, "orders/track.html", {"form": form})
