"""The "Redaktion" group: what editors may do in the admin.

Editors maintain content but cannot manage users or permissions. The group
is created and kept in sync by a data migration. When a new content model is
added, extend `EDITOR_PERMISSIONS` and add a migration calling
`sync_editor_group` again.
"""

EDITOR_GROUP_NAME = "Redaktion"

# app_label → model → actions
EDITOR_PERMISSIONS = {
    "posts": {"post": ["view", "add", "change", "delete"]},
    "events": {"event": ["view", "add", "change", "delete"]},
    "documents": {
        "document": ["view", "add", "change", "delete"],
        "documentcategory": ["view", "add", "change", "delete"],
    },
    # Fixed pages: edit only.
    "pages": {"page": ["view", "change"]},
    # Contact messages: read and delete only.
    "contact": {"contactmessage": ["view", "delete"]},
}


def sync_editor_group(apps, schema_editor=None):
    """Create the group and set exactly the permissions above."""
    from django.contrib.auth.management import create_permissions

    # Permissions are normally created after all migrations ran; make sure
    # they exist now.
    for app_config in apps.get_app_configs():
        app_config.models_module = True
        create_permissions(app_config, apps=apps, verbosity=0)
        app_config.models_module = None

    Group = apps.get_model("auth", "Group")
    Permission = apps.get_model("auth", "Permission")

    group, _ = Group.objects.get_or_create(name=EDITOR_GROUP_NAME)
    permissions = []
    for app_label, models in EDITOR_PERMISSIONS.items():
        for model, actions in models.items():
            for action in actions:
                # filter() instead of get(): when an older migration runs on a
                # fresh database, models added later do not exist yet. A later
                # migration syncs again and adds them.
                permissions.extend(
                    Permission.objects.filter(
                        content_type__app_label=app_label,
                        codename=f"{action}_{model}",
                    )
                )
    group.permissions.set(permissions)
