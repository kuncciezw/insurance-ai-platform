import { useState, useEffect } from 'react';
import { X, Loader2, CheckCircle, Mail, User, Calendar } from 'lucide-react';

export default function UserApprovalModal({ 
  show, 
  onClose, 
  onApprove, 
  user, 
  loading,
  companyProfile 
}) {
  const [selectedRole, setSelectedRole] = useState('VIEWER');

  useEffect(() => {
    if (user) {
      setSelectedRole('VIEWER'); // Default to viewer
    }
  }, [user, show]);

  const availableRoles = [
    { value: 'SUPER_ADMIN', label: 'Super Admin', description: 'Full system access' },
    { value: 'ADMIN', label: 'Admin', description: 'Manage users and settings' },
    { value: 'CLAIMS_ADJUSTER', label: 'Claims Adjuster', description: 'Process and approve claims' },
    { value: 'UNDERWRITER', label: 'Underwriter', description: 'Manage policies and premiums' },
    { value: 'FRAUD_INVESTIGATOR', label: 'Fraud Investigator', description: 'Investigate fraud cases' },
    { value: 'VIEWER', label: 'Viewer', description: 'Read-only access' },
  ];

  const handleApprove = async () => {
    await onApprove(user.id, selectedRole);
  };

  if (!show || !user) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4" style={{ backgroundColor: 'rgba(0,0,0,0.5)' }}>
      <div className="bg-white rounded-xl shadow-2xl max-w-lg w-full">
        <div className="flex items-center justify-between p-6 border-b" style={{ borderColor: '#E5E7EB' }}>
          <h3 className="text-xl font-bold" style={{ color: companyProfile.secondary_color }}>
            Approve User Registration
          </h3>
          <button
            onClick={onClose}
            className="p-2 rounded-lg hover:bg-gray-100"
            disabled={loading}
          >
            <X className="w-6 h-6" style={{ color: '#7F8C8D' }} />
          </button>
        </div>

        <div className="p-6">
          {/* User Details */}
          <div className="mb-6 p-4 rounded-lg" style={{ backgroundColor: '#F8F9FA' }}>
            <h4 className="text-sm font-semibold mb-3" style={{ color: companyProfile.secondary_color }}>
              Applicant Information
            </h4>
            
            <div className="space-y-2">
              <div className="flex items-center">
                <User className="w-4 h-4 mr-2" style={{ color: '#7F8C8D' }} />
                <span className="text-sm font-medium" style={{ color: '#2C3E50' }}>
                  {user.first_name && user.last_name 
                    ? `${user.first_name} ${user.last_name}` 
                    : 'Name not provided'}
                </span>
              </div>
              
              <div className="flex items-center">
                <Mail className="w-4 h-4 mr-2" style={{ color: '#7F8C8D' }} />
                <span className="text-sm" style={{ color: '#7F8C8D' }}>{user.email}</span>
              </div>
              
              <div className="flex items-center">
                <User className="w-4 h-4 mr-2" style={{ color: '#7F8C8D' }} />
                <span className="text-sm font-mono" style={{ color: '#7F8C8D' }}>
                  @{user.username}
                </span>
              </div>
              
              <div className="flex items-center">
                <Calendar className="w-4 h-4 mr-2" style={{ color: '#7F8C8D' }} />
                <span className="text-sm" style={{ color: '#7F8C8D' }}>
                  Applied: {new Date(user.date_joined).toLocaleDateString('en-US', {
                    month: 'long',
                    day: 'numeric',
                    year: 'numeric',
                    hour: '2-digit',
                    minute: '2-digit'
                  })}
                </span>
              </div>
            </div>
          </div>

          {/* Role Selection */}
          <div className="mb-6">
            <label className="block text-sm font-medium mb-3" style={{ color: companyProfile.secondary_color }}>
              Assign Role
            </label>
            <div className="space-y-2">
              {availableRoles.map((role) => (
                <label
                  key={role.value}
                  className="flex items-start p-3 rounded-lg border-2 cursor-pointer transition-all"
                  style={{
                    borderColor: selectedRole === role.value ? companyProfile.primary_color : '#E5E7EB',
                    backgroundColor: selectedRole === role.value ? '#FFF5F2' : 'white',
                  }}
                >
                  <input
                    type="radio"
                    name="role"
                    value={role.value}
                    checked={selectedRole === role.value}
                    onChange={(e) => setSelectedRole(e.target.value)}
                    className="mt-1"
                    style={{ accentColor: companyProfile.primary_color }}
                  />
                  <div className="ml-3 flex-1">
                    <div className="font-medium" style={{ color: companyProfile.secondary_color }}>
                      {role.label}
                    </div>
                    <div className="text-xs mt-0.5" style={{ color: '#7F8C8D' }}>
                      {role.description}
                    </div>
                  </div>
                </label>
              ))}
            </div>
          </div>

          {/* Warning for elevated roles */}
          {(selectedRole === 'SUPER_ADMIN' || selectedRole === 'ADMIN') && (
            <div className="mb-6 p-3 rounded-lg flex items-start" style={{ backgroundColor: '#FEF3C7' }}>
              <CheckCircle className="w-5 h-5 mr-2 mt-0.5" style={{ color: '#92400E' }} />
              <div className="text-sm" style={{ color: '#92400E' }}>
                <span className="font-medium">Elevated permissions:</span> This role will have extensive system access.
              </div>
            </div>
          )}

          {/* Actions */}
          <div className="flex justify-end gap-3">
            <button
              type="button"
              onClick={onClose}
              disabled={loading}
              className="px-6 py-2 rounded-lg font-medium transition-colors"
              style={{ backgroundColor: '#F8F9FA', color: '#7F8C8D' }}
            >
              Cancel
            </button>
            <button
              type="button"
              onClick={handleApprove}
              disabled={loading}
              className="px-6 py-2 rounded-lg text-white font-medium transition-colors disabled:opacity-50 flex items-center"
              style={{ backgroundColor: '#10B981' }}
              onMouseEnter={(e) => !loading && (e.target.style.backgroundColor = '#059669')}
              onMouseLeave={(e) => !loading && (e.target.style.backgroundColor = '#10B981')}
            >
              {loading && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
              {loading ? 'Approving...' : 'Approve & Activate'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}