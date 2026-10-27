"""Currency exchange rates: the extra third-party API, with a time limit and a fallback.

- Calls open.er-api.com with a 3-second timeout.
- Caches a good answer in memory for 10 minutes.
- On any failure (timeout, DNS, bad JSON...) returns static fallback rates.
"""
import json
import logging
import time
import urllib.request

from django.conf import settings

logger = logging.getLogger("maisonheure.rates")

TIMEOUT_SECONDS = 3
CACHE_SECONDS = 10 * 60
CURRENCIES = ["INR", "USD", "EUR", "GBP", "AED"]

# Approximate INR -> X rates, used only when the live API is unavailable.
FALLBACK_RATES = {"INR": 1.0, "USD": 0.0119, "EUR": 0.0103, "GBP": 0.0089, "AED": 0.0437}

_cache = {"data": None, "fetched_at": 0.0}


def _fetch_live():
    request = urllib.request.Request(settings.FX_API_URL, headers={"User-Agent": "MaisonHeure/1.0"})
    with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
        payload = json.loads(response.read().decode("utf-8"))
    if payload.get("result") != "success":
        raise ValueError("FX API returned an error")
    rates = payload["rates"]
    return {code: float(rates[code]) for code in CURRENCIES}


def get_rates():
    now = time.monotonic()
    if _cache["data"] and now - _cache["fetched_at"] < CACHE_SECONDS:
        return _cache["data"]
    try:
        data = {"base": "INR", "rates": _fetch_live(), "source": "live"}
        _cache.update(data=data, fetched_at=now)
        return data
    except Exception as exc:
        logger.warning("FX rates unavailable, using fallback: %s", exc.__class__.__name__)
        # Not cached, so the next request retries the live API.
        return {"base": "INR", "rates": dict(FALLBACK_RATES), "source": "fallback"}


def clear_cache():
    _cache.update(data=None, fetched_at=0.0)
