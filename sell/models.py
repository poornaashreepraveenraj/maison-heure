from django.conf import settings
from django.db import models

from store.models import Watch


class Consignment(models.Model):
    class Status(models.TextChoices):
        RECEIVED = "received", "Received"
        REVIEWING = "reviewing", "Reviewing"
        OFFER_MADE = "offer_made", "Offer made"
        ACCEPTED = "accepted", "Accepted"
        DECLINED = "declined", "Declined"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="consignments"
    )
    name = models.CharField(max_length=120)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    brand = models.CharField(max_length=80)
    model = models.CharField(max_length=120)
    year = models.PositiveSmallIntegerField()
    condition = models.CharField(max_length=12, choices=Watch.Condition.choices)
    box_and_papers = models.BooleanField(default=False)
    asking_price = models.DecimalField("Asking price (INR)", max_digits=12, decimal_places=2)
    # Links rather than uploads: Vercel's filesystem is read-only, so uploaded
    # files would need external storage (see README "Known limitations").
    photos = models.TextField(blank=True, help_text="Links to photos (Google Drive, iCloud, etc.), one per line.")
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.RECEIVED)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.brand} {self.model} from {self.name}"
