from __future__ import annotations

from typing import Any

from django.contrib.auth.models import User
from rest_framework import serializers

from .models import CompanyProfile, UserProfile


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = [
            'id',
            'role',
            'employee_id',
            'phone_number',
            'is_active',
            'has_driving_license',
            'has_defensive_license',
            'is_medical_license_valid',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'employee_id', 'created_at', 'updated_at']


class UserSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer()
    full_name = serializers.SerializerMethodField()
    is_active = serializers.BooleanField(source='profile.is_active', read_only=True)

    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'full_name',
            'is_active',
            'is_staff',
            'date_joined',
            'last_login',
            'profile',
        ]
        read_only_fields = ['id', 'date_joined', 'last_login']

    def get_full_name(self, obj: User) -> str:
        return obj.get_full_name() or obj.username


class UserListSerializer(serializers.ModelSerializer):
    role = serializers.CharField(source='profile.role', read_only=True)
    role_display = serializers.CharField(source='profile.get_role_display', read_only=True)
    employee_id = serializers.CharField(source='profile.employee_id', read_only=True)
    full_name = serializers.SerializerMethodField()
    is_active = serializers.BooleanField(source='profile.is_active', read_only=True)

    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'email',
            'full_name',
            'first_name',
            'last_name',
            'role',
            'role_display',
            'employee_id',
            'is_active',
            'date_joined',
            'last_login',
        ]

    def get_full_name(self, obj: User) -> str:
        return obj.get_full_name() or obj.username


class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)
    role = serializers.ChoiceField(choices=UserProfile.ROLE_CHOICES, write_only=True)
    phone_number = serializers.CharField(required=False, allow_blank=True, write_only=True)
    has_driving_license = serializers.BooleanField(required=False, default=False, write_only=True)
    has_defensive_license = serializers.BooleanField(required=False, default=False, write_only=True)
    is_medical_license_valid = serializers.BooleanField(required=False, default=False, write_only=True)

    class Meta:
        model = User
        fields = [
            'username',
            'email',
            'password',
            'password_confirm',
            'first_name',
            'last_name',
            'role',
            'phone_number',
            'has_driving_license',
            'has_defensive_license',
            'is_medical_license_valid',
        ]

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({'password_confirm': 'Passwords do not match'})

        request = self.context.get('request')
        if request and hasattr(request.user, 'profile'):
            creator_profile: UserProfile = request.user.profile  # type: ignore[attr-defined]
            creator_role = creator_profile.role
            target_role = attrs['role']

            if target_role == 'SUPER_ADMIN' and creator_role != 'SUPER_ADMIN':
                raise serializers.ValidationError(
                    {'role': 'Only Super Admin can create Super Admin users'}
                )
            if target_role == 'ADMIN' and creator_role not in ['SUPER_ADMIN', 'ADMIN']:
                raise serializers.ValidationError(
                    {'role': 'Only Super Admin or Admin can create Admin users'}
                )

        return attrs

    def create(self, validated_data: dict[str, Any]) -> User:
        role = validated_data.pop('role')
        phone_number = validated_data.pop('phone_number', '')
        has_driving_license = validated_data.pop('has_driving_license', False)
        has_defensive_license = validated_data.pop('has_defensive_license', False)
        is_medical_license_valid = validated_data.pop('is_medical_license_valid', False)
        validated_data.pop('password_confirm')

        user = User.objects.create_user(**validated_data)

        profile: UserProfile = user.profile  # type: ignore[attr-defined]
        profile.role = role
        profile.phone_number = phone_number
        profile.has_driving_license = has_driving_license
        profile.has_defensive_license = has_defensive_license
        profile.is_medical_license_valid = is_medical_license_valid
        profile.is_active = True

        request = self.context.get('request')
        if request:
            profile.created_by = request.user

        profile.save()
        return user

    def to_representation(self, instance: User) -> Any:
        return UserSerializer(instance, context=self.context).data


