from django.urls import path

from . import views

app_name = "cart"

urlpatterns = [
    path("bag/", views.bag_detail, name="bag"),
    path("bag/add/<int:watch_id>/", views.bag_add, name="add"),
    path("bag/remove/<int:watch_id>/", views.bag_remove, name="remove"),
    path("bag/promo/", views.apply_promo, name="promo"),
]
