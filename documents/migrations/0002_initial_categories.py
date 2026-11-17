"""Create the initial document categories. More can be added in the admin."""

from django.db import migrations

CATEGORIES = [
    ("Statuten", "statuten", 10),
    ("Formulare", "formulare", 20),
    ("Jahresberichte", "jahresberichte", 30),
]


def create_categories(apps, schema_editor):
    DocumentCategory = apps.get_model("documents", "DocumentCategory")
    for name, slug, order in CATEGORIES:
        DocumentCategory.objects.get_or_create(
            slug=slug, defaults={"name": name, "order": order}
        )


def remove_categories(apps, schema_editor):
    DocumentCategory = apps.get_model("documents", "DocumentCategory")
    DocumentCategory.objects.filter(
        slug__in=[slug for _, slug, _ in CATEGORIES], documents__isnull=True
    ).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("documents", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(create_categories, remove_categories),
    ]
