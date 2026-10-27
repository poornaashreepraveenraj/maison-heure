from django.urls import path

from . import views

app_name = "orders"

urlpatterns = [
    path("checkout/", views.checkout_shipping, name="checkout"),
    path("checkout/delivery/", views.checkout_delivery, name="checkout_delivery"),
    path("checkout/payment/", views.checkout_payment, name="checkout_payment"),
    path("orders/<str:reference>/confirmed/", views.order_confirmed, name="confirmed"),
    path("orders/<str:reference>/", views.order_detail, name="detail"),
    path("account/orders/", views.my_orders, name="my_orders"),
    path("track/", views.track_order, name="track"),
]
