"""
Django management command to create a super admin user
Run with: python manage.py create_superadmin
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from apps.dashboard.models import UserProfile


class Command(BaseCommand):
    help = 'Creates a super admin user for the insurance system'

    def handle(self, *args, **kwargs):
        username = 'insurance_master'
        password = 'Adhoc26'
        email = 'admin@insurance.com'
        
        # Check if user already exists
        if User.objects.filter(username=username).exists():
            self.stdout.write(
                self.style.WARNING(f'User "{username}" already exists!')
            )
            user = User.objects.get(username=username)
            
            # Update to ensure they have super admin role
            if hasattr(user, 'profile'):
                user.profile.role = 'SUPER_ADMIN'
                user.profile.is_active = True
                user.profile.save()
                self.stdout.write(
                    self.style.SUCCESS(f'Updated "{username}" to SUPER_ADMIN role')
                )
        else:
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
            # Note: employee_id will be auto-generated
            user.profile.role = 'SUPER_ADMIN'
            user.profile.is_active = True
            user.profile.save()
            
            self.stdout.write(
                self.style.SUCCESS(f'Successfully created super admin: "{username}"')
            )
        
        self.stdout.write(self.style.SUCCESS('\n=== Super Admin Details ==='))
        self.stdout.write(f'Username: {username}')
        self.stdout.write(f'Password: {password}')
        self.stdout.write(f'Email: {email}')
        self.stdout.write(f'Role: {user.profile.get_role_display()}')
        self.stdout.write(f'Employee ID: {user.profile.employee_id}')
        self.stdout.write(self.style.SUCCESS('===========================\n'))