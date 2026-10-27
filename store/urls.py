from django.urls import path

from . import views

app_name = "store"

urlpatterns = [
    path("", views.home, name="home"),
    path("shop/", views.shop, name="shop"),
    path("watch/<slug:slug>/", views.watch_detail, name="watch_detail"),
    path("about/", views.about, name="about"),
    path("api/watches/", views.api_watches, name="api_watches"),
    path("api/watches/<slug:slug>/status/", views.api_watch_status, name="api_watch_status"),
]
