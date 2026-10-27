"""MongoDB (Atlas) storage for chat logs and assistant feedback.

The site must keep working when MongoDB is missing or unreachable, so every
function here swallows connection errors, logs a warning and returns None.
After a failure we back off for a minute instead of waiting 2.5 s on every request.
"""
import logging
import time
import uuid

from django.conf import settings
from django.utils import timezone

logger = logging.getLogger("maisonheure.mongo")

_client = None
_last_failure = 0.0
RETRY_AFTER_SECONDS = 60


def is_configured():
    return bool(settings.MONGODB_URI)


def get_db():
    global _client, _last_failure
    if not is_configured():
        return None
    if time.monotonic() - _last_failure < RETRY_AFTER_SECONDS:
        return None
    try:
        if _client is None:
            from pymongo import MongoClient

            _client = MongoClient(settings.MONGODB_URI, serverSelectionTimeoutMS=2500, connectTimeoutMS=2500)
        return _client[settings.MONGODB_DB]
    except Exception as exc:
        _last_failure = time.monotonic()
        logger.warning("MongoDB unavailable: %s", exc.__class__.__name__)
        return None


def _insert(collection, document):
    global _last_failure
    db = get_db()
    if db is None:
        return False
    try:
        db[collection].insert_one(document)
        return True
    except Exception as exc:
        _last_failure = time.monotonic()
        logger.warning("MongoDB insert into %s failed: %s", collection, exc.__class__.__name__)
        return False


def log_chat(session_id, page, question, answer, source, ticket=None):
    """Store one assistant exchange. Returns the log_id used for feedback."""
    log_id = uuid.uuid4().hex
    _insert(
        "chat_logs",
        {
            "log_id": log_id,
            "session_id": session_id,
            "page": page,
            "question": question,
            "answer": answer,
            "source": source,
            "ticket": ticket,
            "created_at": timezone.now(),
        },
    )
    return log_id


def log_feedback(log_id, session_id, helpful, comment=""):
    return _insert(
        "feedback",
        {
            "log_id": log_id,
            "session_id": session_id,
            "helpful": bool(helpful),
            "comment": comment,
            "created_at": timezone.now(),
        },
    )


def ping():
    """'ok', 'down' or 'not_configured' — used by /health/."""
    global _last_failure
    if not is_configured():
        return "not_configured"
    db = get_db()
    if db is None:
        return "down"
    try:
        db.command("ping")
        return "ok"
    except Exception as exc:
        _last_failure = time.monotonic()
        logger.warning("MongoDB ping failed: %s", exc.__class__.__name__)
        return "down"
