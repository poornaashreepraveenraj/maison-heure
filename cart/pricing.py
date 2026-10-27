"""All money maths lives here so the bag and checkout always agree.

Totals are always recomputed on the server from database prices; any total
sent by the browser is ignored.
"""
from decimal import ROUND_HALF_UP, Decimal

DELIVERY_OPTIONS = {
    "standard": {"label": "Insured standard", "days": "5–7 business days", "min_days": 5, "max_days": 7, "price": Decimal("1500")},
    "express": {"label": "Insured express", "days": "2–3 business days", "min_days": 2, "max_days": 3, "price": Decimal("3500")},
}
DEFAULT_DELIVERY = "standard"

# Demo promo codes: code -> fractional discount
PROMO_CODES = {"WELCOME10": Decimal("0.10")}

# Pre-owned goods in India can be taxed under the GST margin scheme: GST is
# charged on the dealer's margin, not the full price. We assume a 15% margin
# for this demo, so the tax line is 18% x 15% of the discounted price.
GST_RATE = Decimal("0.18")
ASSUMED_DEALER_MARGIN = Decimal("0.15")


def _money(value):
    return value.quantize(Decimal("1"), rounding=ROUND_HALF_UP)


def normalise_promo(code):
    code = (code or "").strip().upper()
    return code if code in PROMO_CODES else ""


def compute_totals(watches, promo_code="", delivery=DEFAULT_DELIVERY):
    subtotal = sum((w.price_inr for w in watches), Decimal("0"))
    promo_code = normalise_promo(promo_code)
    discount = _money(subtotal * PROMO_CODES.get(promo_code, Decimal("0")))
    option = DELIVERY_OPTIONS.get(delivery, DELIVERY_OPTIONS[DEFAULT_DELIVERY])
    shipping = option["price"] if watches else Decimal("0")
    tax = _money((subtotal - discount) * ASSUMED_DEALER_MARGIN * GST_RATE)
    return {
        "subtotal": _money(subtotal),
        "discount": discount,
        "promo_code": promo_code,
        "shipping": shipping,
        "tax": tax,
        "total": _money(subtotal - discount + shipping + tax),
        "delivery": delivery if delivery in DELIVERY_OPTIONS else DEFAULT_DELIVERY,
    }
