from rest_framework import status, viewsets
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.db.models import Sum, Count, Avg
from django.utils import timezone
from datetime import timedelta

from apps.fraud_detection.models import Policyholder, Vehicle, Policy, Claim
from .models import UserProfile, CompanyProfile, RolePermission
from .serializers import (
    UserSerializer, UserListSerializer, UserCreateSerializer,
    UserUpdateSerializer, PasswordChangeSerializer, CompanyProfileSerializer
)
from .permissions import IsAdmin, IsSuperAdmin


@api_view(['POST'])
@permission_classes([AllowAny])
def register_user(request):
    """
    PUBLIC self-registration endpoint - creates pending user awaiting admin approval
    This is ONLY for users registering themselves via the public register page
    """
    username = request.data.get('username')
    email = request.data.get('email')
    password = request.data.get('password')
    first_name = request.data.get('first_name', '')
    last_name = request.data.get('last_name', '')
    
    if not username or not email or not password:
        return Response(
            {'error': 'Please provide username, email, and password'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if User.objects.filter(username=username).exists():
        return Response(
            {'error': 'Username already exists'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if User.objects.filter(email=email).exists():
        return Response(
            {'error': 'Email already exists'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Create user - Django user stays active for potential login
    user = User.objects.create_user(
        username=username,
        email=email,
        password=password,
        first_name=first_name,
        last_name=last_name,
        is_active=True  # Django user active
    )
    
    # Profile is created automatically via signal
    # Mark profile as INACTIVE/PENDING (this controls app access)
    user.profile.role = 'VIEWER'  # Default role (admin can change)
    user.profile.is_active = False  # ⭐ PENDING APPROVAL
    user.profile.save()
    
    # Generate JWT tokens
    refresh = RefreshToken.for_user(user)
    
    return Response({
        'message': 'Application submitted successfully. An administrator will review your request.',
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'role': user.profile.role,
            'role_display': user.profile.get_role_display(),
            'is_active': user.profile.is_active,  # False - pending
            'status': 'pending_approval'
        },
        'tokens': {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }
    }, status=status.HTTP_201_CREATED)
    

@api_view(['POST'])
@permission_classes([AllowAny])
def login_user(request):
    """
    Login user and return JWT tokens with role info
    """
    username = request.data.get('username')
    password = request.data.get('password')
    
    if not username or not password:
        return Response(
            {'error': 'Please provide username and password'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    user = authenticate(username=username, password=password)
    
    if user is None:
        return Response(
            {'error': 'Invalid credentials'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    if not user.is_active:
        return Response(
            {'error': 'Account is disabled'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Check if profile is active
    if hasattr(user, 'profile') and not user.profile.is_active:
        return Response(
            {'error': 'Account is disabled'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    if hasattr(user, 'profile') and not user.profile.is_active:
        return Response(
            {
                'error': 'Your account is pending approval. An administrator will review your application shortly.',
                'status': 'pending_approval'
            },
            status=status.HTTP_403_FORBIDDEN
        )
        
        
    # Update last login IP
    if hasattr(user, 'profile'):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        user.profile.last_login_ip = ip
        user.profile.save()
    
    # Generate JWT tokens
    refresh = RefreshToken.for_user(user)
    
    return Response({
        'message': 'Login successful',
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'role': user.profile.role if hasattr(user, 'profile') else 'VIEWER',
            'role_display': user.profile.get_role_display() if hasattr(user, 'profile') else 'Viewer',
            'is_active': user.profile.is_active if hasattr(user, 'profile') else True,
            'permissions': get_user_permissions(user),
        },
        'tokens': {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_user(request):
    """
    Logout user by blacklisting refresh token
    """
    try:
        refresh_token = request.data.get('refresh_token')
        token = RefreshToken(refresh_token)
        token.blacklist()
        
        return Response({
            'message': 'Logout successful'
        }, status=status.HTTP_205_RESET_CONTENT)
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_profile(request):
    """
    Get current user profile with permissions
    """
    user = request.user
    
    return Response({
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'full_name': user.get_full_name() or user.username,
        'is_staff': user.is_staff,
        'is_active': user.is_active,
        'date_joined': user.date_joined,
        'role': user.profile.role if hasattr(user, 'profile') else 'VIEWER',
        'role_display': user.profile.get_role_display() if hasattr(user, 'profile') else 'Viewer',
        'employee_id': user.profile.employee_id if hasattr(user, 'profile') else '',
        'phone_number': user.profile.phone_number if hasattr(user, 'profile') else '',
        'permissions': get_user_permissions(user),
    })


def get_user_permissions(user):
    """Helper function to get user permissions based on role"""
    if not hasattr(user, 'profile'):
        return {}
    
    profile = user.profile
    
    return {
        # User Management
        'can_create_super_admin': profile.can_create_super_admin(),
        'can_create_admin': profile.can_create_admin(),
        'can_create_users': profile.can_create_users(),
        'can_manage_users': profile.can_manage_users(),
        'can_delete_users': profile.can_delete_users(),
        
        # View Permissions
        'can_view_policyholders': profile.can_view_policyholders(),
        'can_view_vehicles': profile.can_view_vehicles(),
        'can_view_policies': profile.can_view_policies(),
        'can_view_claims': profile.can_view_claims(),
        'can_view_fraud_detection': profile.can_view_fraud_detection(),
        
        # Policyholders
        'can_create_policyholders': profile.can_create_policyholders(),
        'can_edit_policyholders': profile.can_edit_policyholders(),
        'can_delete_policyholders': profile.can_delete_policyholders(),
        
        # Policies
        'can_create_policies': profile.can_create_policies(),
        'can_edit_policies': profile.can_edit_policies(),
        'can_delete_policies': profile.can_delete_policies(),
        
        # Claims
        'can_process_claims': profile.can_process_claims(),
        'can_approve_claims': profile.can_approve_claims(),
        'can_delete_claims': profile.can_delete_claims(),
        
        # Fraud Detection
        'can_use_fraud_detection': profile.can_use_fraud_detection(),
        'can_flag_fraud': profile.can_flag_fraud(),
        
        # Premium & Estimation
        'can_calculate_premium': profile.can_calculate_premium(),
        'can_estimate_claims': profile.can_estimate_claims(),
        
        # Reports
        'can_export_reports': profile.can_export_reports(),
    }


# User Management ViewSet
class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet for user management (Admin only)
    """
    queryset = User.objects.all().select_related('profile').order_by('-date_joined')
    permission_classes = [IsAuthenticated, IsAdmin]
    
    def get_serializer_class(self):
        if self.action == 'list':
            return UserListSerializer
        elif self.action == 'create':
            return UserCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return UserUpdateSerializer
        return UserSerializer
    
    def destroy(self, request, *args, **kwargs):
        """Delete user with permission check"""
        user_to_delete = self.get_object()
        
        # Super Admin can only be deleted by Super Admin
        if hasattr(user_to_delete, 'profile'):
            if user_to_delete.profile.role == 'SUPER_ADMIN':
                if not request.user.profile.can_create_super_admin():
                    return Response(
                        {'error': 'Only Super Admin can delete Super Admin users'},
                        status=status.HTTP_403_FORBIDDEN
                    )
        
        # Can't delete yourself
        if user_to_delete == request.user:
            return Response(
                {'error': 'You cannot delete your own account'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return super().destroy(request, *args, **kwargs)
    
    @action(detail=True, methods=['post'])
    def change_password(self, request, pk=None):
        """Change user password"""
        user = self.get_object()
        
        # Only admins can change other users' passwords
        # Users can change their own password
        if user != request.user and not request.user.profile.can_manage_users():
            return Response(
                {'error': 'You do not have permission to change this password'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = PasswordChangeSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if serializer.is_valid():
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            return Response({'message': 'Password changed successfully'})
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def get_company_profile(request):
    """
    Get or update company profile settings
    GET: accessible to all authenticated users
    PUT/PATCH: Admin only
    """
    profile = CompanyProfile.get_instance()
    
    if request.method == 'GET':
        serializer = CompanyProfileSerializer(profile)
        return Response(serializer.data)
    
    # PUT/PATCH - Admin only
    if not hasattr(request.user, 'profile') or request.user.profile.role not in ['SUPER_ADMIN', 'ADMIN']:
        return Response(
            {'error': 'You do not have permission to update company profile'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    try:
        serializer = CompanyProfileSerializer(
            profile,
            data=request.data,
            partial=request.method == 'PATCH'
        )
        
        if serializer.is_valid():
            serializer.save(updated_by=request.user)
            return Response({
                'message': 'Company profile updated successfully',
                'data': serializer.data
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )




@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdmin])
def get_roles_permissions(request):
    """
    Get all roles and their current permissions.
    Returns both database values and computed effective permissions.
    """
    roles_data = {}
    permission_list = [perm[0] for perm in RolePermission.PERMISSION_CHOICES]
    
    for role_code, role_name in UserProfile.ROLE_CHOICES:
        # Create a temporary profile to get effective permissions
        temp_profile = UserProfile(role=role_code)
        
        # Get all permissions for this role
        role_permissions = {}
        for perm in permission_list:
            # Get the effective permission (from DB or default)
            role_permissions[perm] = temp_profile._check_permission(perm)
        
        roles_data[role_code] = role_permissions
    
    return Response({
        'roles': roles_data,
        'permission_list': [
            {'id': perm[0], 'label': perm[1]} 
            for perm in RolePermission.PERMISSION_CHOICES
        ]
    })


@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated, IsSuperAdmin])
def update_role_permissions(request, role_id):
    """
    Update permissions for a specific role.
    Only Super Admin can modify permissions.
    Accepts: { "permission_id": true/false, ... }
    """
    # Validate role exists
    valid_roles = [role[0] for role in UserProfile.ROLE_CHOICES]
    if role_id not in valid_roles:
        return Response(
            {'error': f'Invalid role: {role_id}'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Get valid permissions
    valid_permissions = [perm[0] for perm in RolePermission.PERMISSION_CHOICES]
    
    # Track updates
    updated = []
    errors = []
    
    # Process each permission in request
    for perm_id, enabled in request.data.items():
        if perm_id not in valid_permissions:
            errors.append(f'Invalid permission: {perm_id}')
            continue
        
        if not isinstance(enabled, bool):
            errors.append(f'Invalid value for {perm_id}: must be boolean')
            continue
        
        try:
            # Update or create permission
            RolePermission.set_permission(
                role=role_id,
                permission=perm_id,
                enabled=enabled,
                updated_by=request.user
            )
            updated.append(perm_id)
        except Exception as e:
            errors.append(f'Error updating {perm_id}: {str(e)}')
    
    response_data = {
        'message': f'Updated {len(updated)} permissions for {role_id}',
        'updated': updated,
    }
    
    if errors:
        response_data['errors'] = errors
        return Response(response_data, status=status.HTTP_207_MULTI_STATUS)
    
    return Response(response_data)


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsSuperAdmin])
def reset_role_permissions(request, role_id):
    """
    Reset a role's permissions to defaults.
    Deletes all custom permissions for the role.
    """
    valid_roles = [role[0] for role in UserProfile.ROLE_CHOICES]
    if role_id not in valid_roles:
        return Response(
            {'error': f'Invalid role: {role_id}'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Delete all custom permissions for this role
    deleted_count, _ = RolePermission.objects.filter(role=role_id).delete()
    
    return Response({
        'message': f'Reset {deleted_count} permissions for {role_id} to defaults',
        'role': role_id,
        'deleted_count': deleted_count
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsSuperAdmin])
def get_permission_audit_log(request):
    """
    Get audit log of permission changes.
    Shows who changed what and when.
    """
    permissions = RolePermission.objects.select_related('updated_by').order_by('-updated_at')
    
    # Optional filtering
    role = request.query_params.get('role')
    if role:
        permissions = permissions.filter(role=role)
    
    permission = request.query_params.get('permission')
    if permission:
        permissions = permissions.filter(permission=permission)
    
    # Limit results
    limit = int(request.query_params.get('limit', 100))
    permissions = permissions[:limit]
    
    data = []
    for perm in permissions:
        data.append({
            'role': perm.role,
            'role_display': perm.get_role_display(),
            'permission': perm.permission,
            'permission_display': perm.get_permission_display(),
            'enabled': perm.enabled,
            'updated_at': perm.updated_at,
            'updated_by': perm.updated_by.username if perm.updated_by else None,
            'updated_by_name': perm.updated_by.get_full_name() if perm.updated_by else None,
        })
    
    return Response({
        'count': len(data),
        'results': data
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsSuperAdmin])
def bulk_update_permissions(request):
    """
    Bulk update permissions for multiple roles at once.
    Format: {
        "ADMIN": { "can_delete_users": true, ... },
        "VIEWER": { "can_view_claims": false, ... }
    }
    """
    if not isinstance(request.data, dict):
        return Response(
            {'error': 'Request body must be an object with role keys'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    valid_roles = [role[0] for role in UserProfile.ROLE_CHOICES]
    valid_permissions = [perm[0] for perm in RolePermission.PERMISSION_CHOICES]
    
    results = {}
    errors = []
    
    for role_id, permissions in request.data.items():
        if role_id not in valid_roles:
            errors.append(f'Invalid role: {role_id}')
            continue
        
        if not isinstance(permissions, dict):
            errors.append(f'Permissions for {role_id} must be an object')
            continue
        
        updated = []
        for perm_id, enabled in permissions.items():
            if perm_id not in valid_permissions:
                errors.append(f'{role_id}: Invalid permission {perm_id}')
                continue
            
            if not isinstance(enabled, bool):
                errors.append(f'{role_id}: Invalid value for {perm_id}')
                continue
            
            try:
                RolePermission.set_permission(
                    role=role_id,
                    permission=perm_id,
                    enabled=enabled,
                    updated_by=request.user
                )
                updated.append(perm_id)
            except Exception as e:
                errors.append(f'{role_id}: Error updating {perm_id} - {str(e)}')
        
        results[role_id] = {
            'updated_count': len(updated),
            'updated': updated
        }
    
    response_data = {
        'message': 'Bulk update completed',
        'results': results
    }
    
    if errors:
        response_data['errors'] = errors
        return Response(response_data, status=status.HTTP_207_MULTI_STATUS)
    
    return Response(response_data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_statistics(request):
    """
    Get comprehensive dashboard statistics (filtered by role if needed)
    """
    # Time filters
    today = timezone.now().date()
    thirty_days_ago = today - timedelta(days=30)
    
    user = request.user
    profile = user.profile if hasattr(user, 'profile') else None
    
    # Base statistics (everyone can see)
    total_policyholders = Policyholder.objects.count()
    active_policyholders = Policyholder.objects.filter(is_active=True).count()
    
    total_policies = Policy.objects.count()
    active_policies = Policy.objects.filter(status='ACTIVE').count()
    
    total_vehicles = Vehicle.objects.count()
    
    total_claims = Claim.objects.count()
    pending_claims = Claim.objects.filter(
        claim_status__in=['SUBMITTED', 'UNDER_REVIEW']
    ).count()
    
    # Role-specific data
    statistics = {
        'total_policyholders': total_policyholders,
        'active_policyholders': active_policyholders,
        'total_policies': total_policies,
        'active_policies': active_policies,
        'total_vehicles': total_vehicles,
        'total_claims': total_claims,
        'pending_claims': pending_claims,
    }
    
    # Add sensitive financial data only for authorized roles
    if profile and profile.role in ['SUPER_ADMIN', 'ADMIN', 'UNDERWRITER', 'CLAIMS_ADJUSTER']:
        total_premium_amount = Policy.objects.filter(
            status='ACTIVE'
        ).aggregate(total=Sum('premium_amount'))['total'] or 0
        
        total_claims_amount = Claim.objects.filter(
            claim_status='APPROVED'
        ).aggregate(total=Sum('approved_amount'))['total'] or 0
        
        statistics.update({
            'total_premium_amount': float(total_premium_amount),
            'total_claims_amount': float(total_claims_amount),
        })
    
    # Add fraud statistics only for authorized roles
    if profile and profile.role in ['SUPER_ADMIN', 'ADMIN', 'CLAIMS_ADJUSTER', 'FRAUD_INVESTIGATOR']:
        fraudulent_claims = Claim.objects.filter(is_fraudulent=True).count()
        high_risk_claims = Claim.objects.filter(fraud_score__gte=0.7).count()
        average_fraud_score = Claim.objects.aggregate(avg=Avg('fraud_score'))['avg'] or 0
        
        statistics.update({
            'fraudulent_claims': fraudulent_claims,
            'high_risk_claims': high_risk_claims,
            'average_fraud_score': float(average_fraud_score),
        })
    
    return Response(statistics)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def claims_activity(request):
    """Get claims activity data for charts"""
    period = request.query_params.get('period', '12months')
    
    today = timezone.now().date()
    
    if period == '7days':
        data = []
        days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        for i in range(7):
            date = today - timedelta(days=6-i)
            count = Claim.objects.filter(submitted_date__date=date).count()
            data.append({'label': days[date.weekday()], 'count': count})
    
    elif period == '30days':
        data = []
        for i in range(4):
            start_date = today - timedelta(days=(4-i)*7)
            end_date = start_date + timedelta(days=7)
            count = Claim.objects.filter(
                submitted_date__date__gte=start_date,
                submitted_date__date__lt=end_date
            ).count()
            data.append({'label': f'Week {i+1}', 'count': count})
    
    elif period == '12months':
        data = []
        months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                  'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        for i in range(12):
            month_date = today - timedelta(days=30*(11-i))
            count = Claim.objects.filter(
                submitted_date__year=month_date.year,
                submitted_date__month=month_date.month
            ).count()
            data.append({'label': months[month_date.month-1], 'count': count})
    
    else:
        data = []
        for i in range(4):
            quarter_start = today - timedelta(days=365) + timedelta(days=i*91)
            quarter_end = quarter_start + timedelta(days=91)
            count = Claim.objects.filter(
                submitted_date__date__gte=quarter_start,
                submitted_date__date__lt=quarter_end
            ).count()
            data.append({'label': f'Q{i+1}', 'count': count})
    
    return Response(data)