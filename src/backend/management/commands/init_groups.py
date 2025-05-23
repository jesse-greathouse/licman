from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission

class Command(BaseCommand):
    help = 'Create default user groups with specific permissions.'

    GROUP_PERMISSIONS = {
        "admin": [
            # LogEntry
            ("admin", "logentry", "view_logentry"),

            # Group
            ("auth", "group", "view_group"),

            # Permission
            ("auth", "permission", "view_permission"),

            # User
            ("auth", "user", "add_user"),
            ("auth", "user", "change_user"),
            ("auth", "user", "delete_user"),
            ("auth", "user", "view_user"),

            # ContentType
            ("contenttypes", "contenttype", "add_contenttype"),
            ("contenttypes", "contenttype", "change_contenttype"),
            ("contenttypes", "contenttype", "delete_contenttype"),
            ("contenttypes", "contenttype", "view_contenttype"),

            # Sessions
            ("sessions", "session", "view_session"),
            ("sessions", "session", "delete_session"),
        ],
        "support": [
            # LogEntry
            ("admin", "logentry", "view_logentry"),

            # User
            ("auth", "user", "view_user"),
            ("auth", "user", "change_user"),

            # ContentType
            ("contenttypes", "contenttype", "change_contenttype"),
            ("contenttypes", "contenttype", "view_contenttype"),

            # Sessions
            ("sessions", "session", "view_session"),
        ]
    }

    def handle(self, *args, **kwargs):
        for group_name, perms in self.GROUP_PERMISSIONS.items():
            group, created = Group.objects.get_or_create(name=group_name)
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created group: {group_name}'))
            else:
                self.stdout.write(f'Group already exists: {group_name}')

            group.permissions.clear()  # Optional: reset before assigning

            for app_label, model, codename in perms:
                try:
                    permission = Permission.objects.get(
                        content_type__app_label=app_label,
                        content_type__model=model,
                        codename=codename
                    )
                    group.permissions.add(permission)
                except Permission.DoesNotExist:
                    self.stderr.write(self.style.ERROR(
                        f"Missing permission: {app_label}.{model}.{codename}"
                    ))

            self.stdout.write(self.style.SUCCESS(
                f'Assigned {group.permissions.count()} permissions to "{group_name}"'
            ))
