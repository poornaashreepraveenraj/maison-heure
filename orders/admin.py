from django.contrib import admin

from .models import Address, Order, OrderItem, OrderStatusEvent


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("watch", "price_at_purchase")
    can_delete = False


class OrderStatusEventInline(admin.TabularInline):
    model = OrderStatusEvent
    extra = 0
    readonly_fields = ("created_at",)
    fields = ("status", "note", "created_at")


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("reference", "email", "total", "payment_status", "status", "courier", "created_at")
    list_editable = ("status",)
    list_filter = ("status", "payment_status", "delivery_method", "created_at")
    search_fields = ("reference", "email", "tracking_number", "ship_name")
    readonly_fields = ("reference", "created_at", "updated_at")
    inlines = [OrderItemInline, OrderStatusEventInline]
    actions = ["mark_shipped", "mark_out_for_delivery", "mark_delivered"]
    fieldsets = (
        (None, {"fields": ("reference", "user", "email", "status", "payment_status")}),
        ("Shipping address", {"fields": ("ship_name", "ship_phone", "ship_line1", "ship_line2", "ship_city", "ship_state", "ship_pincode")}),
        ("Delivery", {"fields": ("delivery_method", "courier", "tracking_number", "estimated_delivery")}),
        ("Money", {"fields": ("subtotal", "discount", "promo_code", "shipping", "tax", "total")}),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )

    def save_model(self, request, obj, form, change):
        """Every status change made in admin (form or list_editable) adds a timeline event."""
        super().save_model(request, obj, form, change)
        if change and "status" in form.changed_data:
            obj.events.create(status=obj.status, note=f"Updated by {request.user.username}")

    def _bulk_status(self, request, queryset, status):
        for order in queryset:
            order.set_status(status, note=f"Updated by {request.user.username}")
        self.message_user(request, f"{queryset.count()} order(s) updated.")

    @admin.action(description="Mark shipped")
    def mark_shipped(self, request, queryset):
        self._bulk_status(request, queryset, Order.Status.SHIPPED)

    @admin.action(description="Mark out for delivery")
    def mark_out_for_delivery(self, request, queryset):
        self._bulk_status(request, queryset, Order.Status.OUT_FOR_DELIVERY)

    @admin.action(description="Mark delivered")
    def mark_delivered(self, request, queryset):
        self._bulk_status(request, queryset, Order.Status.DELIVERED)


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ("name", "user", "city", "state", "pincode", "is_default")
    search_fields = ("name", "user__username", "city", "pincode")
    list_filter = ("state", "is_default")
