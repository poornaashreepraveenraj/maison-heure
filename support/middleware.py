import logging
import time

from .ratelimit import client_ip

logger = logging.getLogger("maisonheure.requests")


class RequestLoggingMiddleware:
    """Logs one line per request to stdout (visible in Vercel's runtime logs).

    Only the path is logged — never query strings, form data, passwords or tokens.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        started = time.perf_counter()
        response = self.get_response(request)
        duration_ms = (time.perf_counter() - started) * 1000
        user = getattr(request, "user", None)
        username = user.username if user is not None and user.is_authenticated else "anonymous"
        logger.info(
            "method=%s path=%s status=%s duration_ms=%.1f user=%s ip=%s",
            request.method,
            request.path,
            response.status_code,
            duration_ms,
            username,
            client_ip(request),
        )
        return response
