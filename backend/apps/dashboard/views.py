from __future__ import annotations

from datetime import timedelta
from typing import Any, Type

from django.contrib.auth import authenticate
from django.contrib.auth.models import AbstractUser, User
from django.db.models import Avg, Sum
from django.utils import timezone
from rest_framework import serializers as drf_serializers
from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from apps.fraud_detection.models import Claim, Policy, Policyholder, Vehicle
from system_settings.models import GlobalPricingSettings  # <-- ADDED: Import Global Settings

from .models import CompanyProfile, RolePermission, UserProfile
from .permissions import IsAdmin, IsSuperAdmin
from .serializers import (
    CompanyProfileSerializer,
    PasswordChangeSerializer,
    UserCreateSerializer,
    UserListSerializer,
    UserSerializer,
    UserUpdateSerializer,
)


def _get_profile(user: AbstractUser) -> UserProfile | None:
    return getattr(user, 'profile', None)


@api_view(['POST'])
@permission_classes([AllowAny])
def register_user(request: Request) -> Response:
    payload: dict[str, Any] = request.data  # type: ignore[assignment]
    username = payload.get('username')
    email = payload.get('email')
    password = payload.get('password')
    first_name = payload.get('first_name', '')
    last_name = payload.get('last_name', '')

    if not username or not email or not password:
        return Response(
            {'error': 'Please provide username, email, and password'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if User.objects.filter(username=username).exists():
        return Response({'error': 'Username already exists'}, status=status.HTTP_400_BAD_REQUEST)

    if User.objects.filter(email=email).exists():
        return Response({'error': 'Email already exists'}, status=status.HTTP_400_BAD_REQUEST)

    user = User.objects.create_user(
        username=username,
        email=email,
        password=password,
        first_name=first_name,
        last_name=last_name,
        is_active=True,
    )

    profile = _get_profile(user)
    if profile is not None:
        profile.role = 'VIEWER'
        profile.is_active = False
        profile.save()

    refresh = RefreshToken.for_user(user)

    return Response(
        {
            'message': 'Application submitted successfully. An administrator will review your request.',
            'user': {
                'id': user.pk,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'role': profile.role if profile else 'VIEWER',
                'is_active': profile.is_active if profile else False,
                'status': 'pending_approval',
            },
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            },
        },
        status=status.HTTP_201_CREATED,
    )


@api_view(['POST'])
@permission_classes([AllowAny])
def login_user(request: Request) -> Response:
    payload: dict[str, Any] = request.data  # type: ignore[assignment]
    username = payload.get('username')
    password = payload.get('password')

    if not username or not password:
        return Response(
            {'error': 'Please provide username and password'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    user = authenticate(username=username, password=password)

    if user is None:
        return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

    if not user.is_active:
        return Response({'error': 'Account is disabled'}, status=status.HTTP_403_FORBIDDEN)

    profile = _get_profile(user)

    if profile is not None and not profile.is_active:
        return Response(
            {
                'error': 'Your account is pending approval. An administrator will review your application shortly.',
                'status': 'pending_approval',
            },
            status=status.HTTP_403_FORBIDDEN,
        )

    if profile is not None:
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        profile.last_login_ip = ip
        profile.save()

    refresh = RefreshToken.for_user(user)

    return Response({
        'message': 'Login successful',
        'user': {
            'id': user.pk,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'role': profile.role if profile else 'VIEWER',
            'role_display': dict(UserProfile.ROLE_CHOICES).get(profile.role, 'Viewer') if profile else 'Viewer',
            'is_active': profile.is_active if profile else True,
            'permissions': get_user_permissions(user),
        },
        'tokens': {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        },
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_user(request: Request) -> Response:
    try:
        payload: dict[str, Any] = request.data  # type: ignore[assignment]
        refresh_token = str(payload.get('refresh_token', ''))
        token = RefreshToken(refresh_token)  # type: ignore[arg-type]
        token.blacklist()
        return Response({'message': 'Logout successful'}, status=status.HTTP_205_RESET_CONTENT)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_profile(request: Request) -> Response:
    user = request.user
    profile = _get_profile(user)

    return Response({
        'id': user.pk,
        'username': user.username,
        'email': user.email,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'full_name': user.get_full_name() or user.username,
        'is_staff': user.is_staff,
        'is_active': user.is_active,
        'date_joined': user.date_joined,
        'role': profile.role if profile else 'VIEWER',
        'role_display': dict(UserProfile.ROLE_CHOICES).get(profile.role, 'Viewer') if profile else 'Viewer',
        'employee_id': profile.employee_id if profile else '',
        'phone_number': profile.phone_number if profile else '',
        'permissions': get_user_permissions(user),
    })


def get_user_permissions(user: AbstractUser) -> dict[str, bool]:
    profile = _get_profile(user)
    if profile is None:
        return {}

    return {
        'can_create_super_admin': profile.can_create_super_admin(),
        'can_create_admin': profile.can_create_admin(),
        'can_create_users': profile.can_create_users(),
        'can_manage_users': profile.can_manage_users(),
        'can_delete_users': profile.can_delete_users(),
        'can_view_policyholders': profile.can_view_policyholders(),
        'can_view_vehicles': profile.can_view_vehicles(),
        'can_view_policies': profile.can_view_policies(),
        'can_view_claims': profile.can_view_claims(),
        'can_view_fraud_detection': profile.can_view_fraud_detection(),
        'can_create_policyholders': profile.can_create_policyholders(),
        'can_edit_policyholders': profile.can_edit_policyholders(),
        'can_delete_policyholders': profile.can_delete_policyholders(),
        'can_create_policies': profile.can_create_policies(),
        'can_edit_policies': profile.can_edit_policies(),
        'can_delete_policies': profile.can_delete_policies(),
        'can_process_claims': profile.can_process_claims(),
        'can_approve_claims': profile.can_approve_claims(),
        'can_delete_claims': profile.can_delete_claims(),
        'can_use_fraud_detection': profile.can_use_fraud_detection(),
        'can_flag_fraud': profile.can_flag_fraud(),
        'can_calculate_premium': profile.can_calculate_premium(),
        'can_estimate_claims': profile.can_estimate_claims(),
        'can_export_reports': profile.can_export_reports(),
    }


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().select_related('profile').order_by('-date_joined')
    permission_classes = [IsAuthenticated, IsAdmin]

    def get_serializer_class(self) -> Type[drf_serializers.Serializer]:  # type: ignore[override]
        if self.action == 'list':
            return UserListSerializer
        if self.action == 'create':
            return UserCreateSerializer
        if self.action in ('update', 'partial_update'):
            return UserUpdateSerializer
        return UserSerializer

    def destroy(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        user_to_delete: User = self.get_object()
        profile = _get_profile(user_to_delete)
        requester_profile = _get_profile(request.user)  # type: ignore[arg-type]

        if profile and profile.role == 'SUPER_ADMIN':
            if requester_profile is None or not requester_profile.can_create_super_admin():
                return Response(
                    {'error': 'Only Super Admin can delete Super Admin users'},
                    status=status.HTTP_403_FORBIDDEN,
                )

        if user_to_delete == request.user:
            return Response(
                {'error': 'You cannot delete your own account'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return super().destroy(request, *args, **kwargs)

    @action(detail=True, methods=['post'])
    def change_password(self, request: Request, pk: Any = None) -> Response:
        user: User = self.get_object()
        requester_profile = _get_profile(request.user)  # type: ignore[arg-type]

        if user != request.user and (
            requester_profile is None or not requester_profile.can_manage_users()
        ):
            return Response(
                {'error': 'You do not have permission to change this password'},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = PasswordChangeSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            return Response({'message': 'Password changed successfully'})

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def get_company_profile(request: Request) -> Response:
    profile = CompanyProfile.get_instance()

    if request.method == 'GET':
        serializer = CompanyProfileSerializer(profile)
        return Response(serializer.data)

    requester_profile = _get_profile(request.user)  # type: ignore[arg-type]
    if requester_profile is None or requester_profile.role not in ('SUPER_ADMIN', 'ADMIN'):
        return Response(
            {'error': 'You do not have permission to update company profile'},
            status=status.HTTP_403_FORBIDDEN,
        )

    try:
        serializer = CompanyProfileSerializer(
            profile,
            data=request.data,
            partial=request.method == 'PATCH',
        )
        if serializer.is_valid():
            serializer.save(updated_by=request.user)
            return Response({'message': 'Company profile updated successfully', 'data': serializer.data})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdmin])
def get_roles_permissions(request: Request) -> Response:
    roles_data: dict[str, dict[str, bool]] = {}
    permission_list = [perm[0] for perm in RolePermission.PERMISSION_CHOICES]

    for role_code, _ in UserProfile.ROLE_CHOICES:
        temp_profile = UserProfile(role=role_code)
        role_permissions: dict[str, bool] = {}
        for perm in permission_list:
            role_permissions[perm] = temp_profile._check_permission(perm)
        roles_data[role_code] = role_permissions

    return Response({
        'roles': roles_data,
        'permission_list': [
            {'id': perm[0], 'label': perm[1]}
            for perm in RolePermission.PERMISSION_CHOICES
        ],
    })


@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated, IsSuperAdmin])
def update_role_permissions(request: Request, role_id: str) -> Response:
    valid_roles = [role[0] for role in UserProfile.ROLE_CHOICES]
    if role_id not in valid_roles:
        return Response({'error': f'Invalid role: {role_id}'}, status=status.HTTP_400_BAD_REQUEST)

    valid_permissions = [perm[0] for perm in RolePermission.PERMISSION_CHOICES]
    updated: list[str] = []
    errors: list[str] = []

    for perm_id, enabled in request.data.items(): # type: ignore
        if perm_id not in valid_permissions:
            errors.append(f'Invalid permission: {perm_id}')
            continue
        if not isinstance(enabled, bool):
            errors.append(f'Invalid value for {perm_id}: must be boolean')
            continue
        try:
            RolePermission.set_permission(
                role=role_id,
                permission=perm_id,
                enabled=enabled,
                updated_by=request.user,  # type: ignore[arg-type]
            )
            updated.append(perm_id)
        except Exception as e:
            errors.append(f'Error updating {perm_id}: {str(e)}')

    response_data: dict[str, Any] = {
        'message': f'Updated {len(updated)} permissions for {role_id}',
        'updated': updated,
    }
    if errors:
        response_data['errors'] = errors
        return Response(response_data, status=status.HTTP_207_MULTI_STATUS)

    return Response(response_data)


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsSuperAdmin])
def reset_role_permissions(request: Request, role_id: str) -> Response:
    valid_roles = [role[0] for role in UserProfile.ROLE_CHOICES]
    if role_id not in valid_roles:
        return Response({'error': f'Invalid role: {role_id}'}, status=status.HTTP_400_BAD_REQUEST)

    deleted_count, _ = RolePermission.objects.filter(role=role_id).delete()
    return Response({
        'message': f'Reset {deleted_count} permissions for {role_id} to defaults',
        'role': role_id,
        'deleted_count': deleted_count,
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsSuperAdmin])
def get_permission_audit_log(request: Request) -> Response:
    permissions_qs = RolePermission.objects.select_related('updated_by').order_by('-updated_at')

    role = request.query_params.get('role')
    if role:
        permissions_qs = permissions_qs.filter(role=role)

    permission = request.query_params.get('permission')
    if permission:
        permissions_qs = permissions_qs.filter(permission=permission)

    limit = int(request.query_params.get('limit', 100))
    permissions_qs = permissions_qs[:limit]

    role_labels = dict(RolePermission.ROLE_CHOICES)
    perm_labels = dict(RolePermission.PERMISSION_CHOICES)

    data = [
        {
            'role': perm.role,
            'role_display': role_labels.get(perm.role, perm.role),
            'permission': perm.permission,
            'permission_display': perm_labels.get(perm.permission, perm.permission),
            'enabled': perm.enabled,
            'updated_at': perm.updated_at,
            'updated_by': perm.updated_by.username if perm.updated_by else None,
            'updated_by_name': perm.updated_by.get_full_name() if perm.updated_by else None,
        }
        for perm in permissions_qs
    ]

    return Response({'count': len(data), 'results': data})


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsSuperAdmin])
def bulk_update_permissions(request: Request) -> Response:
    payload: dict[str, Any] = request.data  # type: ignore[assignment]
    if not isinstance(payload, dict):
        return Response(
            {'error': 'Request body must be an object with role keys'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    valid_roles = [role[0] for role in UserProfile.ROLE_CHOICES]
    valid_permissions = [perm[0] for perm in RolePermission.PERMISSION_CHOICES]

    results: dict[str, Any] = {}
    errors: list[str] = []

    for role_id, permissions in payload.items():
        if role_id not in valid_roles:
            errors.append(f'Invalid role: {role_id}')
            continue
        if not isinstance(permissions, dict):
            errors.append(f'Permissions for {role_id} must be an object')
            continue

        updated: list[str] = []
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
                    updated_by=request.user,  # type: ignore[arg-type]
                )
                updated.append(perm_id)
            except Exception as e:
                errors.append(f'{role_id}: Error updating {perm_id} - {str(e)}')

        results[role_id] = {'updated_count': len(updated), 'updated': updated}

    response_data: dict[str, Any] = {'message': 'Bulk update completed', 'results': results}
    if errors:
        response_data['errors'] = errors
        return Response(response_data, status=status.HTTP_207_MULTI_STATUS)

    return Response(response_data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_statistics(request: Request) -> Response:
    user = request.user
    profile = _get_profile(user)

    statistics: dict[str, Any] = {
        'total_policyholders': Policyholder.objects.count(),
        'active_policyholders': Policyholder.objects.filter(is_active=True).count(),
        'total_policies': Policy.objects.count(),
        'active_policies': Policy.objects.filter(status='ACTIVE').count(),
        'total_vehicles': Vehicle.objects.count(),
        'total_claims': Claim.objects.count(),
        'pending_claims': Claim.objects.filter(
            claim_status__in=['SUBMITTED', 'UNDER_REVIEW']
        ).count(),
    }

    if profile and profile.role in ('SUPER_ADMIN', 'ADMIN', 'UNDERWRITER', 'CLAIMS_ADJUSTER'):
        premium_qs = (
            Policy.objects.filter(status='ACTIVE')
            .values('currency')
            .annotate(total=Sum('premium_amount'))
        )
        claims_qs = (
            Claim.objects.filter(claim_status='APPROVED')
            .values('policy__currency')
            .annotate(total=Sum('approved_amount'))
        )

        premiums_by_currency = {
            row['currency']: float(row['total'] or 0) for row in premium_qs
        }
        claims_by_currency = {
            row['policy__currency']: float(row['total'] or 0) for row in claims_qs
        }

        statistics['financials'] = {
            'premiums': premiums_by_currency,
            'claims': claims_by_currency,
        }

    if profile and profile.role in ('SUPER_ADMIN', 'ADMIN', 'CLAIMS_ADJUSTER', 'FRAUD_INVESTIGATOR'):
        # --> INTEGRATED: Fetch Global Pricing Settings
        settings = GlobalPricingSettings.get_solo()
        average_fraud_score = Claim.objects.aggregate(avg=Avg('fraud_score'))['avg'] or 0
        
        statistics['fraud'] = {
            'fraudulent_claims': Claim.objects.filter(is_fraudulent=True).count(),
            # --> INTEGRATED: Use dynamic variance warning threshold instead of hardcoded 0.7
            'high_risk_claims': Claim.objects.filter(fraud_score__gte=settings.threshold_variance_warning).count(),
            'average_fraud_score': float(average_fraud_score),
        }

    return Response(statistics)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def claims_activity(request: Request) -> Response:
    period = request.query_params.get('period', '12months')
    today = timezone.now().date()

    data: list[dict[str, Any]] = []

    if period == '7days':
        days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        for i in range(7):
            date = today - timedelta(days=6 - i)
            count = Claim.objects.filter(submitted_date__date=date).count()
            data.append({'label': days[date.weekday()], 'count': count})

    elif period == '30days':
        for i in range(4):
            start_date = today - timedelta(days=(4 - i) * 7)
            end_date = start_date + timedelta(days=7)
            count = Claim.objects.filter(
                submitted_date__date__gte=start_date,
                submitted_date__date__lt=end_date,
            ).count()
            data.append({'label': f'Week {i + 1}', 'count': count})

    elif period == '12months':
        months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                  'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        for i in range(12):
            month_date = today - timedelta(days=30 * (11 - i))
            count = Claim.objects.filter(
                submitted_date__year=month_date.year,
                submitted_date__month=month_date.month,
            ).count()
            data.append({'label': months[month_date.month - 1], 'count': count})

    else:
        for i in range(4):
            quarter_start = today - timedelta(days=365) + timedelta(days=i * 91)
            quarter_end = quarter_start + timedelta(days=91)
            count = Claim.objects.filter(
                submitted_date__date__gte=quarter_start,
                submitted_date__date__lt=quarter_end,
            ).count()
            data.append({'label': f'Q{i + 1}', 'count': count})

    return Response(data)