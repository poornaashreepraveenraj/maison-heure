"""Rebrand: Second Hour -> Maison Heure in FAQ and error-code text already in the database.

Fresh databases get the new wording straight from 0002; this updates databases
that were seeded before the rename.
"""
from django.db import migrations

REPLACEMENTS = [("Second Hour", "Maison Heure"), ("SH-2026-", "MH-2026-"), ("SH-T-", "MH-T-")]


def _rebrand(text):
    for old, new in REPLACEMENTS:
        text = text.replace(old, new)
    return text


def rename(apps, schema_editor):
    for model_name, fields in (("FAQ", ["question", "answer"]), ("ErrorCode", ["title", "explanation", "fix"])):
        model = apps.get_model("support", model_name)
        for row in model.objects.all():
            changed = [f for f in fields if _rebrand(getattr(row, f)) != getattr(row, f)]
            for field in changed:
                setattr(row, field, _rebrand(getattr(row, field)))
            if changed:
                row.save(update_fields=changed)


class Migration(migrations.Migration):
    dependencies = [("support", "0003_faq_mens_womens")]
    operations = [migrations.RunPython(rename, migrations.RunPython.noop)]
