"""
system_settings/views.py

Exposes a single endpoint for reading and updating GlobalPricingSettings.

GET  /api/system-settings/pricing/   — any authenticated user
PUT  /api/system-settings/pricing/   — SUPER_ADMIN or ADMIN only
PATCH /api/system-settings/pricing/  — SUPER_ADMIN or ADMIN only
"""

from __future__ import annotations

from typing import Any

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from .models import GlobalPricingSettings
from .serializers import GlobalPricingSettingsSerializer


# ── Helper ────────────────────────────────────────────────────────────────────
# Defined here so this app has no import dependency on apps.dashboard.

def _get_profile(user: Any):
    """Return the UserProfile attached to *user*, or None."""
    return getattr(user, 'profile', None)


# ── View ──────────────────────────────────────────────────────────────────────

@api_view(['GET', 'PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def global_pricing_settings(request: Request) -> Response:
    """
    Retrieve or update global pricing and threshold settings.

    * GET   — any authenticated user can read the current settings.
    * PUT   — full replacement; SUPER_ADMIN or ADMIN only.
    * PATCH — partial update; SUPER_ADMIN or ADMIN only.
    """
    settings = GlobalPricingSettings.get_solo()

    # ── Read ─────────────────────────────────────────────────────────────
    if request.method == 'GET':
        serializer = GlobalPricingSettingsSerializer(settings)
        return Response(serializer.data)

    # ── Write (PUT / PATCH) ──────────────────────────────────────────────
    requester_profile = _get_profile(request.user)

    if requester_profile is None or requester_profile.role not in ('SUPER_ADMIN', 'ADMIN'):
        return Response(
            {'error': 'You do not have permission to update pricing settings.'},
            status=status.HTTP_403_FORBIDDEN,
        )

    try:
        serializer = GlobalPricingSettingsSerializer(
            settings,
            data=request.data,
            partial=(request.method == 'PATCH'),
        )
        if serializer.is_valid():
            serializer.save()
            return Response({
                'message': 'Pricing settings updated successfully.',
                'data': serializer.data,
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    except Exception as exc:
        return Response(
            {'error': str(exc)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )