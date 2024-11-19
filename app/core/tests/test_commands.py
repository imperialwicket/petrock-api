"""
Test custom Django management commands.
"""
from unittest.mock import patch

from psycopg2 import OperationalError as Psycoppg2Error

from django.core.management import call_command
from django.db.utils import OperationalError
from django.test import TestCase


@patch('django.db.connection.ensure_connection')
class CommandTests(TestCase):
    """Test commands."""

    def test_wait_for_db_ready(self, patched_ensure_connection):
        """Test waiting for database to be ready"""
        patched_ensure_connection.return_value = True

        call_command('wait_for_db')

        self.assertEqual(patched_ensure_connection.call_count, 1)

    @patch('time.sleep')
    def test_wait_for_db_delay(self, patched_sleep, patched_ensure_connection):
        """Test waiting for database when getting OperationalError."""
        patched_ensure_connection.side_effect = [Psycoppg2Error] * 2 + \
            [OperationalError] * 2 + [True]

        call_command('wait_for_db')

        self.assertEqual(patched_ensure_connection.call_count, 5)
        # patched_ensure_connection.assert_called_with(databases=['default'])
