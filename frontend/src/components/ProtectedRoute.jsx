import { Navigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

export default function ProtectedRoute({ 
  children, 
  permission, 
  roles, 
  requireAll = false 
}) {
  const { user, hasPermission, hasRole, isLoading } = useAuth();

  // Show loading state while checking auth
  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <div 
            className="w-16 h-16 border-4 border-t-transparent rounded-full animate-spin mx-auto mb-4"
            style={{ borderColor: '#FF6B4A', borderTopColor: 'transparent' }}
          ></div>
          <p style={{ color: '#7F8C8D' }}>Loading...</p>
        </div>
      </div>
    );
  }

  // Redirect to login if not authenticated
  if (!user) {
    return <Navigate to="/login" replace />;
  }

  // Check permission if provided
  if (permission && !hasPermission(permission)) {
    return <Navigate to="/dashboard" replace />;
  }

  // Check roles if provided
  if (roles && !hasRole(roles)) {
    return <Navigate to="/dashboard" replace />;
  }

  // If multiple permissions/roles provided and requireAll is true
  if (requireAll && permission && roles) {
    if (!hasPermission(permission) || !hasRole(roles)) {
      return <Navigate to="/dashboard" replace />;
    }
  }

  // User has required permissions
  return children;
}