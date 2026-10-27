from datetime import timedelta

from django.conf import settings
from django.db import models
from django.templatetags.static import static
from django.urls import reverse
from django.utils import timezone

RESERVATION_MINUTES = 15


class Brand(models.Model):
    name = models.CharField(max_length=80, unique=True)
    slug = models.SlugField(max_length=80, unique=True)
    country = models.CharField(max_length=60, blank=True)
    founded = models.PositiveSmallIntegerField(null=True, blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class WatchQuerySet(models.QuerySet):
    def release_expired(self):
        """Put watches whose 15-minute checkout hold has lapsed back on sale.

        Only holds created by checkout (reserved_until set) expire; a watch an
        admin marks "reserved" by hand has no expiry and stays reserved.
        """
        return self.filter(
            status=Watch.Status.RESERVED, reserved_until__isnull=False, reserved_until__lt=timezone.now()
        ).update(status=Watch.Status.AVAILABLE, reserved_until=None, reserved_by="")

    def visible(self):
        return self.select_related("brand").prefetch_related("images")


class Watch(models.Model):
    class Movement(models.TextChoices):
        AUTOMATIC = "automatic", "Automatic"
        MANUAL = "manual", "Manual wind"
        QUARTZ = "quartz", "Quartz"

    class Condition(models.TextChoices):
        UNWORN = "unworn", "Unworn"
        EXCELLENT = "excellent", "Excellent"
        VERY_GOOD = "very_good", "Very good"
        GOOD = "good", "Good"

    class Status(models.TextChoices):
        AVAILABLE = "available", "Available"
        RESERVED = "reserved", "Reserved"
        SOLD = "sold", "Sold"

    class Style(models.TextChoices):
        DRESS = "dress", "Dress"
        SPORT = "sport", "Sport"
        VINTAGE = "vintage", "Vintage"

    class Gender(models.TextChoices):
        MEN = "men", "Men's"
        WOMEN = "women", "Women's"
        UNISEX = "unisex", "Unisex"

    brand = models.ForeignKey(Brand, on_delete=models.PROTECT, related_name="watches")
    model = models.CharField(max_length=120)
    slug = models.SlugField(max_length=140, unique=True)
    reference_number = models.CharField(max_length=40)
    year = models.PositiveSmallIntegerField()
    case_size_mm = models.DecimalField(max_digits=4, decimal_places=1)
    case_material = models.CharField(max_length=60)
    movement = models.CharField(max_length=12, choices=Movement.choices, default=Movement.AUTOMATIC)
    condition = models.CharField(max_length=12, choices=Condition.choices, default=Condition.EXCELLENT)
    style = models.CharField(max_length=10, choices=Style.choices, default=Style.SPORT)
    gender = models.CharField(max_length=10, choices=Gender.choices, default=Gender.UNISEX, db_index=True)
    box_and_papers = models.BooleanField(default=False)
    price_inr = models.DecimalField(max_digits=12, decimal_places=2)
    original_retail_inr = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.AVAILABLE, db_index=True)
    featured = models.BooleanField(default=False)
    # Checkout hold: who holds it (session key) and until when.
    reserved_until = models.DateTimeField(null=True, blank=True)
    reserved_by = models.CharField(max_length=64, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = WatchQuerySet.as_manager()

    class Meta:
        ordering = ["-created_at"]
        verbose_name_plural = "watches"

    def __str__(self):
        return f"{self.brand.name} {self.model} ({self.reference_number})"

    def get_absolute_url(self):
        return reverse("store:watch_detail", args=[self.slug])

    @property
    def title(self):
        return f"{self.brand.name} {self.model}"

    @property
    def is_available(self):
        """For sale right now (an expired checkout hold counts as available)."""
        if self.status == self.Status.AVAILABLE:
            return True
        return (
            self.status == self.Status.RESERVED
            and self.reserved_until is not None
            and self.reserved_until <= timezone.now()
        )

    def can_be_bought_by(self, holder_key):
        """True when the watch is for sale, or currently held by this shopper."""
        if self.is_available:
            return True
        return self.status == self.Status.RESERVED and bool(holder_key) and self.reserved_by == holder_key

    def reserve_for(self, holder_key):
        self.status = self.Status.RESERVED
        self.reserved_by = holder_key
        self.reserved_until = timezone.now() + timedelta(minutes=RESERVATION_MINUTES)
        self.save(update_fields=["status", "reserved_by", "reserved_until", "updated_at"])

    @property
    def discount_percent(self):
        if self.original_retail_inr and self.original_retail_inr > self.price_inr:
            return round((1 - self.price_inr / self.original_retail_inr) * 100)
        return None

    @property
    def gallery(self):
        # Sorting in Python keeps the prefetch cache, so cards don't run extra queries.
        return sorted(self.images.all(), key=lambda img: img.order)

    @property
    def primary_image(self):
        images = self.gallery
        return images[0] if images else None

    @property
    def secondary_image(self):
        images = self.gallery
        return images[1] if len(images) > 1 else None


class WatchImage(models.Model):
    """A product photo: an uploaded file, a hosted photo URL, or a path inside /static.

    Vercel's filesystem is read-only, so in production real photos are added as
    URLs (e.g. Cloudinary / your own CDN) and the seed data uses static SVGs.
    Priority when several are set: uploaded file, then URL, then static path.
    """

    watch = models.ForeignKey(Watch, on_delete=models.CASCADE, related_name="images")
    image = models.FileField(upload_to="watches/", blank=True)
    external_url = models.URLField("Photo URL", max_length=500, blank=True, help_text="HTTPS link to a photo you have the rights to use.")
    static_path = models.CharField(max_length=200, blank=True, help_text="Path under /static, e.g. img/watches/x-1.svg")
    alt = models.CharField(max_length=160)
    credit = models.CharField(max_length=120, blank=True, help_text="Photographer, e.g. 'Hans Gaber on Unsplash'.")
    credit_url = models.URLField(max_length=300, blank=True)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return self.alt

    @property
    def is_photo(self):
        """Real photos fill their frame; the placeholder illustrations sit centred."""
        return bool(self.image or self.external_url)

    @property
    def url(self):
        if self.image:
            return self.image.url
        if self.external_url:
            return self.external_url
        if self.static_path:
            return static(self.static_path)
        return static("img/watch-placeholder.svg")


class Wishlist(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="wishlist")
    watch = models.ForeignKey(Watch, on_delete=models.CASCADE, related_name="wishlisted_by")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [models.UniqueConstraint(fields=["user", "watch"], name="unique_wishlist_item")]

    def __str__(self):
        return f"{self.user} - {self.watch}"
