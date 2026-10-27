from django.urls import path

from . import views

app_name = "sell"

urlpatterns = [
    path("sell/", views.sell, name="sell"),
]
