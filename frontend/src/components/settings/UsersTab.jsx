import { Plus, Search, Edit2, Trash2, CheckCircle, XCircle, Loader2 } from 'lucide-react';

export default function UsersTab({ 
  users,
  searchQuery,
  setSearchQuery,
  loading,
  companyProfile,
  currentUser,
  onAddUser,
  onEditUser,
  onDeleteUser
}) {
  const filteredUsers = users.filter(u =>
    (u.first_name + ' ' + u.last_name).toLowerCase().includes(searchQuery.toLowerCase()) ||
    u.email.toLowerCase().includes(searchQuery.toLowerCase()) ||
    u.username.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div>
      {/* Search and Add User */}
      <div className="flex items-center justify-between mb-6">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5" style={{ color: '#7F8C8D' }} />
          <input
            type="text"
            placeholder="Search users..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2 rounded-lg border focus:outline-none focus:ring-2"
            style={{ borderColor: '#E0E0E0' }}
          />
        </div>
        <button
          onClick={onAddUser}
          className="ml-4 px-4 py-2 rounded-lg text-white font-medium flex items-center transition-colors"
          style={{ backgroundColor: companyProfile.primary_color }}
          onMouseEnter={(e) => e.target.style.opacity = '0.9'}
          onMouseLeave={(e) => e.target.style.opacity = '1'}
        >
          <Plus className="w-5 h-5 mr-2" />
          Add User
        </button>
      </div>

      {/* Users Table */}
      {loading ? (
        <div className="text-center py-12">
          <Loader2 className="w-8 h-8 animate-spin mx-auto" style={{ color: companyProfile.primary_color }} />
          <p className="mt-4" style={{ color: '#7F8C8D' }}>Loading users...</p>
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr style={{ backgroundColor: '#F8F9FA' }}>
                <th className="px-4 py-3 text-left text-sm font-semibold" style={{ color: companyProfile.secondary_color }}>
                  Full Name
                </th>
                <th className="px-4 py-3 text-left text-sm font-semibold" style={{ color: companyProfile.secondary_color }}>
                  Email
                </th>
                <th className="px-4 py-3 text-left text-sm font-semibold" style={{ color: companyProfile.secondary_color }}>
                  Role
                </th>
                <th className="px-4 py-3 text-left text-sm font-semibold" style={{ color: companyProfile.secondary_color }}>
                  Status
                </th>
                <th className="px-4 py-3 text-left text-sm font-semibold" style={{ color: companyProfile.secondary_color }}>
                  Last Login
                </th>
                <th className="px-4 py-3 text-right text-sm font-semibold" style={{ color: companyProfile.secondary_color }}>
                  Actions
                </th>
              </tr>
            </thead>
            <tbody>
              {filteredUsers.map((u, index) => (
                <tr
                  key={u.id}
                  className="border-t"
                  style={{ borderColor: '#E5E7EB', backgroundColor: index % 2 === 0 ? 'white' : '#F8F9FA' }}
                >
                  <td className="px-4 py-3">
                    <div className="flex items-center">
                      <div
                        className="w-8 h-8 rounded-full flex items-center justify-center text-white font-bold text-sm mr-3"
                        style={{ backgroundColor: companyProfile.primary_color }}
                      >
                        {u.first_name?.[0] || u.username?.[0] || 'U'}
                      </div>
                      <span className="font-medium" style={{ color: companyProfile.secondary_color }}>
                        {u.first_name && u.last_name ? `${u.first_name} ${u.last_name}` : u.username}
                      </span>
                    </div>
                  </td>
                  <td className="px-4 py-3" style={{ color: '#7F8C8D' }}>
                    {u.email}
                  </td>
                  <td className="px-4 py-3">
                    <span
                      className="px-3 py-1 rounded-full text-sm font-medium"
                      style={{
                        backgroundColor: u.role === 'SUPER_ADMIN' ? '#EBF5FF' : '#F0F9FF',
                        color: u.role === 'SUPER_ADMIN' ? '#1E40AF' : '#0369A1',
                      }}
                    >
                      {u.role_display || u.role || 'Viewer'}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    {u.is_active ? (
                      <span className="flex items-center text-sm" style={{ color: '#10B981' }}>
                        <CheckCircle className="w-4 h-4 mr-1" />
                        Active
                      </span>
                    ) : (
                      <span className="flex items-center text-sm" style={{ color: '#EF4444' }}>
                        <XCircle className="w-4 h-4 mr-1" />
                        Inactive
                      </span>
                    )}
                  </td>
                  <td className="px-4 py-3" style={{ color: '#7F8C8D' }}>
                    {u.last_login ? new Date(u.last_login).toLocaleDateString() : 'Never'}
                  </td>
                  <td className="px-4 py-3 text-right">
                    <button
                      onClick={() => onEditUser(u)}
                      className="p-2 rounded-lg mr-2 transition-colors"
                      style={{ color: '#3B82F6' }}
                      onMouseEnter={(e) => e.target.style.backgroundColor = '#EBF5FF'}
                      onMouseLeave={(e) => e.target.style.backgroundColor = 'transparent'}
                    >
                      <Edit2 className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => onDeleteUser(u.id)}
                      className="p-2 rounded-lg transition-colors"
                      style={{ color: '#EF4444' }}
                      onMouseEnter={(e) => e.target.style.backgroundColor = '#FEE2E2'}
                      onMouseLeave={(e) => e.target.style.backgroundColor = 'transparent'}
                      disabled={u.id === currentUser.id}
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {filteredUsers.length === 0 && (
            <div className="text-center py-12" style={{ color: '#7F8C8D' }}>
              No users found
            </div>
          )}
        </div>
      )}
    </div>
  );
}