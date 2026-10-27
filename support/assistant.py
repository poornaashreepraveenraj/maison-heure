"""Maison Heure Concierge: the support assistant's answer pipeline.

Each question goes through these steps in order and the first one that
produces an answer wins:

  1. Error codes  - a 3-digit code we document (e.g. "what is 470?")
  2. Orders       - "where is my order MH-2026-000123?"
  3. Catalogue    - a reference number we stock (from "Ask about this watch")
  4. FAQ match    - keyword + word-overlap scoring against the FAQ table
  5. Claude       - only if ANTHROPIC_API_KEY is set; restricted to FAQ/error data
  6. Ticket       - nothing could answer, so a SupportTicket is created

Small talk ("hi", "thanks") is answered before step 1 so it never opens a ticket.
"""
import logging
import re

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.urls import reverse

from store.models import Watch
from store.templatetags.store_extras import format_inr

from .models import FAQ, ErrorCode, SupportTicket

logger = logging.getLogger("maisonheure.assistant")

FAQ_THRESHOLD = 2  # one strong keyword hit is enough ("is it fake?")
MAX_QUESTION_LENGTH = 1000

# MH- is the current prefix; SH- (from before the rebrand) is still recognised.
ORDER_REF_RE = re.compile(r"\b(?:MH|SH)-\d{4}-\d{6}\b", re.IGNORECASE)
ERROR_CODE_RE = re.compile(r"(?<![\d.,₹])\b([1-5]\d{2})\b(?![\d.,])")
ORDER_INTENT_RE = re.compile(
    r"\b(where('?s| is)? my (order|watch|parcel)|track(ing)? (my |an )?order|order status|status of my order|my order)\b",
    re.IGNORECASE,
)
SMALLTALK_RE = re.compile(
    r"^\s*(hi|hello|hey|hiya|namaste|good (morning|afternoon|evening)|thanks|thank you|thx|ok(ay)?|cool)\b[\s!.?]*$",
    re.IGNORECASE,
)

STOPWORDS = {
    "a", "an", "the", "is", "are", "am", "was", "be", "it", "its", "i", "me", "my", "we", "you", "your", "our",
    "do", "does", "did", "can", "could", "would", "should", "will", "to", "of", "in", "on", "for", "with", "and",
    "or", "what", "how", "when", "which", "who", "why", "this", "that", "there", "any", "if", "at", "by", "so",
    "have", "has", "get", "about", "from", "please", "tell", "know", "want", "need", "much", "long",
}


def _stem(word):
    """Crude suffix stripping so 'watches'/'watch' and 'shipping'/'ship' match."""
    for suffix in ("ing", "es", "ed", "s"):
        if len(word) > len(suffix) + 3 and word.endswith(suffix):
            return word[: -len(suffix)]
    return word


def tokenize(text):
    return {_stem(w) for w in re.findall(r"[a-z0-9]+", text.lower()) if w not in STOPWORDS and len(w) > 1}


def _result(answer, source, ticket=None):
    return {"answer": answer, "source": source, "ticket": ticket}


# --- Step 1: error codes -------------------------------------------------------

def answer_error_code(message):
    for match in ERROR_CODE_RE.finditer(message):
        code = ErrorCode.objects.filter(code=int(match.group(1))).first()
        if code:
            label = "Maison Heure-specific code" if code.is_site_specific else "standard HTTP code"
            return _result(
                f"**Error {code.code} — {code.title}** ({label}).\n{code.explanation}\n**How to fix it:** {code.fix}",
                "error_code",
            )
    return None


# --- Step 2: orders --------------------------------------------------------------

def _order_summary(order):
    eta = f" Estimated delivery: **{order.estimated_delivery:%d %b %Y}**." if order.estimated_delivery else ""
    courier = f" Courier: {order.courier}, AWB {order.tracking_number}." if order.tracking_number else ""
    return (
        f"Order **{order.reference}** is currently **{order.get_status_display()}**.{courier}{eta}\n"
        f"Full timeline: {order.get_absolute_url()}"
    )


def answer_order(message, user):
    ref_match = ORDER_REF_RE.search(message)
    if not ref_match and not ORDER_INTENT_RE.search(message):
        return None
    track_url = reverse("orders:track")

    if user is not None and user.is_authenticated:
        orders = user.orders.all()
        if ref_match:
            order = orders.filter(reference__iexact=ref_match.group(0)).first()
            if order:
                return _result(_order_summary(order), "order")
            return _result(
                f"I can't find **{ref_match.group(0).upper()}** on your account. If it was placed with a different "
                f"email, look it up at {track_url} using the order reference and that email.",
                "order",
            )
        latest = orders.first()
        if latest:
            return _result(_order_summary(latest) + f"\nAll your orders: {reverse('orders:my_orders')}", "order")
        return _result(f"You don't have any orders on this account yet. Guests can look up an order at {track_url}.", "order")

    # Never reveal order details to an anonymous chat user — send them to the
    # lookup form, which checks the reference *and* the email.
    return _result(
        f"For your privacy I can only show order details after you sign in, or you can track it at {track_url} "
        "with your order reference (e.g. MH-2026-000123) and the email used at checkout.",
        "order",
    )


# --- Step 3: catalogue -------------------------------------------------------------

