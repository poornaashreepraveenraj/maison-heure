"""Very small cache-based rate limiter (fixed window per client IP).

Limits are configured in settings.RATE_LIMITS as name -> (max hits, seconds).
"""
from django.conf import settings
from django.core.cache import cache
from django.http import JsonResponse
from django.shortcuts import render


def client_ip(request):
    # Vercel sits behind a proxy and puts the real client first in X-Forwarded-For.
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "unknown")


def _key(request, name):
    return f"ratelimit:{name}:{client_ip(request)}"


def is_limited(request, name):
    limit, _ = settings.RATE_LIMITS[name]
    return cache.get(_key(request, name), 0) >= limit


def hit(request, name):
    """Record one hit; returns the new count for the current window."""
    _, window = settings.RATE_LIMITS[name]
    key = _key(request, name)
    cache.add(key, 0, window)  # only sets (and starts the window) if missing
    try:
        return cache.incr(key)
    except ValueError:  # key expired between add and incr
        cache.set(key, 1, window)
        return 1


def too_many_requests(request, what="requests"):
    if request.path.startswith("/api/"):
        response = JsonResponse(
            {"error": "Too Many Requests", "code": 429, "answer": f"You've sent a lot of {what} in a short time. Please wait a minute and try again."},
            status=429,
        )
    else:
        response = render(request, "errors/429.html", {"what": what}, status=429)
    response["Retry-After"] = "60"
    return response
