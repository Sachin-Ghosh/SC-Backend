# Create this file at: users/management/commands/create_superuser_if_none_exists.py

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from decouple import config

class Command(BaseCommand):
    help = 'Creates a superuser if none exists'

    def handle(self, *args, **options):
        User = get_user_model()
        if User.objects.filter(is_superuser=True).count() == 0:
            username = config('DJANGO_SUPERUSER_USERNAME', default='admin')
            email = config('DJANGO_SUPERUSER_EMAIL', default='admin@example.com')
            password = config('DJANGO_SUPERUSER_PASSWORD', default='adminpassword')
            
            self.stdout.write('Creating superuser account...')
            superuser = User.objects.create_superuser(
                username=username,
                email=email,
                password=password
            )
            self.stdout.write(self.style.SUCCESS(f'Superuser {username} created successfully!'))
        else:
            self.stdout.write('Superuser already exists.')