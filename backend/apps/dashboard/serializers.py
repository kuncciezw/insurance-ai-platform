"""
Serializers for User Management with RBAC
"""

from rest_framework import serializers
from django.contrib.auth.models import User
from .models import UserProfile, CompanyProfile


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for UserProfile"""
    
    class Meta:
        model = UserProfile
        fields = [
            'id', 'role', 'employee_id', 'phone_number',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'employee_id', 'created_at', 'updated_at']


class UserSerializer(serializers.ModelSerializer):
    """Full serializer for User with profile"""
    
    profile = UserProfileSerializer()
    full_name = serializers.SerializerMethodField()
    is_active = serializers.BooleanField(source='profile.is_active', read_only=True)  # ⭐ Use profile.is_active
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'full_name', 'is_active', 'is_staff', 'date_joined',
            'last_login', 'profile'
        ]
        read_only_fields = ['id', 'date_joined', 'last_login']
    
    def get_full_name(self, obj):
        return obj.get_full_name() or obj.username


class UserListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing users"""
    
    role = serializers.CharField(source='profile.role', read_only=True)
    role_display = serializers.CharField(source='profile.get_role_display', read_only=True)
    employee_id = serializers.CharField(source='profile.employee_id', read_only=True)
    full_name = serializers.SerializerMethodField()
    is_active = serializers.BooleanField(source='profile.is_active', read_only=True)  # ⭐ Use profile.is_active
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'full_name', 'first_name',
            'last_name', 'role', 'role_display', 'employee_id',
            'is_active', 'date_joined', 'last_login'
        ]
    
    def get_full_name(self, obj):
        return obj.get_full_name() or obj.username


class UserCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new users VIA ADMIN PANEL"""
    
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)
    role = serializers.ChoiceField(choices=UserProfile.ROLE_CHOICES, write_only=True)
    phone_number = serializers.CharField(required=False, allow_blank=True, write_only=True)

    class Meta:
        model = User
        fields = [
            'username', 'email', 'password', 'password_confirm',
            'first_name', 'last_name', 'role', 'phone_number'
        ]

    def validate(self, data):
        """Validate user creation data"""
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError({
                'password_confirm': 'Passwords do not match'
            })
        
        # Validate role based on creator's permissions
        request = self.context.get('request')
        if request and hasattr(request.user, 'profile'):
            creator_role = request.user.profile.role
            target_role = data['role']
            
            # Super Admin can only be created by Super Admin
            if target_role == 'SUPER_ADMIN' and creator_role != 'SUPER_ADMIN':
                raise serializers.ValidationError({
                    'role': 'Only Super Admin can create Super Admin users'
                })
            
            # Admin can only be created by Super Admin or Admin
            if target_role == 'ADMIN' and creator_role not in ['SUPER_ADMIN', 'ADMIN']:
                raise serializers.ValidationError({
                    'role': 'Only Super Admin or Admin can create Admin users'
                })
        
        return data

    def create(self, validated_data):
        """Create user with profile - ADMIN CREATED USERS ARE IMMEDIATELY ACTIVE"""
        # Extract profile data
        role = validated_data.pop('role')
        phone_number = validated_data.pop('phone_number', '')
        validated_data.pop('password_confirm')
        
        # Create user
        user = User.objects.create_user(**validated_data)
        
        # Update profile
        profile = user.profile
        profile.role = role
        profile.phone_number = phone_number
        profile.is_active = True  # ADMIN-CREATED USERS ARE ACTIVE IMMEDIATELY
        
        # Set creator
        request = self.context.get('request')
        if request:
            profile.created_by = request.user
        
        profile.save()
        
        return user
    
    def to_representation(self, instance):
        """Use UserSerializer for the response"""
        return UserSerializer(instance, context=self.context).data

class UserUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating users"""
    
    role = serializers.ChoiceField(choices=UserProfile.ROLE_CHOICES, required=False)
    phone_number = serializers.CharField(required=False, allow_blank=True)
    is_active = serializers.BooleanField(required=False) 
    
    class Meta:
        model = User
        fields = [
            'email', 'first_name', 'last_name', 'is_active',
            'role', 'phone_number'
        ]
    
    def validate_role(self, value):
        """Validate role change"""
        request = self.context.get('request')
        instance = self.instance
        
        if request and hasattr(request.user, 'profile') and instance:
            creator_role = request.user.profile.role
            current_role = instance.profile.role
            new_role = value
            
            # Can't change Super Admin role unless you're Super Admin
            if current_role == 'SUPER_ADMIN' and creator_role != 'SUPER_ADMIN':
                raise serializers.ValidationError(
                    'Only Super Admin can modify Super Admin users'
                )
            
            # Can't promote to Super Admin unless you're Super Admin
            if new_role == 'SUPER_ADMIN' and creator_role != 'SUPER_ADMIN':
                raise serializers.ValidationError(
                    'Only Super Admin can promote users to Super Admin'
                )
            
            # Can't promote to Admin unless you're Super Admin or Admin
            if new_role == 'ADMIN' and creator_role not in ['SUPER_ADMIN', 'ADMIN']:
                raise serializers.ValidationError(
                    'Only Super Admin or Admin can promote users to Admin'
                )
        
        return value
    
    def update(self, instance, validated_data):
        """Update user and profile"""
       
        role = validated_data.pop('role', None)
        phone_number = validated_data.pop('phone_number', None)
        is_active = validated_data.pop('is_active', None)
        
        # Update Django User fields (email, first_name, last_name)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
       
        profile = instance.profile
        if role is not None:
            profile.role = role
        if phone_number is not None:
            profile.phone_number = phone_number
        if is_active is not None:
            profile.is_active = is_active
        profile.save()
        
        return instance

class PasswordChangeSerializer(serializers.Serializer):
    """Serializer for changing password"""
    
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)
    new_password_confirm = serializers.CharField(write_only=True)
    
    def validate(self, data):
        if data['new_password'] != data['new_password_confirm']:
            raise serializers.ValidationError({
                'new_password_confirm': 'Passwords do not match'
            })
        return data
    
    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('Current password is incorrect')
        return value


class CompanyProfileSerializer(serializers.ModelSerializer):
    """Serializer for Company Profile"""
    
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
    
    def get_updated_by_name(self, obj):
        if obj.updated_by:
            return obj.updated_by.get_full_name() or obj.updated_by.username
        return None
    
    def validate_primary_color(self, value):
        if value and not value.startswith('#'):
            raise serializers.ValidationError('Color must be in HEX format (e.g., #FF6B4A)')
        if value and len(value) != 7:
            raise serializers.ValidationError('Color must be 7 characters (e.g., #FF6B4A)')
        return value
    
    def validate_secondary_color(self, value):
        if value and not value.startswith('#'):
            raise serializers.ValidationError('Color must be in HEX format (e.g., #2C3E50)')
        if value and len(value) != 7:
            raise serializers.ValidationError('Color must be 7 characters (e.g., #2C3E50)')
        return value