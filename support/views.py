import json
import logging
import time
from itertools import groupby

from django.conf import settings
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.db import connection
from django.http import HttpResponseServerError, JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_GET, require_POST

from . import mongo, ratelimit
from .assistant import answer_question
from .forms import ContactForm
from .models import FAQ, ErrorCode
from .rates import get_rates

logger = logging.getLogger("maisonheure.support")
STARTED_AT = time.time()


# --- Content pages -------------------------------------------------------------------

def faq(request):
    faqs = FAQ.objects.filter(is_published=True).order_by("category", "order", "pk")
    groups = [(category, list(items)) for category, items in groupby(faqs, key=lambda f: f.category)]
    return render(request, "support/faq.html", {"groups": groups, "faq_count": len(faqs)})


def error_codes(request):
    return render(request, "support/error_codes.html", {"codes": ErrorCode.objects.all()})


def contact(request):
    if request.method == "POST":
        form = ContactForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Thank you — your message has reached our team. We reply within one business day.")
            return redirect("support:contact")
    else:
        form = ContactForm()
    return render(request, "support/contact.html", {"form": form})


# --- Assistant API -----------------------------------------------------------------------

def _json_body(request):
    try:
        return json.loads(request.body or b"{}")
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None


@require_POST
def api_chat(request):
    if ratelimit.is_limited(request, "chat"):
        return ratelimit.too_many_requests(request, "messages")
    ratelimit.hit(request, "chat")

    data = _json_body(request)
    if data is None or not isinstance(data.get("message"), str):
        return JsonResponse({"error": "Bad Request", "code": 400, "answer": "Sorry, I couldn't read that message."}, status=400)

    page = str(data.get("page", ""))[:200]
    session_id = str(data.get("session_id", ""))[:64]
    result = answer_question(data["message"], user=request.user, email=str(data.get("email", "")).strip(), page=page)
    result["log_id"] = mongo.log_chat(
        session_id=session_id,
        page=page,
        question=data["message"][:1000],
        answer=result["answer"],
        source=result["source"],
        ticket=result["ticket"],
    )
    return JsonResponse(result)


@require_POST
def api_feedback(request):
    data = _json_body(request)
    if data is None or not data.get("log_id") or not isinstance(data.get("helpful"), bool):
        return JsonResponse({"error": "Bad Request", "code": 400}, status=400)
    stored = mongo.log_feedback(
        log_id=str(data["log_id"])[:64],
        session_id=str(data.get("session_id", ""))[:64],
        helpful=data["helpful"],
        comment=str(data.get("comment", ""))[:500],
    )
    return JsonResponse({"ok": True, "stored": stored})


@require_GET
def api_rates(request):
    return JsonResponse(get_rates())


# --- Monitoring ---------------------------------------------------------------------------

def health(request):
    checks = {}
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        checks["database"] = "ok"
    except Exception as exc:
        logger.error("health: database check failed: %s", exc.__class__.__name__)
        checks["database"] = "down"
    checks["mongodb"] = mongo.ping()
    checks["exchange_rates"] = get_rates()["source"]
    checks["anthropic_configured"] = bool(settings.ANTHROPIC_API_KEY)

    healthy = checks["database"] == "ok"
    degraded = checks["mongodb"] == "down" or checks["exchange_rates"] == "fallback"
    payload = {
        "status": "ok" if healthy and not degraded else ("degraded" if healthy else "down"),
        "uptime_seconds": int(time.time() - STARTED_AT),
        "checks": checks,
    }
    status_code = 200 if healthy else 503
    if request.GET.get("format") == "json":
        return JsonResponse(payload, status=status_code)
    return render(request, "support/health.html", {"health": payload}, status=status_code)


@staff_member_required
def debug_500(request):
    """Staff-only: deliberately raises so the custom 500 page can be demonstrated."""
    raise RuntimeError("Deliberate error to demonstrate the custom 500 page.")


# --- Error handlers (registered in config/urls.py) --------------------------------------------

def _error(request, template, status):
    return render(request, template, status=status)


def bad_request(request, exception=None):
    return _error(request, "400.html", 400)


def permission_denied(request, exception=None):
    return _error(request, "403.html", 403)


def page_not_found(request, exception=None):
    return _error(request, "404.html", 404)


def csrf_failure(request, reason=""):
    return render(request, "403.html", {"csrf_failure": True}, status=403)


def server_error(request):
    # Rendering the full page can itself fail (e.g. the database is down and the
    # session can't load), so fall back to plain HTML in that case.
    try:
        return render(request, "500.html", status=500)
    except Exception:
        return HttpResponseServerError(
            "<!doctype html><title>500 | Maison Heure</title><h1>500 — Something went wrong</h1>"
            "<p>Our team has been notified. Please try again shortly.</p><p><a href='/'>Back to Maison Heure</a></p>"
        )
