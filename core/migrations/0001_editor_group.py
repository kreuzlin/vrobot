"""Create the "Redaktion" group with its permissions (see core/editor_group.py)."""

from django.db import migrations

from core.editor_group import EDITOR_GROUP_NAME, sync_editor_group


def remove_group(apps, schema_editor):
    apps.get_model("auth", "Group").objects.filter(name=EDITOR_GROUP_NAME).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
        ("contenttypes", "0002_remove_content_type_name"),
        ("contact", "0001_initial"),
        ("documents", "0002_initial_categories"),
        ("events", "0001_initial"),
        ("pages", "0002_initial_pages"),
        ("posts", "0002_alter_post_image"),
    ]

    operations = [
        migrations.RunPython(sync_editor_group, remove_group),
    ]
