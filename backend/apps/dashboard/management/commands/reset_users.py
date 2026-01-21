"""
Django management command to delete all users and create a super admin user
Run with: python manage.py reset_users

WARNING: This will delete ALL users from the database!
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from apps.dashboard.models import UserProfile


class Command(BaseCommand):
    help = 'Deletes all users and creates a fresh super admin user'

    def add_arguments(self, parser):
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Confirm deletion of all users',
        )

    def handle(self, *args, **kwargs):
        if not kwargs['confirm']:
            self.stdout.write(
                self.style.ERROR('\n⚠️  WARNING: This will delete ALL users from the database!\n')
            )
            self.stdout.write(
                self.style.WARNING('To proceed, run: python manage.py reset_users --confirm\n')
            )
            return

        # Delete all users
        user_count = User.objects.count()
        self.stdout.write(self.style.WARNING(f'\nDeleting {user_count} user(s)...'))
        
        User.objects.all().delete()
        
        self.stdout.write(self.style.SUCCESS('✓ All users deleted successfully\n'))

        # Create super admin user
        username = 'insurance_master'
        password = 'Adhoc26'
        email = 'admin@insurance.com'
        
        self.stdout.write(self.style.SUCCESS('Creating super admin user...'))
        
        # Create new user
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name='Insurance',
            last_name='Master',
            is_staff=True,
            is_superuser=True
        )
        
        # Update profile (created automatically via signal)
        # Note: employee_id will be auto-generated, department field removed
        user.profile.role = 'SUPER_ADMIN'
        user.profile.is_active = True
        user.profile.save()
        
        self.stdout.write(
            self.style.SUCCESS(f'✓ Successfully created super admin: "{username}"\n')
        )
        
        self.stdout.write(self.style.SUCCESS('╔════════════════════════════════════╗'))
        self.stdout.write(self.style.SUCCESS('║     Super Admin Details            ║'))
        self.stdout.write(self.style.SUCCESS('╠════════════════════════════════════╣'))
        self.stdout.write(f'║ Username:    {username:<21}║')
        self.stdout.write(f'║ Password:    {password:<21}║')
        self.stdout.write(f'║ Email:       {email:<21}║')
        self.stdout.write(f'║ Role:        {user.profile.get_role_display():<21}║')
        self.stdout.write(f'║ Employee ID: {user.profile.employee_id:<21}║')
        self.stdout.write(self.style.SUCCESS('╚════════════════════════════════════╝\n'))