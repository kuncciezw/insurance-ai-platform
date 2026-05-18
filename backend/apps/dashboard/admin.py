from __future__ import annotations

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

from .models import CompanyProfile, RolePermission, UserProfile


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    extra = 0
    # FIX: Explicitly tell Django to use the 'user' field as the anchor
    fk_name = 'user'  
    fieldsets = (
        ('Role & Status', {
            'fields': ('role', 'is_active', 'employee_id', 'phone_number'),
        }),
        ('Risk & Licenses', {
            'fields': ('has_driving_license', 'has_defensive_license', 'is_medical_license_valid'),
        }),
    )
    readonly_fields = ('employee_id',)

# ... [Keep the rest of your UserAdmin, RolePermissionAdmin, CompanyProfileAdmin, and UserProfileAdmin classes as they are] ...

class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'get_role')
    list_select_related = ('profile',)

    @admin.display(description='Role')
    def get_role(self, obj: User) -> str:
        profile: UserProfile | None = getattr(obj, 'profile', None)
        if profile:
            return dict(UserProfile.ROLE_CHOICES).get(profile.role, profile.role)
        return '-'

@admin.register(RolePermission)
class RolePermissionAdmin(admin.ModelAdmin):
    list_display = ('role', 'permission', 'enabled', 'updated_by', 'updated_at')
    list_filter = ('role', 'enabled')
    search_fields = ('role', 'permission')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(CompanyProfile)
class CompanyProfileAdmin(admin.ModelAdmin):
    fieldsets = (
        ('Company Information', {
            'fields': ('company_name', 'company_tagline', 'email', 'phone', 'website'),
        }),
        ('Address', {
            'fields': (
                'address_line1', 'address_line2', 'city',
                'state', 'postal_code', 'country',
            ),
        }),
        ('Business Details', {
            'fields': ('tax_id', 'license_number'),
        }),
        ('Branding', {
            'fields': ('primary_color', 'secondary_color'),
        }),
    )
    readonly_fields = ('updated_at',)

    def has_add_permission(self, request: admin.ModelAdmin) -> bool:  # type: ignore[override]
        return not CompanyProfile.objects.exists()

    def has_delete_permission(self, request: admin.ModelAdmin, obj: CompanyProfile | None = None) -> bool:  # type: ignore[override]
        return False

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'is_active', 'employee_id', 'has_driving_license', 'has_defensive_license', 'is_medical_license_valid')
    list_filter = ('role', 'is_active', 'has_driving_license', 'has_defensive_license', 'is_medical_license_valid')
    search_fields = ('user__username', 'user__email', 'employee_id')
    readonly_fields = ('employee_id', 'created_at', 'updated_at', 'last_login_ip')
    fieldsets = (
        ('User', {
            'fields': ('user', 'role', 'is_active', 'employee_id', 'phone_number'),
        }),
        ('Risk & Licenses', {
            'fields': ('has_driving_license', 'has_defensive_license', 'is_medical_license_valid'),
        }),
        ('Metadata', {
            'fields': ('last_login_ip', 'created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

admin.site.unregister(User)
admin.site.register(User, UserAdmin)