"""FAQ about the Men's / Women's / Unisex edits, so the assistant can answer it."""
from django.db import migrations

QUESTION = "Do you sell men's, women's and unisex watches?"


def seed(apps, schema_editor):
    FAQ = apps.get_model("support", "FAQ")
    FAQ.objects.get_or_create(
        question=QUESTION,
        defaults={
            "answer": "Yes. Every watch is tagged Men's, Women's or Unisex — use the Men and Women links in the menu, or the "
            "'For' filter in the shop. Unisex pieces (typically 34–39 mm) appear in both the men's and women's edits.",
            "category": "Shopping",
            "keywords": "women, womens, ladies, lady, female, men, mens, male, unisex, gender, her, him, small wrist",
            "order": 16,
        },
    )


def unseed(apps, schema_editor):
    apps.get_model("support", "FAQ").objects.filter(question=QUESTION).delete()


class Migration(migrations.Migration):
    dependencies = [("support", "0002_seed_faq_errorcodes")]
    operations = [migrations.RunPython(seed, unseed)]
