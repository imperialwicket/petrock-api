"""
Django command to wait for db to be avialable.
"""
import time

from psycopg2 import OperationalError as Psycopg2OpError

from django.db import connection
from django.db.utils import OperationalError
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """Django command to wait for the db."""

    def handle(self, *args, **options):
        """Entrypoint for command."""
        self.stdout.write('Waiting for database...')
        db_conn = None
        while db_conn is None:
            try:
                connection.ensure_connection()
                db_conn = True
            except (Psycopg2OpError, OperationalError):
                self.stdout.write('Database unavailable, waiting...')
                time.sleep(1)

        self.stdout.write(self.style.SUCCESS('Database available.'))
