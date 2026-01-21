import { Search, CheckCircle, XCircle, Loader2, UserCheck } from 'lucide-react';
import { useConfirm } from '../notifications/useConfirm';

export default function PendingUsersTab({ 
  pendingUsers,
  searchQuery,
  setSearchQuery,
  loading,
  companyProfile,
  onApprove,
  onReject
}) {
  const { showConfirm, ConfirmDialog } = useConfirm();

  const filteredUsers = pendingUsers.filter(u =>
    (u.first_name + ' ' + u.last_name).toLowerCase().includes(searchQuery.toLowerCase()) ||
    u.email.toLowerCase().includes(searchQuery.toLowerCase()) ||
    u.username.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const handleApprove = (user) => {
    onApprove(user);
  };

  const handleReject = async (userId) => {
    const confirmed = await showConfirm({
      title: 'Reject User Application',
      message: 'Are you sure you want to reject this application? This will permanently delete the user account.',
      type: 'danger',
      confirmText: 'Reject Application',
      cancelText: 'Cancel'
    });

    if (confirmed) {
      onReject(userId);
    }
  };

  return (
    <>
      <ConfirmDialog />
      
      <div>
        {/* Search */}
        <div className="flex items-center justify-between mb-6">
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5" style={{ color: '#7F8C8D' }} />
            <input
              type="text"
              placeholder="Search pending users..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 rounded-lg border focus:outline-none focus:ring-2"
              style={{ borderColor: '#E0E0E0' }}
            />
          </div>
          <div className="ml-4 px-4 py-2 rounded-lg" style={{ backgroundColor: '#FEF3C7' }}>
            <span className="text-sm font-medium" style={{ color: '#92400E' }}>
              {filteredUsers.length} pending approval{filteredUsers.length !== 1 ? 's' : ''}
            </span>
          </div>
        </div>

        {/* Info Banner */}
        {filteredUsers.length > 0 && (
          <div className="mb-6 p-4 rounded-lg flex items-start" style={{ backgroundColor: '#EBF5FF' }}>
            <UserCheck className="w-5 h-5 mr-3 mt-0.5" style={{ color: '#1E40AF' }} />
            <div>
              <p className="text-sm font-medium" style={{ color: '#1E40AF' }}>
                Review Registration Applications
              </p>
              <p className="text-sm mt-1" style={{ color: '#1E3A8A' }}>
                These users have submitted registration applications. Review their details and assign appropriate roles before approving.
              </p>
            </div>
          </div>
        )}

        {/* Pending Users Table */}
        {loading ? (
          <div className="text-center py-12">
            <Loader2 className="w-8 h-8 animate-spin mx-auto" style={{ color: companyProfile.primary_color }} />
            <p className="mt-4" style={{ color: '#7F8C8D' }}>Loading pending users...</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr style={{ backgroundColor: '#F8F9FA' }}>
                  <th className="px-4 py-3 text-left text-sm font-semibold" style={{ color: companyProfile.secondary_color }}>
                    Applicant
                  </th>
                  <th className="px-4 py-3 text-left text-sm font-semibold" style={{ color: companyProfile.secondary_color }}>
                    Email
                  </th>
                  <th className="px-4 py-3 text-left text-sm font-semibold" style={{ color: companyProfile.secondary_color }}>
                    Username
                  </th>
                  <th className="px-4 py-3 text-left text-sm font-semibold" style={{ color: companyProfile.secondary_color }}>
                    Applied On
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
                          className="w-10 h-10 rounded-full flex items-center justify-center text-white font-bold mr-3"
                          style={{ backgroundColor: '#F59E0B' }}
                        >
                          {u.first_name?.[0] || u.username?.[0] || 'U'}
                        </div>
                        <div>
                          <div className="font-medium" style={{ color: companyProfile.secondary_color }}>
                            {u.first_name && u.last_name ? `${u.first_name} ${u.last_name}` : 'Not provided'}
                          </div>
                          <div className="flex items-center mt-1">
                            <span
                              className="px-2 py-0.5 rounded-full text-xs font-medium"
                              style={{
                                backgroundColor: '#FEF3C7',
                                color: '#92400E',
                              }}
                            >
                              Pending Approval
                            </span>
                          </div>
                        </div>
                      </div>
                    </td>
                    <td className="px-4 py-3" style={{ color: '#7F8C8D' }}>
                      {u.email}
                    </td>
                    <td className="px-4 py-3" style={{ color: '#7F8C8D' }}>
                      <span className="font-mono text-sm">{u.username}</span>
                    </td>
                    <td className="px-4 py-3" style={{ color: '#7F8C8D' }}>
                      {new Date(u.date_joined).toLocaleDateString('en-US', {
                        month: 'short',
                        day: 'numeric',
                        year: 'numeric',
                        hour: '2-digit',
                        minute: '2-digit'
                      })}
                    </td>
                    <td className="px-4 py-3 text-right">
                      <button
                        onClick={() => handleApprove(u)}
                        className="px-4 py-2 rounded-lg mr-2 transition-colors text-white font-medium"
                        style={{ backgroundColor: '#10B981' }}
                        onMouseEnter={(e) => e.target.style.backgroundColor = '#059669'}
                        onMouseLeave={(e) => e.target.style.backgroundColor = '#10B981'}
                      >
                        <CheckCircle className="w-4 h-4 inline mr-1" />
                        Approve
                      </button>
                      <button
                        onClick={() => handleReject(u.id)}
                        className="px-4 py-2 rounded-lg transition-colors text-white font-medium"
                        style={{ backgroundColor: '#EF4444' }}
                        onMouseEnter={(e) => e.target.style.backgroundColor = '#DC2626'}
                        onMouseLeave={(e) => e.target.style.backgroundColor = '#EF4444'}
                      >
                        <XCircle className="w-4 h-4 inline mr-1" />
                        Reject
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {filteredUsers.length === 0 && (
              <div className="text-center py-12">
                <UserCheck className="w-16 h-16 mx-auto mb-4" style={{ color: '#D1D5DB' }} />
                <p className="text-lg font-medium" style={{ color: '#6B7280' }}>
                  No pending applications
                </p>
                <p className="mt-1" style={{ color: '#9CA3AF' }}>
                  All registration applications have been processed
                </p>
              </div>
            )}
          </div>
        )}
      </div>
    </>
  );
}