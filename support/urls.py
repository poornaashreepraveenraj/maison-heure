from django.urls import path

from . import views

app_name = "support"

urlpatterns = [
    path("faq/", views.faq, name="faq"),
    path("error-codes/", views.error_codes, name="error_codes"),
    path("contact/", views.contact, name="contact"),
    path("health/", views.health, name="health"),
    path("api/chat/", views.api_chat, name="api_chat"),
    path("api/feedback/", views.api_feedback, name="api_feedback"),
    path("api/rates/", views.api_rates, name="api_rates"),
    path("debug/500/", views.debug_500, name="debug_500"),
]
