import time
from django.core.management.base import BaseCommand
from django.db import connection
from django.db.utils import OperationalError
from django.utils.translation import ngettext


class Command(BaseCommand):
    help = 'Checks database connection'

    def add_arguments(self, parser):
        parser.add_argument(
            '--seconds',
            nargs='?',
            type=int,
            help='Number of seconds to wait before retrying',
            default=1,
        )
        parser.add_argument(
            '--retries',
            nargs='?',
            type=int,
            help='Number of retries before exiting',
            default=3,
        )

    def handle(self, *args, **options):
        wait, retries = options['seconds'], options['retries']
        current_retries = 0
        while current_retries < retries:
            current_retries += 1
            try:
                connection.ensure_connection()
                break
            except OperationalError:
                plural_time = ngettext('second', 'seconds', wait)
                self.stdout.write(
                    self.style.WARNING(
                        f'Database unavailable, retrying after {wait} {plural_time}!'
                    )
                )
                time.sleep(wait)

