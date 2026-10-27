from django.contrib import admin

from .models import Brand, Watch, WatchImage, Wishlist


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ("name", "country", "founded")
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}


class WatchImageInline(admin.TabularInline):
    model = WatchImage
    extra = 1
    fields = ("order", "image", "external_url", "static_path", "alt", "credit", "credit_url")


@admin.register(Watch)
class WatchAdmin(admin.ModelAdmin):
    list_display = ("__str__", "gender", "year", "condition", "price_inr", "status", "featured", "box_and_papers")
    list_editable = ("status", "featured")
    list_filter = ("status", "gender", "brand", "condition", "movement", "style", "box_and_papers", "featured")
    search_fields = ("model", "reference_number", "brand__name", "slug")
    prepopulated_fields = {"slug": ("model", "reference_number")}
    readonly_fields = ("reserved_until", "reserved_by", "created_at", "updated_at")
    inlines = [WatchImageInline]
    actions = ["mark_available", "mark_sold"]

    @admin.action(description="Mark selected watches as available")
    def mark_available(self, request, queryset):
        updated = queryset.update(status=Watch.Status.AVAILABLE, reserved_until=None, reserved_by="")
        self.message_user(request, f"{updated} watch(es) marked available.")

    @admin.action(description="Mark selected watches as sold")
    def mark_sold(self, request, queryset):
        updated = queryset.update(status=Watch.Status.SOLD, reserved_until=None, reserved_by="")
        self.message_user(request, f"{updated} watch(es) marked sold.")


@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ("user", "watch", "created_at")
    search_fields = ("user__username", "watch__model")
