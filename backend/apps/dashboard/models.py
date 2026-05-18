from __future__ import annotations

from typing import Any
import uuid

from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver


class RolePermission(models.Model):
    ROLE_CHOICES = [
        ('SUPER_ADMIN', 'Super Admin'),
        ('ADMIN', 'Admin'),
        ('CLAIMS_ADJUSTER', 'Claims Adjuster'),
        ('UNDERWRITER', 'Underwriter'),
        ('FRAUD_INVESTIGATOR', 'Fraud Investigator'),
        ('VIEWER', 'Viewer'),
    ]

    PERMISSION_CHOICES = [
        ('can_create_super_admin', 'Can Create Super Admin'),
        ('can_create_admin', 'Can Create Admin'),
        ('can_create_users', 'Can Create Users'),
        ('can_manage_users', 'Can Manage Users'),
        ('can_delete_users', 'Can Delete Users'),
        ('can_view_policyholders', 'Can View Policyholders'),
        ('can_view_vehicles', 'Can View Vehicles'),
        ('can_view_policies', 'Can View Policies'),
        ('can_view_claims', 'Can View Claims'),
        ('can_view_fraud_detection', 'Can View Fraud Detection'),
        ('can_create_policyholders', 'Can Create Policyholders'),
        ('can_edit_policyholders', 'Can Edit Policyholders'),
        ('can_delete_policyholders', 'Can Delete Policyholders'),
        ('can_create_policies', 'Can Create Policies'),
        ('can_edit_policies', 'Can Edit Policies'),
        ('can_delete_policies', 'Can Delete Policies'),
        ('can_process_claims', 'Can Process Claims'),
        ('can_approve_claims', 'Can Approve Claims'),
        ('can_delete_claims', 'Can Delete Claims'),
        ('can_use_fraud_detection', 'Can Use Fraud Detection'),
        ('can_flag_fraud', 'Can Flag Fraud'),
        ('can_calculate_premium', 'Can Calculate Premium'),
        ('can_estimate_claims', 'Can Estimate Claims'),
        ('can_export_reports', 'Can Export Reports'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    role = models.CharField(max_length=50, choices=ROLE_CHOICES)
    permission = models.CharField(max_length=100, choices=PERMISSION_CHOICES)
    enabled = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='permission_updates',
    )

    class Meta:
        unique_together = ('role', 'permission')
        indexes = [models.Index(fields=['role', 'permission'])]
        verbose_name = 'Role Permission'
        verbose_name_plural = 'Role Permissions'

    def __str__(self) -> str:
        role_label = dict(self.ROLE_CHOICES).get(self.role, self.role)
        perm_label = dict(self.PERMISSION_CHOICES).get(self.permission, self.permission)
        return f"{role_label} - {perm_label}: {self.enabled}"

    @classmethod
    def get_permission(cls, role: str, permission: str) -> bool | None:
        try:
            obj = cls.objects.get(role=role, permission=permission)
            return obj.enabled
        except cls.DoesNotExist:
            return None

    @classmethod
    def set_permission(
        cls,
        role: str,
        permission: str,
        enabled: bool,
        updated_by: User | None = None,
    ) -> RolePermission:
        obj, _ = cls.objects.update_or_create(
            role=role,
            permission=permission,
            defaults={'enabled': enabled, 'updated_by': updated_by},
        )
        return obj

    @classmethod
    def initialize_defaults(cls) -> int:
        defaults = cls._get_default_permissions()
        created_count = 0
        for role, permissions in defaults.items():
            for perm, enabled in permissions.items():
                _, created = cls.objects.get_or_create(
                    role=role,
                    permission=perm,
                    defaults={'enabled': enabled},
                )
                if created:
                    created_count += 1
        return created_count

    @classmethod
    def _get_default_permissions(cls) -> dict[str, dict[str, bool]]:
        return {
            'SUPER_ADMIN': {
                'can_create_super_admin': True,
                'can_create_admin': True,
                'can_create_users': True,
                'can_manage_users': True,
                'can_delete_users': True,
                'can_view_policyholders': True,
                'can_view_vehicles': True,
                'can_view_policies': True,
                'can_view_claims': True,
                'can_view_fraud_detection': True,
                'can_create_policyholders': True,
                'can_edit_policyholders': True,
                'can_delete_policyholders': True,
                'can_create_policies': True,
                'can_edit_policies': True,
                'can_delete_policies': True,
                'can_process_claims': True,
                'can_approve_claims': True,
                'can_delete_claims': True,
                'can_use_fraud_detection': True,
                'can_flag_fraud': True,
                'can_calculate_premium': True,
                'can_estimate_claims': True,
                'can_export_reports': True,
            },
            'ADMIN': {
                'can_create_super_admin': False,
                'can_create_admin': True,
                'can_create_users': True,
                'can_manage_users': True,
                'can_delete_users': True,
                'can_view_policyholders': True,
                'can_view_vehicles': True,
                'can_view_policies': True,
                'can_view_claims': True,
                'can_view_fraud_detection': True,
                'can_create_policyholders': True,
                'can_edit_policyholders': True,
                'can_delete_policyholders': True,
                'can_create_policies': True,
                'can_edit_policies': True,
                'can_delete_policies': True,
                'can_process_claims': True,
                'can_approve_claims': True,
                'can_delete_claims': True,
                'can_use_fraud_detection': True,
                'can_flag_fraud': True,
                'can_calculate_premium': True,
                'can_estimate_claims': True,
                'can_export_reports': True,
            },
            'CLAIMS_ADJUSTER': {
                'can_create_super_admin': False,
                'can_create_admin': False,
                'can_create_users': False,
                'can_manage_users': False,
                'can_delete_users': False,
                'can_view_policyholders': True,
                'can_view_vehicles': True,
                'can_view_policies': True,
                'can_view_claims': True,
                'can_view_fraud_detection': True,
                'can_create_policyholders': False,
                'can_edit_policyholders': False,
                'can_delete_policyholders': False,
                'can_create_policies': False,
                'can_edit_policies': False,
                'can_delete_policies': False,
                'can_process_claims': True,
                'can_approve_claims': True,
                'can_delete_claims': False,
                'can_use_fraud_detection': True,
                'can_flag_fraud': True,
                'can_calculate_premium': False,
                'can_estimate_claims': True,
                'can_export_reports': True,
            },
            'UNDERWRITER': {
                'can_create_super_admin': False,
                'can_create_admin': False,
                'can_create_users': False,
                'can_manage_users': False,
                'can_delete_users': False,
                'can_view_policyholders': True,
                'can_view_vehicles': True,
                'can_view_policies': True,
                'can_view_claims': True,
                'can_view_fraud_detection': True,
                'can_create_policyholders': True,
                'can_edit_policyholders': True,
                'can_delete_policyholders': False,
                'can_create_policies': True,
                'can_edit_policies': True,
                'can_delete_policies': False,
                'can_process_claims': False,
                'can_approve_claims': False,
                'can_delete_claims': False,
                'can_use_fraud_detection': True,
                'can_flag_fraud': False,
                'can_calculate_premium': True,
                'can_estimate_claims': True,
                'can_export_reports': True,
            },
            'FRAUD_INVESTIGATOR': {
                'can_create_super_admin': False,
                'can_create_admin': False,
                'can_create_users': False,
                'can_manage_users': False,
                'can_delete_users': False,
                'can_view_policyholders': True,
                'can_view_vehicles': True,
                'can_view_policies': True,
                'can_view_claims': True,
                'can_view_fraud_detection': True,
                'can_create_policyholders': False,
                'can_edit_policyholders': False,
                'can_delete_policyholders': False,
                'can_create_policies': False,
                'can_edit_policies': False,
                'can_delete_policies': False,
                'can_process_claims': False,
                'can_approve_claims': False,
                'can_delete_claims': False,
                'can_use_fraud_detection': True,
                'can_flag_fraud': True,
                'can_calculate_premium': False,
                'can_estimate_claims': False,
                'can_export_reports': True,
            },
            'VIEWER': {
                'can_create_super_admin': False,
                'can_create_admin': False,
                'can_create_users': False,
                'can_manage_users': False,
                'can_delete_users': False,
                'can_view_policyholders': True,
                'can_view_vehicles': True,
                'can_view_policies': True,
                'can_view_claims': True,
                'can_view_fraud_detection': False,
                'can_create_policyholders': False,
                'can_edit_policyholders': False,
                'can_delete_policyholders': False,
                'can_create_policies': False,
                'can_edit_policies': False,
                'can_delete_policies': False,
                'can_process_claims': False,
                'can_approve_claims': False,
                'can_delete_claims': False,
                'can_use_fraud_detection': False,
                'can_flag_fraud': False,
                'can_calculate_premium': False,
                'can_estimate_claims': False,
                'can_export_reports': False,
            },
        }


class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('SUPER_ADMIN', 'Super Admin'),
        ('ADMIN', 'Admin'),
        ('CLAIMS_ADJUSTER', 'Claims Adjuster'),
        ('UNDERWRITER', 'Underwriter'),
        ('FRAUD_INVESTIGATOR', 'Fraud Investigator'),
        ('VIEWER', 'Viewer'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=50, choices=ROLE_CHOICES, default='VIEWER')
    employee_id = models.CharField(max_length=20, unique=True, blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    is_active = models.BooleanField(default=True)
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)

    has_driving_license = models.BooleanField(default=False)
    has_defensive_license = models.BooleanField(default=False)
    is_medical_license_valid = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_profiles',
    )

    class Meta:
        ordering = ['-created_at']

    def __str__(self) -> str:
        role_label = dict(self.ROLE_CHOICES).get(self.role, self.role)
        return f"{self.user.username} - {role_label}"

    def save(self, *args: Any, **kwargs: Any) -> None:
        if not self.employee_id:
            self.employee_id = self._generate_employee_id()
        super().save(*args, **kwargs)

    def _generate_employee_id(self) -> str:
        import random
        while True:
            emp_id = f"EMP{random.randint(10000, 99999)}"
            if not UserProfile.objects.filter(employee_id=emp_id).exists():
                return emp_id

    def _check_permission(self, permission_name: str) -> bool:
        db_value = RolePermission.get_permission(self.role, permission_name)
        if db_value is not None:
            return db_value
        defaults = RolePermission._get_default_permissions()
        return defaults.get(self.role, {}).get(permission_name, False)

    def can_create_super_admin(self) -> bool:
        return self._check_permission('can_create_super_admin')

    def can_create_admin(self) -> bool:
        return self._check_permission('can_create_admin')

    def can_create_users(self) -> bool:
        return self._check_permission('can_create_users')

    def can_manage_users(self) -> bool:
        return self._check_permission('can_manage_users')

    def can_delete_users(self) -> bool:
        return self._check_permission('can_delete_users')

    def can_view_policyholders(self) -> bool:
        return self._check_permission('can_view_policyholders')

    def can_view_vehicles(self) -> bool:
        return self._check_permission('can_view_vehicles')

    def can_view_policies(self) -> bool:
        return self._check_permission('can_view_policies')

    def can_view_claims(self) -> bool:
        return self._check_permission('can_view_claims')

    def can_view_fraud_detection(self) -> bool:
        return self._check_permission('can_view_fraud_detection')

    def can_create_policyholders(self) -> bool:
        return self._check_permission('can_create_policyholders')

    def can_edit_policyholders(self) -> bool:
        return self._check_permission('can_edit_policyholders')

    def can_delete_policyholders(self) -> bool:
        return self._check_permission('can_delete_policyholders')

    def can_create_policies(self) -> bool:
        return self._check_permission('can_create_policies')

    def can_edit_policies(self) -> bool:
        return self._check_permission('can_edit_policies')

    def can_delete_policies(self) -> bool:
        return self._check_permission('can_delete_policies')

    def can_process_claims(self) -> bool:
        return self._check_permission('can_process_claims')

    def can_approve_claims(self) -> bool:
        return self._check_permission('can_approve_claims')

    def can_delete_claims(self) -> bool:
        return self._check_permission('can_delete_claims')

    def can_use_fraud_detection(self) -> bool:
        return self._check_permission('can_use_fraud_detection')

    def can_flag_fraud(self) -> bool:
        return self._check_permission('can_flag_fraud')

    def can_calculate_premium(self) -> bool:
        return self._check_permission('can_calculate_premium')

    def can_estimate_claims(self) -> bool:
        return self._check_permission('can_estimate_claims')

    def can_export_reports(self) -> bool:
        return self._check_permission('can_export_reports')


