from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("register/", views.register, name="register"),
    path("login/", views.RateLimitedLoginView.as_view(), name="login"),
    path("logout/", views.MaisonHeureLogoutView.as_view(), name="logout"),
    path("account/", views.dashboard, name="dashboard"),
    path("account/wishlist/", views.wishlist, name="wishlist"),
    path("account/wishlist/toggle/<int:watch_id>/", views.wishlist_toggle, name="wishlist_toggle"),
]
