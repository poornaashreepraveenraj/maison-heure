import uuid

from django.db import models


class FAQ(models.Model):
    question = models.CharField(max_length=200)
    answer = models.TextField()
    category = models.CharField(max_length=40)
    keywords = models.CharField(
        max_length=300, blank=True, help_text="Comma-separated words/phrases the assistant matches on."
    )
    order = models.PositiveSmallIntegerField(default=0)
    is_published = models.BooleanField(default=True)

    class Meta:
        ordering = ["order", "pk"]
        verbose_name = "FAQ"
        verbose_name_plural = "FAQs"

    def __str__(self):
        return self.question

    @property
    def keyword_list(self):
        return [k.strip().lower() for k in self.keywords.split(",") if k.strip()]


class ErrorCode(models.Model):
    code = models.PositiveSmallIntegerField(unique=True)
    title = models.CharField(max_length=80)
    explanation = models.TextField(help_text="What it means on this site.")
    fix = models.TextField(help_text="What the visitor can do about it.")
    is_site_specific = models.BooleanField(default=False)

    class Meta:
        ordering = ["code"]

    def __str__(self):
        return f"{self.code} {self.title}"


class SupportTicket(models.Model):
    class Status(models.TextChoices):
        OPEN = "open", "Open"
        IN_PROGRESS = "in_progress", "In progress"
        CLOSED = "closed", "Closed"

    reference = models.CharField(max_length=12, unique=True, editable=False)
    question = models.TextField()
    email = models.EmailField(blank=True)
    page = models.CharField(max_length=200, blank=True)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.OPEN)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.reference

    def save(self, *args, **kwargs):
        # MH-T-00001 style reference, derived from the primary key after insert.
        if not self.reference:
            self.reference = f"T{uuid.uuid4().hex[:11]}"
            super().save(*args, **kwargs)
            self.reference = f"MH-T-{self.pk:05d}"
            super().save(update_fields=["reference"])
            return
        super().save(*args, **kwargs)


class ContactMessage(models.Model):
    name = models.CharField(max_length=120)
    email = models.EmailField()
    subject = models.CharField(max_length=160)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.subject} ({self.email})"