class UserUpdateSerializer(serializers.ModelSerializer):
    role = serializers.ChoiceField(choices=UserProfile.ROLE_CHOICES, required=False)
    phone_number = serializers.CharField(required=False, allow_blank=True)
    is_active = serializers.BooleanField(required=False)
    has_driving_license = serializers.BooleanField(required=False)
    has_defensive_license = serializers.BooleanField(required=False)
    is_medical_license_valid = serializers.BooleanField(required=False)

    class Meta:
        model = User
        fields = [
            'email',
            'first_name',
            'last_name',
            'is_active',
            'role',
            'phone_number',
            'has_driving_license',
            'has_defensive_license',
            'is_medical_license_valid',
        ]

    def validate_role(self, value: str) -> str:
        request = self.context.get('request')
        instance: User | None = self.instance  # type: ignore[assignment]

        if request and hasattr(request.user, 'profile') and instance:
            creator_profile: UserProfile = request.user.profile  # type: ignore[attr-defined]
            creator_role = creator_profile.role
            instance_profile: UserProfile = instance.profile  # type: ignore[attr-defined]
            current_role = instance_profile.role

            if current_role == 'SUPER_ADMIN' and creator_role != 'SUPER_ADMIN':
                raise serializers.ValidationError(
                    'Only Super Admin can modify Super Admin users'
                )
            if value == 'SUPER_ADMIN' and creator_role != 'SUPER_ADMIN':
                raise serializers.ValidationError(
                    'Only Super Admin can promote users to Super Admin'
                )
            if value == 'ADMIN' and creator_role not in ['SUPER_ADMIN', 'ADMIN']:
                raise serializers.ValidationError(
                    'Only Super Admin or Admin can promote users to Admin'
                )

        return value

    def update(self, instance: User, validated_data: dict[str, Any]) -> User:
        role = validated_data.pop('role', None)
        phone_number = validated_data.pop('phone_number', None)
        is_active = validated_data.pop('is_active', None)
        has_driving_license = validated_data.pop('has_driving_license', None)
        has_defensive_license = validated_data.pop('has_defensive_license', None)
        is_medical_license_valid = validated_data.pop('is_medical_license_valid', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        profile: UserProfile = instance.profile  # type: ignore[attr-defined]
        if role is not None:
            profile.role = role
        if phone_number is not None:
            profile.phone_number = phone_number
        if is_active is not None:
            profile.is_active = is_active
        if has_driving_license is not None:
            profile.has_driving_license = has_driving_license
        if has_defensive_license is not None:
            profile.has_defensive_license = has_defensive_license
        if is_medical_license_valid is not None:
            profile.is_medical_license_valid = is_medical_license_valid
        profile.save()

        return instance


class PasswordChangeSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)
    new_password_confirm = serializers.CharField(write_only=True)

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError(
                {'new_password_confirm': 'Passwords do not match'}
            )
        return attrs

    def validate_old_password(self, value: str) -> str:
        user: User = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('Current password is incorrect')
        return value


class CompanyProfileSerializer(serializers.ModelSerializer):
    full_address = serializers.ReadOnlyField()
    updated_by_name = serializers.SerializerMethodField()

    class Meta:
        model = CompanyProfile
        fields = [
            'id',
            'company_name',
            'company_tagline',
            'email',
            'phone',
            'website',
            'address_line1',
            'address_line2',
            'city',
            'state',
            'postal_code',
            'country',
            'full_address',
            'tax_id',
            'license_number',
            'primary_color',
            'secondary_color',
            'updated_at',
            'updated_by_name',
        ]
        read_only_fields = ['id', 'updated_at', 'full_address', 'updated_by_name']

    def get_updated_by_name(self, obj: CompanyProfile) -> str | None:
        if obj.updated_by:
            return obj.updated_by.get_full_name() or obj.updated_by.username
        return None

    def validate_primary_color(self, value: str) -> str:
        if value and not value.startswith('#'):
            raise serializers.ValidationError('Color must be in HEX format (e.g., #FF6B4A)')
        if value and len(value) != 7:
            raise serializers.ValidationError('Color must be 7 characters (e.g., #FF6B4A)')
        return value

    def validate_secondary_color(self, value: str) -> str:
        if value and not value.startswith('#'):
            raise serializers.ValidationError('Color must be in HEX format (e.g., #2C3E50)')
        if value and len(value) != 7:
            raise serializers.ValidationError('Color must be 7 characters (e.g., #2C3E50)')
        return value