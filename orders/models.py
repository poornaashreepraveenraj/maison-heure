import uuid

from django.conf import settings
from django.core.validators import RegexValidator
from django.db import models
from django.urls import reverse

from store.models import Watch

pincode_validator = RegexValidator(r"^[1-9]\d{5}$", "Enter a valid 6-digit PIN code.")
phone_validator = RegexValidator(r"^\+?\d[\d\s-]{8,14}$", "Enter a valid phone number.")


class Address(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="addresses")
    name = models.CharField(max_length=120)
    phone = models.CharField(max_length=20, validators=[phone_validator])
    line1 = models.CharField("Address line 1", max_length=200)
    line2 = models.CharField("Address line 2", max_length=200, blank=True)
    city = models.CharField(max_length=80)
    state = models.CharField(max_length=80)
    pincode = models.CharField("PIN code", max_length=6, validators=[pincode_validator])
    is_default = models.BooleanField(default=False)

    class Meta:
        verbose_name_plural = "addresses"
        ordering = ["-is_default", "-pk"]

    def __str__(self):
        return f"{self.name}, {self.city} {self.pincode}"


class Order(models.Model):
    class PaymentStatus(models.TextChoices):
        PENDING = "pending", "Pending"
        PAID = "paid", "Paid"
        FAILED = "failed", "Failed"
        REFUNDED = "refunded", "Refunded"

    class Status(models.TextChoices):
        PLACED = "placed", "Placed"
        AUTHENTICATED = "authenticated", "Authenticated"
        PACKED = "packed", "Packed"
        SHIPPED = "shipped", "Shipped"
        OUT_FOR_DELIVERY = "out_for_delivery", "Out for delivery"
        DELIVERED = "delivered", "Delivered"
        CANCELLED = "cancelled", "Cancelled"

    class Delivery(models.TextChoices):
        STANDARD = "standard", "Insured standard (5–7 days)"
        EXPRESS = "express", "Insured express (2–3 days)"

    # The customer-facing timeline, in order (cancelled is shown separately).
    TIMELINE = [
        Status.PLACED,
        Status.AUTHENTICATED,
        Status.PACKED,
        Status.SHIPPED,
        Status.OUT_FOR_DELIVERY,
        Status.DELIVERED,
    ]

    reference = models.CharField(max_length=20, unique=True, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="orders")
    email = models.EmailField()
    # Address snapshot: copied at checkout so later address edits don't change old orders.
    ship_name = models.CharField(max_length=120)
    ship_phone = models.CharField(max_length=20)
    ship_line1 = models.CharField(max_length=200)
    ship_line2 = models.CharField(max_length=200, blank=True)
    ship_city = models.CharField(max_length=80)
    ship_state = models.CharField(max_length=80)
    ship_pincode = models.CharField(max_length=6)
    delivery_method = models.CharField(max_length=10, choices=Delivery.choices, default=Delivery.STANDARD)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)
    shipping = models.DecimalField(max_digits=10, decimal_places=2)
    tax = models.DecimalField(max_digits=10, decimal_places=2)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    promo_code = models.CharField(max_length=20, blank=True)
    total = models.DecimalField(max_digits=12, decimal_places=2)
    payment_status = models.CharField(max_length=10, choices=PaymentStatus.choices, default=PaymentStatus.PENDING)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PLACED, db_index=True)
    courier = models.CharField(max_length=80, blank=True)
    tracking_number = models.CharField("AWB tracking number", max_length=40, blank=True)
    estimated_delivery = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.reference

    def save(self, *args, **kwargs):
        # Reference is derived from the primary key, which only exists after the
        # first insert, so a temporary unique value is used for that insert.
        if not self.reference:
            self.reference = f"TMP-{uuid.uuid4().hex[:12]}"
            super().save(*args, **kwargs)
            self.reference = f"MH-{self.created_at.year}-{self.pk:06d}"
            super().save(update_fields=["reference"])
            return
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("orders:detail", args=[self.reference])

    def set_status(self, status, note=""):
        """Change status and append an event to the customer timeline."""
        self.status = status
        self.save(update_fields=["status", "updated_at"])
        return self.events.create(status=status, note=note)

    def timeline(self):
        """List of dicts for the tracking template: label, done flag, timestamp."""
        reached = {}
        for event in self.events.all():
            reached.setdefault(event.status, event.created_at)
        current_index = self.TIMELINE.index(self.status) if self.status in self.TIMELINE else -1
        steps = []
        for index, status in enumerate(self.TIMELINE):
            steps.append(
                {
                    "status": status,
                    "label": Order.Status(status).label,
                    "done": index <= current_index,
                    "current": index == current_index,
                    "at": reached.get(status),
                }
            )
        return steps

    @property
    def address_lines(self):
        parts = [self.ship_line1, self.ship_line2, f"{self.ship_city}, {self.ship_state} {self.ship_pincode}"]
        return [p for p in parts if p]


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    watch = models.ForeignKey(Watch, on_delete=models.PROTECT, related_name="order_items")
    price_at_purchase = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"{self.watch} @ {self.price_at_purchase}"


class OrderStatusEvent(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="events")
    status = models.CharField(max_length=20, choices=Order.Status.choices)
    note = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at", "pk"]

    def __str__(self):
        return f"{self.order.reference}: {self.get_status_display()}"
