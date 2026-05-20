# In apps/dashboard/urls.py
from django.urls import path, include, re_path
from rest_framework.routers import SimpleRouter
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    register_user,
    login_user,
    logout_user,
    dashboard_statistics,
    user_profile,
    claims_activity,
    get_company_profile,
    get_roles_permissions,
    update_role_permissions,
    reset_role_permissions,
    get_permission_audit_log,
    bulk_update_permissions,
    UserViewSet
)

router = SimpleRouter()
router.register(r'users', UserViewSet, basename='user')

app_name = 'dashboard'

dashboard_patterns = [
    # Authentication endpoints
    path('auth/register/', register_user, name='register'),
    path('auth/login/', login_user, name='login'),
    path('auth/logout/', logout_user, name='logout'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/profile/', user_profile, name='user_profile'),
    
    # Dashboard endpoints
    path('statistics/', dashboard_statistics, name='dashboard_statistics'),
    path('activity/', claims_activity, name='claims_activity'),
    
    # Company Profile endpoint
    path('company-profile/', get_company_profile, name='get_company_profile'),
    
    # Roles & Permissions endpoints
    re_path(r'^roles/permissions/audit/?$', get_permission_audit_log, name='permission_audit_log'),
    re_path(r'^roles/permissions/bulk/?$', bulk_update_permissions, name='bulk_update_permissions'),
    re_path(r'^roles/permissions/?$', get_roles_permissions, name='roles_permissions'),
    re_path(r'^roles/(?P<role_id>[^/]+)/permissions/reset/?$', reset_role_permissions, name='reset_role_permissions'),
    re_path(r'^roles/(?P<role_id>[^/]+)/permissions/?$', update_role_permissions, name='update_role_permissions'),
]

urlpatterns = router.urls + dashboard_patterns