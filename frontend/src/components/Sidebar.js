import { useState, useEffect } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { api } from '../services/api';
import {
  LayoutDashboard,
  Users,
  Car,
  FileText,
  AlertTriangle,
  Calculator,
  ClipboardList,
  LogOut,
  DollarSign,
  Settings,
  Shield,
} from 'lucide-react';

export default function Sidebar({ activePath }) {
  const navigate = useNavigate();
  const location = useLocation();
  const { user, logout, hasPermission, hasRole } = useAuth();
  
  const [companyProfile, setCompanyProfile] = useState(null);

  useEffect(() => {
    fetchCompanyProfile();
  }, []);

  const fetchCompanyProfile = async () => {
    try {
      const data = await api.getCompanyProfile();
      setCompanyProfile(data);
    } catch (err) {
      console.error('Failed to load company profile:', err);
      setCompanyProfile({
        company_name: 'Insurance AI',
        company_tagline: 'Admin Portal',
        primary_color: '#FF6B4A',
        secondary_color: '#2C3E50',
      });
    }
  };

  const handleLogout = async () => {
    try {
      await logout();
      navigate('/login');
    } catch (err) {
      console.error('Logout failed:', err);
    }
  };

  // Define menu items with CORRECT permission requirements
  const allMenuItems = [
    { 
      name: 'Dashboard', 
      icon: LayoutDashboard, 
      path: '/dashboard',
      // No permission needed - everyone can see dashboard
    },
    { 
      name: 'Policyholders', 
      icon: Users, 
      path: '/policyholders',
      permission: 'can_view_policyholders'
    },
    { 
      name: 'Vehicles', 
      icon: Car, 
      path: '/vehicles',
      permission: 'can_view_vehicles'
    },
    { 
      name: 'Policies', 
      icon: FileText, 
      path: '/policies',
      permission: 'can_view_policies'
    },
    { 
      name: 'Claims', 
      icon: ClipboardList, 
      path: '/claims',
      permission: 'can_view_claims'
    },
    { 
      name: 'Fraud Detection', 
      icon: AlertTriangle, 
      path: '/fraud-detection',
      permission: 'can_view_fraud_detection'
    },
    { 
      name: 'Premium Calculator', 
      icon: Calculator, 
      path: '/premium-calculator',
      permission: 'can_calculate_premium'
    },
    { 
      name: 'Claims Estimator', 
      icon: DollarSign, 
      path: '/claims-estimator',
      permission: 'can_estimate_claims'
    },
    { 
      name: 'System Settings', 
      icon: Settings, 
      path: '/settings',
      // Only admins can access settings (includes user management)
      permission: 'can_manage_users'
    },
  ];

  // Filter menu items based on user permissions and roles
  const menuItems = allMenuItems.filter(item => {
    // Items with no permission requirement are visible to all
    if (!item.permission && !item.roles) {
      return true;
    }

    // Check role-based access
    if (item.roles) {
      return hasRole(item.roles);
    }

    // Check permission-based access
    if (item.permission) {
      return hasPermission(item.permission);
    }

    return false;
  });

  const currentPath = activePath || location.pathname;

  const primaryColor = companyProfile?.primary_color || '#FF6B4A';
  const secondaryColor = companyProfile?.secondary_color || '#2C3E50';

  return (
    <div className="w-64 shadow-lg" style={{ backgroundColor: secondaryColor }}>
      <div className="p-6">
        <h1 className="text-xl font-bold text-white">
          {companyProfile?.company_name || 'Insurance AI'}
        </h1>
        <p className="text-sm mt-1" style={{ color: '#BDC3C7' }}>
          {companyProfile?.company_tagline || 'Admin Portal'}
        </p>
      </div>

      <nav className="mt-6">
        {menuItems.map((item) => {
          const Icon = item.icon;
          const isActive = currentPath === item.path;
          return (
            <Link
              key={item.path}
              to={item.path}
              className="flex items-center px-6 py-3 transition-colors"
              style={{
                backgroundColor: isActive ? primaryColor : 'transparent',
                color: isActive ? 'white' : '#BDC3C7',
              }}
              onMouseEnter={(e) => {
                if (!isActive) {
                  e.currentTarget.style.backgroundColor = '#34495E';
                  e.currentTarget.style.color = 'white';
                }
              }}
              onMouseLeave={(e) => {
                if (!isActive) {
                  e.currentTarget.style.backgroundColor = 'transparent';
                  e.currentTarget.style.color = '#BDC3C7';
                }
              }}
            >
              <Icon className="w-5 h-5 mr-3" />
              {item.name}
            </Link>
          );
        })}
      </nav>

      <div className="absolute bottom-0 w-64 p-6 border-t" style={{ borderColor: '#34495E' }}>
        <div className="flex items-center mb-4">
          <div
            className="w-10 h-10 rounded-full flex items-center justify-center text-white font-bold"
            style={{ backgroundColor: primaryColor }}
          >
            {user?.first_name?.[0] || user?.username?.[0] || 'U'}
          </div>
          <div className="ml-3">
            <p className="text-white text-sm font-medium">
              {user?.first_name && user?.last_name
                ? `${user.first_name} ${user.last_name}`
                : user?.username || 'User'}
            </p>
            <p className="text-xs" style={{ color: '#BDC3C7' }}>
              {user?.role_display || user?.role || 'User'}
            </p>
          </div>
        </div>
        <button
          onClick={handleLogout}
          className="w-full flex items-center justify-center px-4 py-2 rounded-lg transition-colors"
          style={{ backgroundColor: '#34495E', color: 'white' }}
          onMouseEnter={(e) => {
            e.target.style.backgroundColor = primaryColor;
          }}
          onMouseLeave={(e) => {
            e.target.style.backgroundColor = '#34495E';
          }}
        >
          <LogOut className="w-4 h-4 mr-2" />
          Logout
        </button>
      </div>
    </div>
  );
}