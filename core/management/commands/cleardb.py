from django.db import connection
from django.core.management.base import BaseCommand


class Command(BaseCommand):

    help = 'Clear database (removes all tables)'

    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            cursor.execute('DROP SCHEMA public CASCADE;')
            cursor.execute('CREATE SCHEMA public;')
            cursor.execute('GRANT ALL ON SCHEMA public TO postgres;')
            cursor.execute('GRANT ALL ON SCHEMA public TO public;')
