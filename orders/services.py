"""Checkout business logic, kept out of the views so it is easy to test and explain."""
import logging
import secrets
from datetime import timedelta

from django.core.mail import send_mail
from django.db import transaction
from django.template.loader import render_to_string
from django.utils import timezone

from cart.bag import Bag, WatchUnavailable, holder_key
from cart.pricing import DELIVERY_OPTIONS, compute_totals
from store.models import Watch

from .models import Order, OrderItem

logger = logging.getLogger("maisonheure.orders")

DEMO_COURIER = "Insured Courier (demo)"


def reserve_bag_items(request):
    """Hold every watch in the bag for 15 minutes while the shopper checks out.

    Rows are locked with select_for_update so two shoppers can't grab the same
    watch at the same moment. Raises WatchUnavailable (error 470) if any watch
    is already sold or held by someone else.
    """
    Watch.objects.release_expired()
    key = holder_key(request)
    bag = Bag(request)
    with transaction.atomic():
        watches = list(Watch.objects.select_for_update().filter(pk__in=bag.ids).order_by("pk"))
        unavailable = [w for w in watches if not w.can_be_bought_by(key)]
        if unavailable:
            raise WatchUnavailable(unavailable)
        for watch in watches:
            watch.reserve_for(key)
    return watches


def _tracking_number():
    return "MHX" + "".join(secrets.choice("0123456789") for _ in range(9))


def place_order(request, shipping, delivery):
    """Create the order atomically and mark its watches as sold.

    Prices and totals come from the database, never from the browser.
    """
    key = holder_key(request)
    bag = Bag(request)
    with transaction.atomic():
        watches = list(
            Watch.objects.select_for_update().select_related("brand").filter(pk__in=bag.ids).order_by("pk")
        )
        if not watches:
            raise ValueError("The bag is empty.")
        unavailable = [w for w in watches if not w.can_be_bought_by(key)]
        if unavailable:
            raise WatchUnavailable(unavailable)

        totals = compute_totals(watches, bag.promo_code, delivery)
        option = DELIVERY_OPTIONS[totals["delivery"]]
        order = Order.objects.create(
            user=request.user,
            email=shipping["email"],
            ship_name=shipping["name"],
            ship_phone=shipping["phone"],
            ship_line1=shipping["line1"],
            ship_line2=shipping.get("line2", ""),
            ship_city=shipping["city"],
            ship_state=shipping["state"],
            ship_pincode=shipping["pincode"],
            delivery_method=totals["delivery"],
            subtotal=totals["subtotal"],
            shipping=totals["shipping"],
            tax=totals["tax"],
            discount=totals["discount"],
            promo_code=totals["promo_code"],
            total=totals["total"],
            payment_status=Order.PaymentStatus.PAID,
            courier=DEMO_COURIER,
            tracking_number=_tracking_number(),
            estimated_delivery=timezone.localdate() + timedelta(days=option["max_days"]),
        )
        OrderItem.objects.bulk_create(
            [OrderItem(order=order, watch=w, price_at_purchase=w.price_inr) for w in watches]
        )
        Watch.objects.filter(pk__in=[w.pk for w in watches]).update(
            status=Watch.Status.SOLD, reserved_until=None, reserved_by=""
        )
        order.events.create(status=Order.Status.PLACED, note="Order placed and payment confirmed (demo).")
        transaction.on_commit(lambda: send_confirmation_email(order.pk))

    bag.clear()
    logger.info("order placed ref=%s items=%s total=%s", order.reference, len(watches), order.total)
    return order


def send_confirmation_email(order_id):
    order = Order.objects.prefetch_related("items__watch__brand").get(pk=order_id)
    body = render_to_string("orders/email_confirmation.txt", {"order": order})
    try:
        send_mail(f"Your Maison Heure order {order.reference}", body, None, [order.email])
    except Exception:  # email must never break checkout
        logger.exception("confirmation email failed ref=%s", order.reference)
