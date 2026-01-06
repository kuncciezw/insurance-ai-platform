"""
Authentication and Dashboard Views
"""

from rest_framework import status, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.db.models import Sum, Count, Avg, Q
from django.utils import timezone
from datetime import timedelta

from apps.fraud_detection.models import Policyholder, Vehicle, Policy, Claim


@api_view(['POST'])
@permission_classes([AllowAny])
def register_user(request):
    """
    Register a new user
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
    
    user = User.objects.create_user(
        username=username,
        email=email,
        password=password,
        first_name=first_name,
        last_name=last_name
    )
    
    # Generate JWT tokens
    refresh = RefreshToken.for_user(user)
    
    return Response({
        'message': 'User created successfully',
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
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
    Login user and return JWT tokens
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
def dashboard_statistics(request):
    """
    Get comprehensive dashboard statistics
    """
    # Time filters
    today = timezone.now().date()
    thirty_days_ago = today - timedelta(days=30)
    
    # Policyholder statistics
    total_policyholders = Policyholder.objects.count()
    active_policyholders = Policyholder.objects.filter(is_active=True).count()
    new_policyholders_month = Policyholder.objects.filter(
        created_at__date__gte=thirty_days_ago
    ).count()
    
    # Policy statistics
    total_policies = Policy.objects.count()
    active_policies = Policy.objects.filter(status='ACTIVE').count()
    expiring_soon = Policy.objects.filter(
        status='ACTIVE',
        end_date__gte=today,
        end_date__lte=today + timedelta(days=30)
    ).count()
    
    total_premium_value = Policy.objects.filter(
        status='ACTIVE'
    ).aggregate(total=Sum('premium_amount'))['total'] or 0
    
    # Vehicle statistics
    total_vehicles = Vehicle.objects.count()
    high_value_vehicles = Vehicle.objects.filter(market_value__gt=50000).count()
    modified_vehicles = Vehicle.objects.filter(is_modified=True).count()
    
    # Claim statistics
    total_claims = Claim.objects.count()
    pending_claims = Claim.objects.filter(
        claim_status__in=['SUBMITTED', 'UNDER_REVIEW']
    ).count()
    approved_claims = Claim.objects.filter(claim_status='APPROVED').count()
    rejected_claims = Claim.objects.filter(claim_status='REJECTED').count()
    fraudulent_claims = Claim.objects.filter(is_fraudulent=True).count()
    
    total_claimed_amount = Claim.objects.aggregate(
        total=Sum('claimed_amount')
    )['total'] or 0
    
    total_approved_amount = Claim.objects.aggregate(
        total=Sum('approved_amount')
    )['total'] or 0
    
    average_fraud_score = Claim.objects.aggregate(
        avg=Avg('fraud_score')
    )['avg'] or 0
    
    # Recent activity
    recent_claims = Claim.objects.filter(
        submitted_date__date__gte=thirty_days_ago
    ).count()
    
    # Claims by type
    claims_by_type = dict(
        Claim.objects.values('claim_type').annotate(
            count=Count('id')
        ).values_list('claim_type', 'count')
    )
    
    # Claims by status
    claims_by_status = dict(
        Claim.objects.values('claim_status').annotate(
            count=Count('id')
        ).values_list('claim_status', 'count')
    )
    
    # Fraud detection metrics
    high_risk_claims = Claim.objects.filter(fraud_score__gte=0.7).count()
    fraud_detection_rate = (fraudulent_claims / total_claims * 100) if total_claims > 0 else 0
    
    # Policy type distribution
    policies_by_type = dict(
        Policy.objects.values('policy_type').annotate(
            count=Count('id')
        ).values_list('policy_type', 'count')
    )
    
    statistics = {
        'policyholders': {
            'total': total_policyholders,
            'active': active_policyholders,
            'new_this_month': new_policyholders_month,
        },
        'policies': {
            'total': total_policies,
            'active': active_policies,
            'expiring_soon': expiring_soon,
            'total_premium_value': float(total_premium_value),
            'by_type': policies_by_type,
        },
        'vehicles': {
            'total': total_vehicles,
            'high_value': high_value_vehicles,
            'modified': modified_vehicles,
        },
        'claims': {
            'total': total_claims,
            'pending': pending_claims,
            'approved': approved_claims,
            'rejected': rejected_claims,
            'fraudulent': fraudulent_claims,
            'high_risk': high_risk_claims,
            'recent_month': recent_claims,
            'total_claimed_amount': float(total_claimed_amount),
            'total_approved_amount': float(total_approved_amount),
            'average_fraud_score': float(average_fraud_score),
            'fraud_detection_rate': round(fraud_detection_rate, 2),
            'by_type': claims_by_type,
            'by_status': claims_by_status,
        },
        'summary': {
            'approval_rate': round((approved_claims / total_claims * 100) if total_claims > 0 else 0, 2),
            'rejection_rate': round((rejected_claims / total_claims * 100) if total_claims > 0 else 0, 2),
            'average_claim_value': float(
                Claim.objects.aggregate(avg=Avg('claimed_amount'))['avg'] or 0
            ),
        }
    }
    
    return Response(statistics)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_profile(request):
    """
    Get current user profile
    """
    user = request.user
    
    return Response({
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'is_staff': user.is_staff,
        'is_active': user.is_active,
        'date_joined': user.date_joined,
    })