def answer_catalogue(message):
    lowered = message.lower()
    for watch in Watch.objects.select_related("brand").only(
        "slug", "model", "reference_number", "status", "price_inr", "condition", "year", "box_and_papers", "brand__name"
    ):
        if watch.reference_number.lower() in lowered:
            if watch.is_available:
                status = f"is **available** at {format_inr(watch.price_inr)}"
            elif watch.status == Watch.Status.RESERVED:
                status = "is **reserved** for another client right now — it may come back if their hold lapses"
            else:
                status = "has been **sold**. Use 'Notify me' on its page and we'll tell you when a similar piece arrives"
            papers = "with box & papers" if watch.box_and_papers else "without box & papers"
            return _result(
                f"The **{watch.title}** (ref. {watch.reference_number}, {watch.year}, "
                f"{watch.get_condition_display().lower()} condition, {papers}) {status}. "
                "Every watch passes our 4-step authentication and carries a 12-month warranty.",
                "catalogue",
            )
    return None


# --- Step 4: FAQ ---------------------------------------------------------------------

def _keyword_hit(keyword, tokens):
    """Exact stem match, or a shared prefix for longer words ('international' ~ 'internationally')."""
    stem = _stem(keyword)
    if stem in tokens:
        return True
    return len(stem) >= 5 and any(t.startswith(stem) for t in tokens)


def match_faq(message):
    """Score each FAQ and return the best one above FAQ_THRESHOLD.

    +3 per keyword phrase found in the text, +2 per single keyword matched,
    +1 per word shared with the FAQ question, +2 if every question word is present.
    """
    text = message.lower()
    tokens = tokenize(message)
    best, best_score = None, 0
    for faq in FAQ.objects.filter(is_published=True):
        score = 0
        for keyword in faq.keyword_list:
            if " " in keyword:
                score += 3 if keyword in text else 0
            elif _keyword_hit(keyword, tokens):
                score += 2
        question_tokens = tokenize(faq.question)
        score += len(tokens & question_tokens)
        if question_tokens and question_tokens <= tokens:
            score += 2
        if score > best_score:
            best, best_score = faq, score
    return best if best_score >= FAQ_THRESHOLD else None


# --- Step 5: Claude fallback ---------------------------------------------------------------

def build_system_prompt():
    faqs = "\n".join(f"Q: {f.question}\nA: {f.answer}" for f in FAQ.objects.filter(is_published=True))
    codes = "\n".join(f"{c.code} {c.title}: {c.explanation} Fix: {c.fix}" for c in ErrorCode.objects.all())
    return (
        "You are the Maison Heure Concierge, the support assistant for Maison Heure, an Indian online store for "
        "authenticated pre-owned luxury watches.\n\n"
        "Answer only from the reference data below (the store's FAQs and error codes). Do not add facts about "
        "watches, brands, prices or policies that are not in it. Keep answers under 80 words, warm and plain. "
        "Never give investment advice or promise what a watch will be worth.\n\n"
        "If the reference data does not answer the question, reply with exactly NO_ANSWER and nothing else.\n\n"
        f"<faqs>\n{faqs}\n</faqs>\n\n<error_codes>\n{codes}\n</error_codes>"
    )


def ask_claude(message):
    """Returns Claude's answer text, or None if not configured / no answer / any failure."""
    if not settings.ANTHROPIC_API_KEY:
        return None
    try:
        import anthropic
    except ImportError:
        logger.warning("anthropic package not installed")
        return None

    client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY, timeout=15.0, max_retries=0)
    try:
        response = client.beta.messages.create(
            model=settings.ANTHROPIC_MODEL,
            max_tokens=1024,
            system=build_system_prompt(),
            messages=[{"role": "user", "content": message}],
            output_config={"effort": "low"},
            # If a safety classifier declines, the API retries on a fallback model in the same call.
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
        )
    except anthropic.APITimeoutError:
        logger.warning("Claude timed out after 15s")
        return None
    except anthropic.RateLimitError:
        logger.warning("Claude rate limited")
        return None
    except anthropic.APIStatusError as exc:
        logger.warning("Claude API error status=%s", exc.status_code)
        return None
    except anthropic.APIConnectionError:
        logger.warning("Claude connection error")
        return None

    if response.stop_reason == "refusal":
        return None
    text = "".join(block.text for block in response.content if block.type == "text").strip()
    if not text or "NO_ANSWER" in text:
        return None
    return text


# --- Step 6: ticket ---------------------------------------------------------------------

def create_ticket(message, email="", page=""):
    try:
        validate_email(email)
    except ValidationError:
        email = ""
    ticket = SupportTicket.objects.create(question=message, email=email, page=page[:200])
    follow_up = (
        f"We'll reply to **{email}**."
        if email
        else "Add your email in the box below and ask again, or quote this reference on our contact page."
    )
    return _result(
        f"I couldn't find a confident answer, so I've opened support ticket **{ticket.reference}** for our team. "
        f"{follow_up}",
        "ticket",
        ticket.reference,
    )


# --- Pipeline -------------------------------------------------------------------------------

def answer_question(message, user=None, email="", page=""):
    message = (message or "").strip()[:MAX_QUESTION_LENGTH]
    if not message:
        return _result("Ask me anything about our watches, orders, delivery or error codes.", "smalltalk")

    if SMALLTALK_RE.match(message):
        return _result(
            "Hello! I'm the Maison Heure Concierge. I can explain authentication, delivery, returns and error "
            "codes, or check an order. What would you like to know?",
            "smalltalk",
        )

    for step in (
        lambda: answer_error_code(message),
        lambda: answer_order(message, user),
        lambda: answer_catalogue(message),
    ):
        result = step()
        if result:
            return result

    faq = match_faq(message)
    if faq:
        return _result(f"**{faq.question}**\n{faq.answer}", "faq")

    ai_answer = ask_claude(message)
    if ai_answer:
        return _result(ai_answer, "ai")

    return create_ticket(message, email=email, page=page)
