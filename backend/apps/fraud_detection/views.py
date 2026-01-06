"""
API ViewSets for Fraud Detection Application
"""

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
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
    filterset_fields = ['gender', 'marital_status', 'occupation', 'is_active', 'state', 'city']
    search_fields = ['first_name', 'last_name', 'email', 'policy_holder_id', 'phone_number']
    ordering_fields = ['created_at', 'last_name', 'credit_score', 'annual_income']
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
            Q(claims__is_fraudulent=True)
        ).distinct()
        
        serializer = self.get_serializer(high_risk_holders, many=True)
        return Response(serializer.data)


class VehicleViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Vehicles
    """
    queryset = Vehicle.objects.select_related('policyholder').all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['vehicle_type', 'fuel_type', 'year', 'make', 'has_anti_theft', 'is_modified']
    search_fields = ['vehicle_id', 'vin', 'registration_number', 'make', 'model']
    ordering_fields = ['created_at', 'year', 'market_value', 'odometer_reading']
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
    filterset_fields = ['status', 'policy_type', 'coverage_level']
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
            premium_amount=policy.premium_amount,
            coverage_amount=policy.coverage_amount,
            deductible=policy.deductible,
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
    filterset_fields = [
        'claim_status', 'claim_type', 'severity', 'is_fraudulent',
        'police_report_filed', 'third_party_involved'
    ]
    search_fields = [
        'claim_number', 'incident_description', 
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