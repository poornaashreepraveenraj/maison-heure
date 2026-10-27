from store.catalogue_data import BRANDS

from .rates import CURRENCIES

QUICK_REPLIES = ["Is it authentic?", "Track my order", "Error 470", "Return policy"]


def site(request):
    # No database queries here: this runs on every page, including the 500 page.
    return {"chat_quick_replies": QUICK_REPLIES, "currencies": CURRENCIES, "nav_brands": BRANDS}
