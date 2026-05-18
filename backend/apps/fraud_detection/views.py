"""
API ViewSets for Fraud Detection Application
Updated with corrected filter fields
"""

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count, Sum, Avg, Q
from django.utils import timezone
from datetime import timedelta

from .models import Policyholder, Vehicle, Policy, Claim
from .serializers import (
    PolicyholderSerializer, PolicyholderListSerializer,
    VehicleSerializer, VehicleListSerializer,
    PolicySerializer, PolicyListSerializer,
    ClaimSerializer, ClaimListSerializer,
    ClaimFraudAnalysisSerializer
)


class PolicyholderViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Policyholders
    
    Provides CRUD operations and additional filtering capabilities
    """
    queryset = Policyholder.objects.all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['gender', 'marital_status', 'occupation', 'is_active', 'state', 'city', 'credit_rating']
    search_fields = ['first_name', 'last_name', 'email', 'policy_holder_id', 'phone_number']
    ordering_fields = ['created_at', 'last_name', 'credit_score', 'monthly_income']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        """Use different serializers for list and detail views"""
        if self.action == 'list':
            return PolicyholderListSerializer
        return PolicyholderSerializer
    
    def get_permissions(self):
        """Allow unauthenticated creation (registration), require auth for other operations"""
        if self.action == 'create':
            return [AllowAny()]
        return [IsAuthenticated()]
    
    @action(detail=True, methods=['get'])
    def policies(self, request, pk=None):
        """Get all policies for a specific policyholder"""
        policyholder = self.get_object()
        policies = policyholder.policies.all()
        serializer = PolicyListSerializer(policies, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def vehicles(self, request, pk=None):
        """Get all vehicles for a specific policyholder"""
        policyholder = self.get_object()
        vehicles = policyholder.vehicles.all()
        serializer = VehicleListSerializer(vehicles, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def claims(self, request, pk=None):
        """Get all claims for a specific policyholder"""
        policyholder = self.get_object()
        claims = policyholder.claims.all()
        serializer = ClaimListSerializer(claims, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def statistics(self, request, pk=None):
        """Get statistical summary for a policyholder"""
        policyholder = self.get_object()
        
        stats = {
            'total_policies': policyholder.policies.count(),
            'active_policies': policyholder.policies.filter(status='ACTIVE').count(),
            'total_vehicles': policyholder.vehicles.count(),
            'total_claims': policyholder.claims.count(),
            'pending_claims': policyholder.claims.filter(claim_status='SUBMITTED').count(),
            'approved_claims': policyholder.claims.filter(claim_status='APPROVED').count(),
            'total_claimed_amount': policyholder.claims.aggregate(
                total=Sum('claimed_amount')
            )['total'] or 0,
            'fraudulent_claims': policyholder.claims.filter(is_fraudulent=True).count(),
        }
        
        return Response(stats)
    
    @action(detail=False, methods=['get'])
    def high_risk(self, request):
        """Get policyholders with high-risk indicators"""
        high_risk_holders = Policyholder.objects.filter(
            Q(credit_score__lt=600) | 
            Q(claims__is_fraudulent=True) |
            Q(has_driving_license=False) |
            Q(is_medical_license_valid=False)
        ).distinct()
        
        serializer = self.get_serializer(high_risk_holders, many=True)
        return Response(serializer.data)


class VehicleViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Vehicles
    """
    queryset = Vehicle.objects.select_related('policyholder').all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    # Updated filterset_fields - removed 'vehicle_id', changed 'year' to 'manufacture_year'
    filterset_fields = ['vehicle_type', 'fuel_type', 'manufacture_year', 'make', 'has_anti_theft', 'is_modified']
    search_fields = ['vin', 'registration_number', 'make', 'model']
    ordering_fields = ['created_at', 'manufacture_year', 'market_value', 'odometer_reading']
    ordering = ['-created_at']
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        """Use different serializers for list and detail views"""
        if self.action == 'list':
            return VehicleListSerializer
        return VehicleSerializer
    
    @action(detail=True, methods=['get'])
    def policies(self, request, pk=None):
        """Get all policies for a specific vehicle"""
        vehicle = self.get_object()
        policies = vehicle.policies.all()
        serializer = PolicyListSerializer(policies, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def claims(self, request, pk=None):
        """Get all claims for a specific vehicle"""
        vehicle = self.get_object()
        claims = vehicle.claims.all()
        serializer = ClaimListSerializer(claims, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def high_value(self, request):
        """Get high-value vehicles (market value > $50,000)"""
        high_value_vehicles = Vehicle.objects.filter(market_value__gt=50000)
        serializer = self.get_serializer(high_value_vehicles, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def modified_vehicles(self, request):
        """Get all modified vehicles"""
        modified = Vehicle.objects.filter(is_modified=True)
        serializer = self.get_serializer(modified, many=True)
        return Response(serializer.data)


class PolicyViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Insurance Policies
    """
    queryset = Policy.objects.select_related('policyholder', 'vehicle').all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'policy_type', 'coverage_level', 'currency']
    search_fields = ['policy_number', 'policyholder__first_name', 'policyholder__last_name']
    ordering_fields = ['created_at', 'start_date', 'end_date', 'premium_amount']
    ordering = ['-created_at']
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        """Use different serializers for list and detail views"""
        if self.action == 'list':
            return PolicyListSerializer
        return PolicySerializer
    
    @action(detail=True, methods=['get'])
    def claims(self, request, pk=None):
        """Get all claims for a specific policy"""
        policy = self.get_object()
        claims = policy.claims.all()
        serializer = ClaimListSerializer(claims, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def active(self, request):
        """Get all active policies"""
        active_policies = Policy.objects.filter(status='ACTIVE')
        serializer = self.get_serializer(active_policies, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def expiring_soon(self, request):
        """Get policies expiring within next 30 days"""
        today = timezone.now().date()
        thirty_days_later = today + timedelta(days=30)
        
        expiring = Policy.objects.filter(
            status='ACTIVE',
            end_date__gte=today,
            end_date__lte=thirty_days_later
        )
        
        serializer = self.get_serializer(expiring, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def renew(self, request, pk=None):
        """Renew a policy"""
        policy = self.get_object()
        
        if policy.status != 'ACTIVE' and policy.status != 'EXPIRED':
            return Response(
                {'error': 'Only active or expired policies can be renewed'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create new policy based on current one
        new_policy = Policy.objects.create(
            policy_number=f"POL-{timezone.now().timestamp()}",
            policyholder=policy.policyholder,
            vehicle=policy.vehicle,
            policy_type=policy.policy_type,
            coverage_level=policy.coverage_level,
            status='PENDING',
            currency=policy.currency,
            start_date=policy.end_date,
            end_date=policy.end_date + timedelta(days=365),
            has_roadside_assistance=policy.has_roadside_assistance,
            has_rental_coverage=policy.has_rental_coverage,
            has_glass_coverage=policy.has_glass_coverage
        )
        
        serializer = self.get_serializer(new_policy)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get policy statistics"""
        stats = {
            'total_policies': Policy.objects.count(),
            'active_policies': Policy.objects.filter(status='ACTIVE').count(),
            'expired_policies': Policy.objects.filter(status='EXPIRED').count(),
            'cancelled_policies': Policy.objects.filter(status='CANCELLED').count(),
            'total_premium_value': Policy.objects.filter(
                status='ACTIVE'
            ).aggregate(total=Sum('premium_amount'))['total'] or 0,
            'average_premium': Policy.objects.filter(
                status='ACTIVE'
            ).aggregate(avg=Avg('premium_amount'))['avg'] or 0,
            'policies_by_type': dict(
                Policy.objects.values('policy_type').annotate(count=Count('id')).values_list('policy_type', 'count')
            )
        }
        
        return Response(stats)


class ClaimViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Insurance Claims
    """
    queryset = Claim.objects.select_related('policy', 'policyholder', 'vehicle').all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    # Updated filterset_fields - removed fields that no longer exist
    filterset_fields = [
        'claim_status', 'claim_type', 'severity', 'is_fraudulent', 'payment_method'
    ]
    search_fields = [
        'claim_number', 
        'policyholder__first_name', 'policyholder__last_name'
    ]
    ordering_fields = [
        'submitted_date', 'incident_date', 'claimed_amount', 
        'fraud_score', 'claim_status'
    ]
    ordering = ['-submitted_date']
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        """Use different serializers for list and detail views"""
        if self.action == 'list':
            return ClaimListSerializer
        elif self.action == 'fraud_analysis':
            return ClaimFraudAnalysisSerializer
        return ClaimSerializer
    
    @action(detail=False, methods=['get'])
    def pending(self, request):
        """Get all pending claims"""
        pending_claims = Claim.objects.filter(
            claim_status__in=['SUBMITTED', 'UNDER_REVIEW']
        )
        serializer = self.get_serializer(pending_claims, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def fraudulent(self, request):
        """Get all claims flagged as fraudulent"""
        fraudulent_claims = Claim.objects.filter(
            Q(is_fraudulent=True) | Q(fraud_score__gte=0.7)
        )
        serializer = self.get_serializer(fraudulent_claims, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def high_value(self, request):
        """Get high-value claims (>$10,000)"""
        high_value_claims = Claim.objects.filter(claimed_amount__gt=10000)
        serializer = self.get_serializer(high_value_claims, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve a claim"""
        claim = self.get_object()
        
        if claim.claim_status not in ['SUBMITTED', 'UNDER_REVIEW']:
            return Response(
                {'error': 'Only submitted or under review claims can be approved'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        approved_amount = request.data.get('approved_amount', claim.claimed_amount)
        
        claim.claim_status = 'APPROVED'
        claim.approved_amount = approved_amount
        claim.reviewed_date = timezone.now()
        claim.save()
        
        serializer = self.get_serializer(claim)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Reject a claim"""
        claim = self.get_object()
        
        if claim.claim_status not in ['SUBMITTED', 'UNDER_REVIEW']:
            return Response(
                {'error': 'Only submitted or under review claims can be rejected'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        rejection_reason = request.data.get('reason', 'No reason provided')
        
        claim.claim_status = 'REJECTED'
        claim.fraud_reason = rejection_reason
        claim.reviewed_date = timezone.now()
        claim.save()
        
        serializer = self.get_serializer(claim)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def mark_paid(self, request, pk=None):
        """Mark claim as paid"""
        claim = self.get_object()
        
        if claim.claim_status != 'APPROVED':
            return Response(
                {'error': 'Only approved claims can be marked as paid'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        paid_amount = request.data.get('paid_amount', claim.approved_amount)
        
        claim.claim_status = 'PAID'
        claim.paid_amount = paid_amount
        claim.save()
        
        serializer = self.get_serializer(claim)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def fraud_analysis(self, request, pk=None):
        """Get fraud analysis for a specific claim"""
        claim = self.get_object()
        serializer = ClaimFraudAnalysisSerializer(claim)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get claim statistics"""
        stats = {
            'total_claims': Claim.objects.count(),
            'pending_claims': Claim.objects.filter(
                claim_status__in=['SUBMITTED', 'UNDER_REVIEW']
            ).count(),
            'approved_claims': Claim.objects.filter(claim_status='APPROVED').count(),
            'rejected_claims': Claim.objects.filter(claim_status='REJECTED').count(),
            'paid_claims': Claim.objects.filter(claim_status='PAID').count(),
            'fraudulent_claims': Claim.objects.filter(is_fraudulent=True).count(),
            'total_claimed_amount': Claim.objects.aggregate(
                total=Sum('claimed_amount')
            )['total'] or 0,
            'total_approved_amount': Claim.objects.aggregate(
                total=Sum('approved_amount')
            )['total'] or 0,
            'total_paid_amount': Claim.objects.aggregate(
                total=Sum('paid_amount')
            )['total'] or 0,
            'average_claim_amount': Claim.objects.aggregate(
                avg=Avg('claimed_amount')
            )['avg'] or 0,
            'claims_by_type': dict(
                Claim.objects.values('claim_type').annotate(
                    count=Count('id')
                ).values_list('claim_type', 'count')
            ),
            'claims_by_status': dict(
                Claim.objects.values('claim_status').annotate(
                    count=Count('id')
                ).values_list('claim_status', 'count')
            )
        }
        
        return Response(stats)
    
    @action(detail=False, methods=['get'])
    def recent_activity(self, request):
        """Get recent claim activity (last 30 days)"""
        thirty_days_ago = timezone.now() - timedelta(days=30)
        recent_claims = Claim.objects.filter(
            submitted_date__gte=thirty_days_ago
        ).order_by('-submitted_date')[:50]
        
        serializer = self.get_serializer(recent_claims, many=True)
        return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def fraud_statistics_chart(request):
    """
    Get fraud detection statistics for dashboard charts
    
    GET /api/fraud-detection/stats/?period=30days
    
    Query Parameters:
    - period: Time period (7days, 30days, 90days, 1year)
    
    Response:
    {
        "low_risk": 158,
        "medium_risk": 28,
        "high_risk": 12,
        "fraud_rate": 6.1,
        "low_risk_percentage": 79.8,
        "medium_risk_percentage": 14.1,
        "high_risk_percentage": 6.1
    }
    """
    
    period = request.query_params.get('period', '30days')
    today = timezone.now().date()
    
    # Calculate date range
    if period == '7days':
        start_date = today - timedelta(days=7)
    elif period == '30days':
        start_date = today - timedelta(days=30)
    elif period == '90days':
        start_date = today - timedelta(days=90)
    else:  # '1year'
        start_date = today - timedelta(days=365)
    
    # Filter claims in period
    claims = Claim.objects.filter(submitted_date__date__gte=start_date)
    
    # Categorize by fraud score
    # Low risk: fraud_score < 0.3
    # Medium risk: 0.3 <= fraud_score < 0.7
    # High risk: fraud_score >= 0.7
    low_risk = claims.filter(fraud_score__lt=0.3).count()
    medium_risk = claims.filter(fraud_score__gte=0.3, fraud_score__lt=0.7).count()
    high_risk = claims.filter(fraud_score__gte=0.7).count()
    
    total = low_risk + medium_risk + high_risk
    
    if total == 0:
        return Response({
            'low_risk': 0,
            'medium_risk': 0,
            'high_risk': 0,
            'fraud_rate': 0,
            'low_risk_percentage': 0,
            'medium_risk_percentage': 0,
            'high_risk_percentage': 0,
            'period': period,
            'total_claims': 0
        })
    
    # Calculate fraud rate (high risk claims percentage)
    fraud_rate = (high_risk / total * 100) if total > 0 else 0
    
    return Response({
        'low_risk': low_risk,
        'medium_risk': medium_risk,
        'high_risk': high_risk,
        'fraud_rate': round(fraud_rate, 1),
        'low_risk_percentage': round((low_risk / total * 100), 1),
        'medium_risk_percentage': round((medium_risk / total * 100), 1),
        'high_risk_percentage': round((high_risk / total * 100), 1),
        'period': period,
        'total_claims': total
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def claims_activity_chart(request):
    """
    Get claims activity data for dashboard charts
    
    GET /api/fraud-detection/activity/?period=12months
    
    Query Parameters:
    - period: Time period (7days, 30days, 12months, 1year)
    
    Response:
    [
        {"label": "Jan", "count": 45},
        {"label": "Feb", "count": 52},
        ...
    ]
    """
    
    period = request.query_params.get('period', '12months')
    today = timezone.now().date()
    
    if period == '7days':
        # Last 7 days
        data = []
        days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        for i in range(7):
            date = today - timedelta(days=6-i)
            count = Claim.objects.filter(submitted_date__date=date).count()
            data.append({'label': days[date.weekday()], 'count': count})
    
    elif period == '30days':
        # Last 4 weeks
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
        # Last 12 months
        data = []
        months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                  'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        
        for i in range(12):
            # Go back 11 months from today
            month_date = today.replace(day=1) - timedelta(days=1)
            for _ in range(10 - i):
                month_date = month_date.replace(day=1) - timedelta(days=1)
            
            count = Claim.objects.filter(
                submitted_date__year=month_date.year,
                submitted_date__month=month_date.month
            ).count()
            
            data.append({
                'label': months[month_date.month - 1], 
                'count': count
            })
    
    else:  # '1year' - quarters
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