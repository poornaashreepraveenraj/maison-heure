"""Remove the seeded watches that only had placeholder illustrations.

The catalogue now shows only watches with real photos (17 pieces). A watch that
already appears in an order is kept so order history never breaks.
"""
from django.db import migrations

REMOVED = [
    "rolex-gmt-master-ii-126710blro",
    "cartier-tank-must-wsta0041",
    "cartier-ballon-bleu-36-w69012z4",
    "cartier-panthere-small-wspn0006",
    "omega-constellation-28-131-10-28",
    "patek-philippe-calatrava-5196r",
    "patek-philippe-aquanaut-5167a",
    "patek-philippe-twenty-4-4910-1200a",
    "audemars-piguet-royal-oak-offshore-26470st",
    "audemars-piguet-code-1159-15210bc",
]


def remove(apps, schema_editor):
    Watch = apps.get_model("store", "Watch")
    Watch.objects.filter(slug__in=REMOVED, order_items__isnull=True).delete()


class Migration(migrations.Migration):
    dependencies = [("store", "0007_unsplash_photos")]
    operations = [migrations.RunPython(remove, migrations.RunPython.noop)]
