import { useState, useEffect } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { api } from '../services/api';
import {
  LayoutDashboard,
  UserPlus,
  FileText,
  AlertTriangle,
  ClipboardCheck,
  LogOut,
  Settings,
  DollarSign,
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
      setCompanyProfile({
        company_name: 'Zimbabwe Insurance AI',
        company_tagline: 'Intelligent Operations',
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

  const allMenuItems = [
    { 
      name: 'Dashboard', 
      icon: LayoutDashboard, 
      path: '/dashboard',
    },
    { 
      name: 'New Registration', 
      icon: UserPlus, 
      path: '/onboarding',
      permission: 'can_create_policyholders'
    },
    { 
      name: 'Policy Issuance', 
      icon: FileText, 
      path: '/policies',
      permission: 'can_view_policies'
    },
    { 
      name: 'Claims Management', 
      icon: ClipboardCheck, 
      path: '/claims',
      permission: 'can_view_claims'
    },
    { 
      name: 'Fraud Analytics', 
      icon: AlertTriangle, 
      path: '/fraud-detection',
      permission: 'can_view_fraud_detection'
    },
    { 
      name: 'Premium Calculator', 
      icon: DollarSign, 
      path: '/premium-calculator',
      roles: ['SUPER_ADMIN', 'ADMIN', 'UNDERWRITER']
    },
    { 
      name: 'System Settings', 
      icon: Settings, 
      path: '/settings',
      permission: 'can_manage_users'
    },
  ];

  const menuItems = allMenuItems.filter(item => {
    if (!item.permission && !item.roles) return true;
    if (item.roles) return hasRole(item.roles);
    if (item.permission) return hasPermission(item.permission);
    return false;
  });

  const currentPath = activePath || location.pathname;
  const primaryColor = companyProfile?.primary_color || '#FF6B4A';
  const secondaryColor = companyProfile?.secondary_color || '#2C3E50';

  return (
    <div className="w-64 min-h-screen shadow-lg flex flex-col shrink-0 overflow-y-auto" style={{ backgroundColor: secondaryColor }}>
      <div className="p-6">
        <h1 className="text-xl font-bold text-white uppercase tracking-wider">
          {companyProfile?.company_name || 'Insurance AI'}
        </h1>
        <div className="h-1 w-12 mt-1" style={{ backgroundColor: primaryColor }}></div>
        <p className="text-xs mt-2 font-medium" style={{ color: '#BDC3C7' }}>
          {companyProfile?.company_tagline || 'Admin Portal'}
        </p>
      </div>

      <nav className="mt-4 flex-grow">
        {menuItems.map((item) => {
          const Icon = item.icon;
          const isActive = currentPath === item.path;
          return (
            <Link
              key={item.path}
              to={item.path}
              className="flex items-center px-6 py-4 transition-all duration-200 border-l-4"
              style={{
                backgroundColor: isActive ? 'rgba(255, 255, 255, 0.05)' : 'transparent',
                color: isActive ? 'white' : '#BDC3C7',
                borderColor: isActive ? primaryColor : 'transparent'
              }}
            >
              <Icon className="w-5 h-5 mr-4" />
              <span className="text-sm font-semibold">{item.name}</span>
            </Link>
          );
        })}
      </nav>

      <div className="p-6 border-t mt-auto" style={{ borderColor: 'rgba(255, 255, 255, 0.1)' }}>
        <div className="flex items-center mb-6">
          <div
            className="w-10 h-10 rounded-lg flex items-center justify-center text-white font-bold shadow-md shrink-0"
            style={{ backgroundColor: primaryColor }}
          >
            {user?.first_name?.[0] || user?.username?.[0] || 'U'}
          </div>
          <div className="ml-3 overflow-hidden">
            <p className="text-white text-sm font-bold truncate">
              {user?.first_name ? `${user.first_name} ${user.last_name}` : user?.username}
            </p>
            <p className="text-[10px] uppercase tracking-tighter" style={{ color: primaryColor }}>
              {user?.role_display || user?.role}
            </p>
          </div>
        </div>
        <button
          onClick={handleLogout}
          className="w-full flex items-center justify-center px-4 py-2.5 rounded-lg text-sm font-bold transition-all hover:opacity-90"
          style={{ backgroundColor: '#34495E', color: 'white' }}
        >
          <LogOut className="w-4 h-4 mr-2" />
          Logout
        </button>
      </div>
    </div>
  );
}