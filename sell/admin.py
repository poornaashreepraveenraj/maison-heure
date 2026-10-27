from django.contrib import admin

from .models import Consignment


@admin.register(Consignment)
class ConsignmentAdmin(admin.ModelAdmin):
    list_display = ("__str__", "email", "year", "condition", "asking_price", "status", "created_at")
    list_editable = ("status",)
    list_filter = ("status", "condition", "box_and_papers", "created_at")
    search_fields = ("name", "email", "brand", "model")
