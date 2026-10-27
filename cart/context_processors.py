from .bag import SESSION_KEY


def bag(request):
    """Bag item count for the header badge on every page."""
    session = getattr(request, "session", None)
    return {"bag_count": len(session.get(SESSION_KEY, [])) if session is not None else 0}
