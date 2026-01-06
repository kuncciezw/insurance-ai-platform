"""
URL routing for Dashboard and Authentication
"""

from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    register_user,
    login_user,
    logout_user,
    dashboard_statistics,
    user_profile
)

urlpatterns = [
    # Authentication endpoints
    path('auth/register/', register_user, name='register'),
    path('auth/login/', login_user, name='login'),
    path('auth/logout/', logout_user, name='logout'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/profile/', user_profile, name='user_profile'),
    
    # Dashboard endpoints
    path('statistics/', dashboard_statistics, name='dashboard_statistics'),
]