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
            
            # Fetch profile explicitly to satisfy Pylance
            try:
                profile = UserProfile.objects.get(user=user)
                profile.role = 'SUPER_ADMIN'
                profile.is_active = True
                profile.save()
                self.stdout.write(
                    self.style.SUCCESS(f'Updated "{username}" to SUPER_ADMIN role')
                )
            except UserProfile.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'Profile for {username} does not exist.'))

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
            # Fetch explicitly to satisfy Pylance
            profile = UserProfile.objects.get(user=user)
            profile.role = 'SUPER_ADMIN'
            profile.is_active = True
            profile.save()
            
            self.stdout.write(
                self.style.SUCCESS(f'Successfully created super admin: "{username}"')
            )
        
        # Get the profile one last time for the display output
        profile = UserProfile.objects.get(user=user)

        self.stdout.write(self.style.SUCCESS('\n=== Super Admin Details ==='))
        self.stdout.write(f'Username: {username}')
        self.stdout.write(f'Password: {password}')
        self.stdout.write(f'Email: {email}')
        self.stdout.write(f'Role: {profile.role}')
        self.stdout.write(f'Employee ID: {profile.employee_id}')
        self.stdout.write(self.style.SUCCESS('===========================\n'))