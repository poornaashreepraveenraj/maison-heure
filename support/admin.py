from django.contrib import admin

from .models import FAQ, ContactMessage, ErrorCode, SupportTicket


@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ("question", "category", "order", "is_published")
    list_editable = ("order", "is_published")
    list_filter = ("category", "is_published")
    search_fields = ("question", "answer", "keywords")


@admin.register(ErrorCode)
class ErrorCodeAdmin(admin.ModelAdmin):
    list_display = ("code", "title", "is_site_specific")
    list_filter = ("is_site_specific",)
    search_fields = ("code", "title", "explanation")


@admin.register(SupportTicket)
class SupportTicketAdmin(admin.ModelAdmin):
    list_display = ("reference", "short_question", "email", "page", "status", "created_at")
    list_editable = ("status",)
    list_filter = ("status", "created_at")
    search_fields = ("reference", "question", "email")
    readonly_fields = ("reference", "created_at")
    actions = ["mark_closed"]

    @admin.display(description="Question")
    def short_question(self, obj):
        return obj.question[:80]

    @admin.action(description="Close selected tickets")
    def mark_closed(self, request, queryset):
        queryset.update(status=SupportTicket.Status.CLOSED)


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ("subject", "name", "email", "is_read", "created_at")
    list_editable = ("is_read",)
    list_filter = ("is_read", "created_at")
    search_fields = ("subject", "name", "email", "message")