class CompanyProfile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company_name = models.CharField(max_length=200, default='InsureTech Solutions')
    company_tagline = models.CharField(max_length=500, blank=True, default='Protecting What Matters Most')
    email = models.EmailField(default='info@insuretech.com')
    phone = models.CharField(max_length=20, blank=True, default='+1 (555) 123-4567')
    website = models.URLField(blank=True, default='https://insuretech.com')
    address_line1 = models.CharField(max_length=255, blank=True, default='123 Insurance Plaza')
    address_line2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True, default='New York')
    state = models.CharField(max_length=100, blank=True, default='NY')
    postal_code = models.CharField(max_length=20, blank=True, default='10001')
    country = models.CharField(max_length=100, blank=True, default='United States')
    tax_id = models.CharField(max_length=50, blank=True)
    license_number = models.CharField(max_length=50, blank=True)
    primary_color = models.CharField(max_length=7, default='#FF6B4A', help_text='Hex color code')
    secondary_color = models.CharField(max_length=7, default='#2C3E50', help_text='Hex color code')
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='company_profile_updates',
    )

    class Meta:
        verbose_name = 'Company Profile'
        verbose_name_plural = 'Company Profile'

    def __str__(self) -> str:
        return self.company_name

    @property
    def full_address(self) -> str:
        parts = [
            self.address_line1,
            self.address_line2,
            f"{self.city}, {self.state} {self.postal_code}",
            self.country,
        ]
        return ', '.join(filter(None, parts))

    @classmethod
    def get_instance(cls) -> CompanyProfile:
        instance = cls.objects.first()
        if not instance:
            instance = cls.objects.create()
        return instance

    def save(self, *args: Any, **kwargs: Any) -> None:
        if not self.pk and CompanyProfile.objects.exists():
            existing = CompanyProfile.objects.first()
            if existing is not None:
                self.pk = existing.pk
        super().save(*args, **kwargs)

    def delete(self, using: Any = None, keep_parents: bool = False) -> tuple[int, dict[str, int]]:
        return (0, {})


@receiver(post_save, sender=User)
def create_user_profile(sender: type[User], instance: User, created: bool, **kwargs: Any) -> None:
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender: type[User], instance: User, **kwargs: Any) -> None:
    profile: UserProfile | None = getattr(instance, 'profile', None)
    if profile is not None:
        profile.save()