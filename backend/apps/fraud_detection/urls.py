"""
URL routing for Fraud Detection API
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    PolicyholderViewSet,
    VehicleViewSet,
    PolicyViewSet,
    ClaimViewSet
)

# Create router and register viewsets
router = DefaultRouter()
router.register(r'policyholders', PolicyholderViewSet, basename='policyholder')
router.register(r'vehicles', VehicleViewSet, basename='vehicle')
router.register(r'policies', PolicyViewSet, basename='policy')
router.register(r'claims', ClaimViewSet, basename='claim')

urlpatterns = [
    path('', include(router.urls)),
]