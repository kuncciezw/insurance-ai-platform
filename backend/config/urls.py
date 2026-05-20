"""
URL Configuration for Insurance AI Platform
Django 6.0
"""
import django.urls.converters as converters
if not hasattr(converters, '_drf_initialized'):
    converters._drf_initialized = True
    
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

# API Documentation Schema
schema_view = get_schema_view(
    openapi.Info(
        title="Insurance AI Platform API",
        default_version='v1',
        description="API documentation for Intelligent Insurance Operations Platform",
        terms_of_service="https://www.example.com/terms/",
        contact=openapi.Contact(email="contact@insurance-ai.com"),
        license=openapi.License(name="MIT License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    # Homepage - redirect to API docs
    path('', RedirectView.as_view(url='/api/docs/', permanent=False), name='home'),
    
    # Admin interface
    path('admin/', admin.site.urls),
    
    # API Documentation
    path('api/docs/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('api/redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    
    # Application API endpoints
    path('api/fraud-detection/', include('apps.fraud_detection.urls')),
    path('api/dynamic-pricing/', include('apps.dynamic_pricing.urls')),
    path('api/claims-automation/', include('apps.claims_automation.urls')),
    path('api/dashboard/', include('apps.dashboard.urls')),
    
    # System Settings
    path('api/system-settings/', include('system_settings.urls')), 
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)