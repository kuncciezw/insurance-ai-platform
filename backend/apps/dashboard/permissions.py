"""
Custom DRF Permissions for RBAC
"""

from rest_framework import permissions


class IsSuperAdmin(permissions.BasePermission):
    """Only Super Admin can access"""
    
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            hasattr(request.user, 'profile') and
            request.user.profile.role == 'SUPER_ADMIN'
        )


class IsAdmin(permissions.BasePermission):
    """Super Admin or Admin can access"""
    
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            hasattr(request.user, 'profile') and
            request.user.profile.role in ['SUPER_ADMIN', 'ADMIN']
        )

class CanManageUsers(permissions.BasePermission):
    """Check if user can manage other users"""
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        if not hasattr(request.user, 'profile'):
            return False
        
        return request.user.profile.can_manage_users()


class RoleBasedPermission(permissions.BasePermission):
    """
    Dynamic permission class that checks role-based permissions
    Set required_roles on the view
    """
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        if not hasattr(request.user, 'profile'):
            return False
        
        # Check if view has required_roles attribute
        required_roles = getattr(view, 'required_roles', None)
        if required_roles is None:
            return True
        
        # Check if view has different roles for different methods
        method_roles = getattr(view, 'method_roles', {})
        if request.method in method_roles:
            required_roles = method_roles[request.method]
        
        return request.user.profile.role in required_roles