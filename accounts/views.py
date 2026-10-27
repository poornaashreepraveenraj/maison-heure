from urllib.parse import urlencode

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.db import IntegrityError
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from cart.views import wants_json
from sell.models import Consignment
from store.models import Watch, Wishlist
from support import ratelimit

from .forms import RegisterForm


def safe_next(request, fallback):
    """Only follow ?next= / next= values that point back to this site (no open redirects)."""
    target = request.POST.get("next") or request.GET.get("next")
    if target and url_has_allowed_host_and_scheme(target, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
        return target
    return fallback


def register(request):
    if request.user.is_authenticated:
        return redirect("accounts:dashboard")
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            try:
                user = form.save()
            except IntegrityError:
                # Two submissions raced past validation (e.g. a double-click on a slow
                # connection): the first created the account, so point to sign-in instead of a 500.
                form.add_error("username", "An account with this username was just created. Please sign in instead.")
            else:
                login(request, user)
                messages.success(request, f"Welcome to Maison Heure, {user.username}.")
                return redirect(safe_next(request, reverse("accounts:dashboard")))
    else:
        form = RegisterForm()
    return render(request, "accounts/register.html", {"form": form, "next": request.GET.get("next", "")})


class RateLimitedLoginView(LoginView):
    """Django's LoginView plus a 429 after repeated failed attempts from one IP."""

    template_name = "accounts/login.html"
    redirect_authenticated_user = True

    def post(self, request, *args, **kwargs):
        if ratelimit.is_limited(request, "login"):
            return ratelimit.too_many_requests(request, "sign-in attempts")
        return super().post(request, *args, **kwargs)

    def form_invalid(self, form):
        ratelimit.hit(self.request, "login")
        return super().form_invalid(form)

    def form_valid(self, form):
        messages.success(self.request, f"Welcome back, {form.get_user().username}.")
        return super().form_valid(form)


class MaisonHeureLogoutView(LogoutView):
    """POST-only logout (Django's default since 5.0); adds a friendly message."""

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        messages.info(request, "You have been signed out.")
        return response


@login_required
def dashboard(request):
    user = request.user
    context = {
        "recent_orders": user.orders.prefetch_related("items__watch__brand")[:3],
        "order_count": user.orders.count(),
        "wishlist_count": user.wishlist.count(),
        "addresses": user.addresses.all(),
        "consignments": Consignment.objects.filter(Q(user=user) | Q(email__iexact=user.email or "-")),
    }
    return render(request, "accounts/dashboard.html", context)


@login_required
def wishlist(request):
    items = Wishlist.objects.filter(user=request.user).select_related("watch__brand").prefetch_related("watch__images")
    watches = [item.watch for item in items]
    return render(
        request,
        "accounts/wishlist.html",
        {"watches": watches, "wishlist_ids": {w.pk for w in watches}, "bag_ids": set(request.session.get("bag", []))},
    )


@require_POST
def wishlist_toggle(request, watch_id):
    if not request.user.is_authenticated:
        if wants_json(request):
            return JsonResponse({"error": "Unauthorized", "code": 401, "login_url": reverse("accounts:login")}, status=401)
        return redirect(f"{reverse('accounts:login')}?{urlencode({'next': safe_next(request, '/')})}")
    watch = get_object_or_404(Watch, pk=watch_id)
    item, created = Wishlist.objects.get_or_create(user=request.user, watch=watch)
    if not created:
        item.delete()
    if wants_json(request):
        return JsonResponse({"ok": True, "in_wishlist": created, "count": request.user.wishlist.count()})
    messages.success(request, f"{watch.title} {'saved to' if created else 'removed from'} your wishlist.")
    return redirect(safe_next(request, reverse("accounts:wishlist")))
