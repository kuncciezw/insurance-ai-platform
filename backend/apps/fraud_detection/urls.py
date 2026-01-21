"""
Fraud Detection App URLs
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PolicyholderViewSet, VehicleViewSet, PolicyViewSet, ClaimViewSet,  fraud_statistics_chart, claims_activity_chart
from . import ml_views  # Import ML views

router = DefaultRouter()
router.register(r'policyholders', PolicyholderViewSet, basename='policyholder')
router.register(r'vehicles', VehicleViewSet, basename='vehicle')
router.register(r'policies', PolicyViewSet, basename='policy')
router.register(r'claims', ClaimViewSet, basename='claim')

# ML-powered fraud detection endpoints
ml_patterns = [
    path('analyze-claim/', ml_views.analyze_claim_fraud, name='analyze-claim'),
    path('batch-analyze/', ml_views.batch_analyze_claims, name='batch-analyze'),
    path('high-risk-claims/', ml_views.get_high_risk_claims, name='high-risk-claims'),
    path('statistics/', ml_views.fraud_statistics, name='fraud-statistics'),
]

urlpatterns = [
    path('', include(router.urls)),
    path('fraud/', include(ml_patterns)),  # ML fraud detection endpoints
    # Chart data endpoints
    path('stats/', fraud_statistics_chart, name='fraud_statistics_chart'),
    path('activity/', claims_activity_chart, name='claims_activity_chart'),
]