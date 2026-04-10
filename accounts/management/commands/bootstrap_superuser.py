"""
Create a development superuser if none exists.

For production, use ``createsuperuser`` with a strong password instead.
"""

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Creates an admin superuser when none exists (development convenience).'

    def add_arguments(self, parser):
        parser.add_argument('--username', default='admin', help='Admin username')
        parser.add_argument('--email', default='admin@example.com', help='Admin email')
        parser.add_argument(
            '--password',
            default=None,
            help='Password (default: prompt or use env only in dev)',
        )

    def handle(self, *args, **options):
        User = get_user_model()
        if User.objects.filter(is_superuser=True).exists():
            self.stdout.write(self.style.WARNING('A superuser already exists; nothing to do.'))
            return

        username = options['username']
        email = options['email']
        password = options['password'] or 'changeme-dev-only'

        User.objects.create_superuser(
            username=username,
            email=email,
            password=password,
            role=User.Role.ADMIN,
        )
        self.stdout.write(
            self.style.SUCCESS(
                f'Created superuser "{username}". Change the password immediately in anything '
                f'other than local development.'
            )
        )
