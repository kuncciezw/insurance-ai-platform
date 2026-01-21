import { useState } from 'react';
import { api } from '../../services/api';

export default function RolesTab({ 
  roles,
  permissions,
  permissionsList,
  companyProfile,
  onPermissionToggle
}) {
  const [loading, setLoading] = useState({});
  
  const availableRoles = [
    { value: 'SUPER_ADMIN', label: 'Super Admin' },
    { value: 'ADMIN', label: 'Admin' },
    { value: 'CLAIMS_ADJUSTER', label: 'Claims Adjuster' },
    { value: 'UNDERWRITER', label: 'Underwriter' },
    { value: 'FRAUD_INVESTIGATOR', label: 'Fraud Investigator' },
    { value: 'VIEWER', label: 'Viewer' },
  ];

  const handleToggle = async (roleId, permissionId, currentValue) => {
    if (roleId === 'SUPER_ADMIN') return;
    
    const loadingKey = `${roleId}-${permissionId}`;
    setLoading(prev => ({ ...prev, [loadingKey]: true }));
    
    try {
      // Use the API service instead of direct fetch
      await api.updateRolePermission(roleId, permissionId, !currentValue);

      // Refresh permissions after successful update
      if (onPermissionToggle) {
        await onPermissionToggle();
      }
    } catch (err) {
      console.error('Error updating permission:', err);
      alert(`Failed to update permission: ${err.message}`);
    } finally {
      setLoading(prev => ({ ...prev, [loadingKey]: false }));
    }
  };

  return (
    <div>
      <h3 className="text-xl font-bold mb-6" style={{ color: companyProfile.secondary_color }}>
        Permissions Matrix
      </h3>
      
      <div className="overflow-x-auto">
        <table className="w-full border" style={{ borderColor: '#E5E7EB' }}>
          <thead>
            <tr style={{ backgroundColor: '#F8F9FA' }}>
              <th className="px-4 py-3 text-left text-sm font-semibold border-r" style={{ color: companyProfile.secondary_color, borderColor: '#E5E7EB' }}>
                Role / Permission
              </th>
              {permissionsList.map((perm) => (
                <th
                  key={perm.id}
                  className="px-4 py-3 text-center text-sm font-semibold border-r"
                  style={{ color: companyProfile.secondary_color, borderColor: '#E5E7EB', minWidth: '120px' }}
                >
                  {perm.label}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {availableRoles.map((role, roleIndex) => {
              const rolePerms = permissions[role.value] || {};
              
              return (
                <tr
                  key={role.value}
                  className="border-t"
                  style={{
                    borderColor: '#E5E7EB',
                    backgroundColor: roleIndex % 2 === 0 ? 'white' : '#F8F9FA',
                  }}
                >
                  <td className="px-4 py-3 font-medium border-r" style={{ color: companyProfile.secondary_color, borderColor: '#E5E7EB' }}>
                    {role.label}
                  </td>
                  {permissionsList.map((perm) => {
                    const hasPermission = role.value === 'SUPER_ADMIN' ? true : (rolePerms[perm.id] ?? false);
                    const loadingKey = `${role.value}-${perm.id}`;
                    const isLoading = loading[loadingKey];
                    
                    return (
                      <td
                        key={perm.id}
                        className="px-4 py-3 text-center border-r"
                        style={{ borderColor: '#E5E7EB' }}
                      >
                        <input
                          type="checkbox"
                          checked={hasPermission}
                          onChange={() => handleToggle(role.value, perm.id, hasPermission)}
                          disabled={role.value === 'SUPER_ADMIN' || isLoading}
                          className="w-5 h-5 cursor-pointer"
                          style={{
                            accentColor: companyProfile.primary_color,
                            opacity: (role.value === 'SUPER_ADMIN' || isLoading) ? 0.5 : 1,
                          }}
                        />
                      </td>
                    );
                  })}
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}