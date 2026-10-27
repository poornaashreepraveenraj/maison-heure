"""Seed 6 brands and 20 watches (with 4 placeholder SVG images each).

Running `migrate` on a fresh database (SQLite locally, Postgres on Vercel)
therefore gives a fully stocked demo shop with no manual steps.
"""
from decimal import Decimal

from django.db import migrations

from store.catalogue_data import BRANDS, IMAGE_VIEWS, WATCHES


def seed(apps, schema_editor):
    Brand = apps.get_model("store", "Brand")
    Watch = apps.get_model("store", "Watch")
    WatchImage = apps.get_model("store", "WatchImage")

    brands = {}
    for data in BRANDS:
        brands[data["slug"]], _ = Brand.objects.get_or_create(slug=data["slug"], defaults=data)

    # Only fields that exist at this point in the migration history; later
    # fields (e.g. gender, added in 0004) are filled in by later migrations.
    model_fields = {f.name for f in Watch._meta.get_fields()}
    for data in WATCHES:
        fields = {k: v for k, v in data.items() if k in model_fields and k not in {"brand", "slug"}}
        fields["brand"] = brands[data["brand"]]
        fields["case_size_mm"] = Decimal(fields["case_size_mm"])
        fields["price_inr"] = Decimal(fields["price_inr"])
        if fields["original_retail_inr"]:
            fields["original_retail_inr"] = Decimal(fields["original_retail_inr"])
        watch, created = Watch.objects.get_or_create(slug=data["slug"], defaults=fields)
        if created:
            brand_name = fields["brand"].name
            WatchImage.objects.bulk_create(
                [
                    WatchImage(
                        watch=watch,
                        static_path=f"img/watches/{data['slug']}-{index}.svg",
                        alt=f"{brand_name} {data['model']} ({data['reference_number']}), {label}",
                        order=index,
                    )
                    for index, (_, label) in enumerate(IMAGE_VIEWS, start=1)
                ]
            )


def unseed(apps, schema_editor):
    Watch = apps.get_model("store", "Watch")
    Brand = apps.get_model("store", "Brand")
    Watch.objects.filter(slug__in=[w["slug"] for w in WATCHES]).delete()
    Brand.objects.filter(slug__in=[b["slug"] for b in BRANDS], watches__isnull=True).delete()


class Migration(migrations.Migration):
    dependencies = [("store", "0001_initial")]
    operations = [migrations.RunPython(seed, unseed)]
