from django.contrib.auth.models import Group, Permission
from django.core.management import BaseCommand
from django.db import transaction

from core.constants import GROUPS, PERMISSIONS_MAP


class Command(BaseCommand):
    """ Init backend command. """
    help = 'Init backend.'

    def handle(self, *args, **options):
        self.create_base_roles()

    @transaction.atomic
    def create_base_roles(self):
        for group in GROUPS:
            group_instance = Group.objects.create(name=group)
            for permission in PERMISSIONS_MAP[group]:
                group_instance.permissions.add(
                    Permission.objects.get(codename=permission)
                )
            group_instance.save()
