import { useState, useEffect } from 'react';
import { X, Loader2 } from 'lucide-react';

export default function UserManagementModal({ 
  show, 
  onClose, 
  onSave, 
  editingUser, 
  loading,
  companyProfile 
}) {
  const [formData, setFormData] = useState({
    first_name: '',
    last_name: '',
    email: '',
    username: '',
    password: '',
    password_confirm: '',
    role: 'VIEWER',
    is_active: true,
  });

  const [errors, setErrors] = useState({});

  // Update form data when editingUser changes or modal opens
  useEffect(() => {
    if (editingUser) {
      setFormData({
        first_name: editingUser.first_name || '',
        last_name: editingUser.last_name || '',
        email: editingUser.email || '',
        username: editingUser.username || '',
        password: '',
        password_confirm: '',
        role: editingUser.role || 'VIEWER',
        is_active: editingUser.is_active ?? true,
      });
    } else {
      setFormData({
        first_name: '',
        last_name: '',
        email: '',
        username: '',
        password: '',
        password_confirm: '',
        role: 'VIEWER',
        is_active: true,
      });
    }
    setErrors({});
  }, [editingUser, show]);

  const availableRoles = [
    { value: 'SUPER_ADMIN', label: 'Super Admin' },
    { value: 'ADMIN', label: 'Admin' },
    { value: 'CLAIMS_ADJUSTER', label: 'Claims Adjuster' },
    { value: 'UNDERWRITER', label: 'Underwriter' },
    { value: 'FRAUD_INVESTIGATOR', label: 'Fraud Investigator' },
    { value: 'VIEWER', label: 'Viewer' },
  ];

  const validateForm = () => {
    const newErrors = {};

    if (!formData.first_name.trim()) {
      newErrors.first_name = 'First name is required';
    }
    if (!formData.last_name.trim()) {
      newErrors.last_name = 'Last name is required';
    }
    if (!formData.email.trim()) {
      newErrors.email = 'Email is required';
    }
    if (!formData.username.trim()) {
      newErrors.username = 'Username is required';
    }

    // Password validation for new users
    if (!editingUser) {
      if (!formData.password) {
        newErrors.password = 'Password is required';
      } else if (formData.password.length < 8) {
        newErrors.password = 'Password must be at least 8 characters';
      }
      if (!formData.password_confirm) {
        newErrors.password_confirm = 'Please confirm password';
      }
    }

    // Password match validation
    if (formData.password || formData.password_confirm) {
      if (formData.password !== formData.password_confirm) {
        newErrors.password_confirm = 'Passwords do not match';
      }
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async () => {
    if (!validateForm()) return;

    // Prepare data for submission
    const submitData = {
      first_name: formData.first_name,
      last_name: formData.last_name,
      email: formData.email,
      username: formData.username,
      role: formData.role,
      is_active: formData.is_active,
    };

    // Only include password fields if they're filled
    if (formData.password) {
      submitData.password = formData.password;
      submitData.password_confirm = formData.password_confirm;
    }

    await onSave(submitData);
  };

  if (!show) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4" style={{ backgroundColor: 'rgba(0,0,0,0.5)' }}>
      <div className="bg-white rounded-xl shadow-2xl max-w-md w-full max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between p-6 border-b sticky top-0 bg-white" style={{ borderColor: '#E5E7EB' }}>
          <h3 className="text-xl font-bold" style={{ color: companyProfile.secondary_color }}>
            {editingUser ? 'Edit User' : 'Add New User'}
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
          <div className="space-y-4">
            {/* Name Fields */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium mb-2" style={{ color: companyProfile.secondary_color }}>
                  First Name *
                </label>
                <input
                  type="text"
                  value={formData.first_name}
                  onChange={(e) => setFormData({ ...formData, first_name: e.target.value })}
                  className="w-full px-4 py-2 rounded-lg border focus:outline-none focus:ring-2"
                  style={{ 
                    borderColor: errors.first_name ? '#EF4444' : '#E0E0E0',
                    focusRingColor: companyProfile.primary_color 
                  }}
                />
                {errors.first_name && (
                  <p className="text-sm mt-1" style={{ color: '#EF4444' }}>{errors.first_name}</p>
                )}
              </div>
              <div>
                <label className="block text-sm font-medium mb-2" style={{ color: companyProfile.secondary_color }}>
                  Last Name *
                </label>
                <input
                  type="text"
                  value={formData.last_name}
                  onChange={(e) => setFormData({ ...formData, last_name: e.target.value })}
                  className="w-full px-4 py-2 rounded-lg border focus:outline-none focus:ring-2"
                  style={{ 
                    borderColor: errors.last_name ? '#EF4444' : '#E0E0E0' 
                  }}
                />
                {errors.last_name && (
                  <p className="text-sm mt-1" style={{ color: '#EF4444' }}>{errors.last_name}</p>
                )}
              </div>
            </div>

            {/* Email */}
            <div>
              <label className="block text-sm font-medium mb-2" style={{ color: companyProfile.secondary_color }}>
                Email *
              </label>
              <input
                type="email"
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                className="w-full px-4 py-2 rounded-lg border focus:outline-none focus:ring-2"
                style={{ 
                  borderColor: errors.email ? '#EF4444' : '#E0E0E0' 
                }}
              />
              {errors.email && (
                <p className="text-sm mt-1" style={{ color: '#EF4444' }}>{errors.email}</p>
              )}
            </div>

            {/* Username */}
            <div>
              <label className="block text-sm font-medium mb-2" style={{ color: companyProfile.secondary_color }}>
                Username *
              </label>
              <input
                type="text"
                value={formData.username}
                onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                className="w-full px-4 py-2 rounded-lg border focus:outline-none focus:ring-2"
                style={{ 
                  borderColor: errors.username ? '#EF4444' : '#E0E0E0' 
                }}
                disabled={!!editingUser}
              />
              {errors.username && (
                <p className="text-sm mt-1" style={{ color: '#EF4444' }}>{errors.username}</p>
              )}
            </div>

            {/* Password */}
            <div>
              <label className="block text-sm font-medium mb-2" style={{ color: companyProfile.secondary_color }}>
                Password {!editingUser && '*'}
              </label>
              <input
                type="password"
                value={formData.password}
                onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                className="w-full px-4 py-2 rounded-lg border focus:outline-none focus:ring-2"
                style={{ 
                  borderColor: errors.password ? '#EF4444' : '#E0E0E0' 
                }}
                placeholder={editingUser ? 'Leave blank to keep current password' : ''}
              />
              {errors.password && (
                <p className="text-sm mt-1" style={{ color: '#EF4444' }}>{errors.password}</p>
              )}
            </div>

            {/* Confirm Password */}
            <div>
              <label className="block text-sm font-medium mb-2" style={{ color: companyProfile.secondary_color }}>
                Confirm Password {!editingUser && '*'}
              </label>
              <input
                type="password"
                value={formData.password_confirm}
                onChange={(e) => setFormData({ ...formData, password_confirm: e.target.value })}
                className="w-full px-4 py-2 rounded-lg border focus:outline-none focus:ring-2"
                style={{ 
                  borderColor: errors.password_confirm ? '#EF4444' : '#E0E0E0' 
                }}
                placeholder={editingUser ? 'Leave blank to keep current password' : ''}
              />
              {errors.password_confirm && (
                <p className="text-sm mt-1" style={{ color: '#EF4444' }}>{errors.password_confirm}</p>
              )}
            </div>

            {/* Role */}
            <div>
              <label className="block text-sm font-medium mb-2" style={{ color: companyProfile.secondary_color }}>
                Role *
              </label>
              <select
                value={formData.role}
                onChange={(e) => setFormData({ ...formData, role: e.target.value })}
                className="w-full px-4 py-2 rounded-lg border focus:outline-none focus:ring-2"
                style={{ borderColor: '#E0E0E0' }}
              >
                {availableRoles.map((role) => (
                  <option key={role.value} value={role.value}>
                    {role.label}
                  </option>
                ))}
              </select>
            </div>

            {/* Active Status */}
            <div className="flex items-center">
              <input
                type="checkbox"
                id="is_active"
                checked={formData.is_active}
                onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                className="w-4 h-4 mr-2"
                style={{ accentColor: companyProfile.primary_color }}
              />
              <label htmlFor="is_active" className="text-sm font-medium" style={{ color: companyProfile.secondary_color }}>
                Active User
              </label>
            </div>
          </div>

          {/* Actions */}
          <div className="flex justify-end gap-3 mt-6">
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
              onClick={handleSubmit}
              disabled={loading}
              className="px-6 py-2 rounded-lg text-white font-medium transition-colors disabled:opacity-50 flex items-center"
              style={{ backgroundColor: companyProfile.primary_color }}
              onMouseEnter={(e) => !loading && (e.target.style.opacity = '0.9')}
              onMouseLeave={(e) => !loading && (e.target.style.opacity = '1')}
            >
              {loading && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
              {loading ? 'Saving...' : editingUser ? 'Update User' : 'Create User'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}