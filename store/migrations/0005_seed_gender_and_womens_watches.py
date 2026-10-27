"""Set Men's / Women's / Unisex on every seeded watch and add the women's and
unisex pieces to databases that were seeded before they existed.
"""
from decimal import Decimal

from django.db import migrations

from store.catalogue_data import IMAGE_VIEWS, WATCHES


def seed(apps, schema_editor):
    Brand = apps.get_model("store", "Brand")
    Watch = apps.get_model("store", "Watch")
    WatchImage = apps.get_model("store", "WatchImage")
    brands = {b.slug: b for b in Brand.objects.all()}

    for data in WATCHES:
        existing = Watch.objects.filter(slug=data["slug"]).first()
        if existing:
            existing.gender = data["gender"]
            existing.save(update_fields=["gender"])
            continue
        fields = {k: v for k, v in data.items() if k not in {"brand", "look", "slug"}}
        fields["brand"] = brands[data["brand"]]
        fields["case_size_mm"] = Decimal(fields["case_size_mm"])
        fields["price_inr"] = Decimal(fields["price_inr"])
        if fields["original_retail_inr"]:
            fields["original_retail_inr"] = Decimal(fields["original_retail_inr"])
        watch = Watch.objects.create(slug=data["slug"], **fields)
        WatchImage.objects.bulk_create(
            [
                WatchImage(
                    watch=watch,
                    static_path=f"img/watches/{data['slug']}-{index}.svg",
                    alt=f"{fields['brand'].name} {data['model']} ({data['reference_number']}), {label}",
                    order=index,
                )
                for index, (_, label) in enumerate(IMAGE_VIEWS, start=1)
            ]
        )


class Migration(migrations.Migration):
    dependencies = [("store", "0004_watch_gender")]
    operations = [migrations.RunPython(seed, migrations.RunPython.noop)]
