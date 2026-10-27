"""Session-based shopping bag.

Every watch is one of a kind, so the bag is just an ordered list of watch IDs
stored in the session (quantity is always 1).
"""
from store.models import Watch

SESSION_KEY = "bag"
PROMO_KEY = "bag_promo"


class WatchUnavailable(Exception):
    """Raised when a sold/reserved watch is added or checked out (site error 470)."""

    def __init__(self, watches):
        self.watches = list(watches)
        super().__init__(", ".join(str(w) for w in self.watches))


def holder_key(request):
    """Identifies who holds a checkout reservation.

    Logged-in shoppers are keyed by user id, because Django rotates the
    session key on login and a session-keyed hold would be lost.
    """
    if request.user.is_authenticated:
        return f"user:{request.user.pk}"
    if not request.session.session_key:
        request.session.save()
    return f"session:{request.session.session_key}"


class Bag:
    def __init__(self, request):
        self.session = request.session
        self.ids = [int(i) for i in self.session.get(SESSION_KEY, [])]

    def __len__(self):
        return len(self.ids)

    def __contains__(self, watch_id):
        return watch_id in self.ids

    def _save(self):
        self.session[SESSION_KEY] = self.ids
        self.session.modified = True

    def add(self, watch):
        if watch.pk not in self.ids:
            self.ids.append(watch.pk)
            self._save()

    def remove(self, watch_id):
        if watch_id in self.ids:
            self.ids.remove(watch_id)
            self._save()

    def clear(self):
        self.ids = []
        self.session.pop(PROMO_KEY, None)
        self._save()

    def watches(self):
        """Watches in the order they were added (missing/deleted ids are skipped)."""
        by_id = {w.pk: w for w in Watch.objects.visible().filter(pk__in=self.ids)}
        return [by_id[i] for i in self.ids if i in by_id]

    @property
    def promo_code(self):
        return self.session.get(PROMO_KEY, "")

    @promo_code.setter
    def promo_code(self, code):
        if code:
            self.session[PROMO_KEY] = code
        else:
            self.session.pop(PROMO_KEY, None)
        self.session.modified = True
