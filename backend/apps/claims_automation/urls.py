"""
URL Configuration for Claims Automation API
"""
from django.urls import path
from rest_framework.routers import SimpleRouter
from . import views

router = SimpleRouter()
router.register(r'estimates', views.ClaimEstimateViewSet, basename='estimate')
router.register(r'processing-logs', views.ClaimProcessingLogViewSet, basename='processing-log')

app_name = 'claims_automation'

claims_patterns = [
    path('estimate-cost/', views.estimate_claim_cost, name='estimate-cost'),
    path('estimate-cost-direct/', views.estimate_claim_cost_direct, name='estimate-cost-direct'),
    path('batch-triage/', views.batch_triage_claims, name='batch-triage'),
    path('recommendations/<uuid:claim_id>/', views.processing_recommendations, name='recommendations'),
    path('claims/<uuid:claim_id>/auto-process/', views.auto_process_claim, name='auto-process'),
    path('statistics/', views.claims_statistics, name='statistics'),
]

urlpatterns = router.urls + claims_patterns