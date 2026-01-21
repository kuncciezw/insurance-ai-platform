import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { api } from '../services/api';
import Sidebar from './Sidebar';
import {
  Search,
  Plus,
  Edit,
  Trash2,
  Eye,
  Cpu,
  ChevronLeft,
  ChevronRight,
  Filter,
} from 'lucide-react';
import ClaimDetailsModal from './ClaimDetailsModal';
import AddEditClaimModal from './AddEditClaimModal';
import { useNotification } from './notifications/useNotification';
import { useConfirm } from './notifications/useConfirm';

export default function ClaimsList() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const { showNotification, NotificationContainer } = useNotification();
  const { showConfirm, ConfirmDialog } = useConfirm();
  const [claims, setClaims] = useState([]);
  const [policies, setPolicies] = useState([]);
  const [policyholders, setPolicyholders] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('All');
  const [showModal, setShowModal] = useState(false);
  const [selectedClaim, setSelectedClaim] = useState(null);
  const [editingClaim, setEditingClaim] = useState(null);
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 10;

  useEffect(() => {
    fetchClaims();
    fetchPolicies();
    fetchPolicyholders();
  }, []);

  const fetchClaims = async () => {
    try {
      setIsLoading(true);
      const data = await api.getClaims();
      setClaims(data.results || data);
    } catch (err) {
      console.error('Failed to fetch claims:', err);
      showNotification('Failed to load claims', 'error');
    } finally {
      setIsLoading(false);
    }
  };

  const fetchPolicies = async () => {
    try {
      const data = await api.getPolicies();
      setPolicies(data.results || data);
    } catch (err) {
      console.error('Failed to fetch policies:', err);
    }
  };

  const fetchPolicyholders = async () => {
    try {
      const data = await api.getPolicyholders();
      setPolicyholders(data.results || data);
    } catch (err) {
      console.error('Failed to fetch policyholders:', err);
    }
  };

  const handleViewDetails = async (claim) => {
    setSelectedClaim(claim);
  };

  const handleProcessWithAI = async (claimId) => {
    try {
      const result = await api.autoProcessClaim(claimId);
      // Refresh the claim with AI results
      const updatedClaim = claims.find(c => c.id === claimId);
      if (updatedClaim) {
        setSelectedClaim({ ...updatedClaim, ai_result: result });
      }
      showNotification('Claim processed successfully with AI', 'success');
    } catch (err) {
      console.error('AI processing failed:', err);
      showNotification('AI processing failed: ' + (err.message || 'Unknown error'), 'error');
    }
  };

  const handleEdit = (claim) => {
    setEditingClaim(claim);
    setShowModal(true);
  };

  const handleDelete = async (id) => {
    const confirmed = await showConfirm({
      title: 'Delete Claim',
      message: 'Are you sure you want to delete this claim? This action cannot be undone.',
      type: 'danger'
    });

    if (confirmed) {
      try {
        await api.deleteClaim(id);
        showNotification('Claim deleted successfully', 'success');
        fetchClaims();
      } catch (err) {
        console.error('Failed to delete claim:', err);
        showNotification('Failed to delete claim: ' + (err.message || 'Unknown error'), 'error');
      }
    }
  };

  const handleModalSuccess = () => {
    showNotification(editingClaim ? 'Claim updated successfully' : 'Claim created successfully', 'success');
    fetchClaims();
  };

  const getStatusColor = (status) => {
    const colors = {
      SUBMITTED: { bg: '#DBEAFE', text: '#1E3A8A' },
      'UNDER_REVIEW': { bg: '#FEF3C7', text: '#92400E' },
      APPROVED: { bg: '#D1FAE5', text: '#065F46' },
      REJECTED: { bg: '#FEE2E2', text: '#991B1B' },
      PAID: { bg: '#D1FAE5', text: '#065F46' },
      CLOSED: { bg: '#F3F4F6', text: '#1F2937' },
      Pending: { bg: '#FEF3C7', text: '#92400E' },
      'Under Review': { bg: '#DBEAFE', text: '#1E3A8A' },
    };
    return colors[status] || { bg: '#F3F4F6', text: '#1F2937' };
  };

  const isPendingClaim = (claim) => {
    const status = claim.claim_status || claim.status || '';
    return ['SUBMITTED', 'UNDER_REVIEW', 'Pending', 'Under Review'].includes(status);
  };

  const filteredClaims = claims.filter((c) => {
    const matchesSearch = `${c.claim_number} ${c.policy_number || ''} ${c.policyholder_name || ''} ${c.claim_type || ''}`
      .toLowerCase()
      .includes(searchTerm.toLowerCase());
    
    const matchesStatus = statusFilter === 'All' || 
      (c.claim_status || c.status) === statusFilter;
    
    return matchesSearch && matchesStatus;
  });

  const totalPages = Math.ceil(filteredClaims.length / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const paginatedClaims = filteredClaims.slice(startIndex, startIndex + itemsPerPage);

  return (
    <div className="flex h-screen overflow-hidden" style={{ backgroundColor: '#F8F9FA' }}>
      {/* Use the Sidebar component */}
      <Sidebar />

      <NotificationContainer />
      <ConfirmDialog />

      {/* Main Content */}
      <div className="flex-1 p-8 overflow-y-auto">
        <div className="mb-8">
          <h2 className="text-3xl font-bold" style={{ color: '#2C3E50' }}>
            Claims Management
          </h2>
          <p className="mt-2" style={{ color: '#7F8C8D' }}>
            Manage insurance claims and approvals
          </p>
        </div>

        {/* Filters and Search */}
        <div className="bg-white p-6 rounded-lg shadow-lg mb-6">
          <div className="flex items-center justify-between gap-4 mb-4">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5" style={{ color: '#7F8C8D' }} />
              <input
                type="text"
                placeholder="Search claims..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-3 rounded-lg border focus:outline-none focus:ring-2"
                style={{ borderColor: '#E5E7EB', backgroundColor: '#F8F9FA' }}
                onFocus={(e) => {
                  e.target.style.borderColor = '#FF6B4A';
                  e.target.style.backgroundColor = 'white';
                }}
                onBlur={(e) => {
                  e.target.style.borderColor = '#E5E7EB';
                  e.target.style.backgroundColor = '#F8F9FA';
                }}
              />
            </div>
            <button
              onClick={() => {
                setEditingClaim(null);
                setShowModal(true);
              }}
              className="flex items-center px-6 py-3 rounded-lg text-white font-medium transition-colors"
              style={{ backgroundColor: '#FF6B4A' }}
              onMouseEnter={(e) => {
                e.target.style.backgroundColor = '#E55A3A';
              }}
              onMouseLeave={(e) => {
                e.target.style.backgroundColor = '#FF6B4A';
              }}
            >
              <Plus className="w-5 h-5 mr-2" />
              Add Claim
            </button>
          </div>

          {/* Status Filter */}
          <div className="flex items-center gap-4">
            <Filter className="w-5 h-5" style={{ color: '#7F8C8D' }} />
            <span className="text-sm font-medium" style={{ color: '#7F8C8D' }}>Filter by Status:</span>
            <div className="flex gap-2">
              {['All', 'SUBMITTED', 'UNDER_REVIEW', 'APPROVED', 'REJECTED', 'PAID'].map((status) => (
                <button
                  key={status}
                  onClick={() => setStatusFilter(status)}
                  className="px-4 py-2 rounded-lg text-sm font-medium transition-all"
                  style={{
                    backgroundColor: statusFilter === status ? '#2C3E50' : 'transparent',
                    color: statusFilter === status ? '#FFFFFF' : '#7F8C8D',
                    border: statusFilter === status ? 'none' : '1px solid #E0E0E0',
                  }}
                >
                  {status === 'All' ? 'All' : status.replace('_', ' ')}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Table */}
        {isLoading ? (
          <div className="text-center py-12">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2" style={{ borderColor: '#FF6B4A' }}></div>
            <p className="mt-4" style={{ color: '#7F8C8D' }}>Loading claims...</p>
          </div>
        ) : (
          <div className="bg-white rounded-lg shadow-lg overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead style={{ backgroundColor: '#F8F9FA' }}>
                  <tr>
                    <th className="px-6 py-4 text-left text-sm font-semibold" style={{ color: '#2C3E50' }}>Claim Number</th>
                    <th className="px-6 py-4 text-left text-sm font-semibold" style={{ color: '#2C3E50' }}>Policy</th>
                    <th className="px-6 py-4 text-left text-sm font-semibold" style={{ color: '#2C3E50' }}>Incident Type</th>
                    <th className="px-6 py-4 text-left text-sm font-semibold" style={{ color: '#2C3E50' }}>Claimed</th>
                    <th className="px-6 py-4 text-left text-sm font-semibold" style={{ color: '#2C3E50' }}>Fraud Score</th>
                    <th className="px-6 py-4 text-left text-sm font-semibold" style={{ color: '#2C3E50' }}>Status</th>
                    <th className="px-6 py-4 text-left text-sm font-semibold" style={{ color: '#2C3E50' }}>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {paginatedClaims.length === 0 ? (
                    <tr>
                      <td colSpan="7" className="px-6 py-8 text-center" style={{ color: '#7F8C8D' }}>
                        No claims found
                      </td>
                    </tr>
                  ) : (
                    paginatedClaims.map((claim) => (
                      <tr key={claim.id} className="border-t hover:bg-gray-50 transition-colors" style={{ borderColor: '#E5E7EB' }}>
                        <td className="px-6 py-4 font-medium" style={{ color: '#2C3E50' }}>
                          {claim.claim_number}
                        </td>
                        <td className="px-6 py-4" style={{ color: '#7F8C8D' }}>
                          {claim.policy_number || 'Unknown'}
                          {claim.policyholder_name && (
                            <div className="text-xs" style={{ color: '#9CA3AF' }}>
                              {claim.policyholder_name}
                            </div>
                          )}
                        </td>
                        <td className="px-6 py-4" style={{ color: '#7F8C8D' }}>{claim.claim_type || claim.incident_type}</td>
                        <td className="px-6 py-4 font-medium" style={{ color: '#2C3E50' }}>
                          ${parseFloat(claim.claimed_amount).toLocaleString()}
                        </td>
                        <td className="px-6 py-4">
                          {claim.fraud_score !== null && claim.fraud_score !== undefined ? (
                            <span
                              className="px-3 py-1 rounded-full text-xs font-medium"
                              style={{
                                backgroundColor: claim.fraud_score > 0.7 ? '#FEE2E2' : claim.fraud_score > 0.4 ? '#FEF3C7' : '#D1FAE5',
                                color: claim.fraud_score > 0.7 ? '#991B1B' : claim.fraud_score > 0.4 ? '#92400E' : '#065F46',
                              }}
                            >
                              {(claim.fraud_score * 100).toFixed(1)}%
                            </span>
                          ) : (
                            <span style={{ color: '#7F8C8D' }}>N/A</span>
                          )}
                        </td>
                        <td className="px-6 py-4">
                          <span
                            className="px-3 py-1 rounded-full text-xs font-medium"
                            style={{
                              backgroundColor: getStatusColor(claim.claim_status || claim.status).bg,
                              color: getStatusColor(claim.claim_status || claim.status).text,
                            }}
                          >
                            {claim.claim_status || claim.status}
                          </span>
                        </td>
                        <td className="px-6 py-4">
                          <div className="flex items-center gap-2">
                            <button
                              onClick={() => handleViewDetails(claim)}
                              className="p-2 rounded-lg transition-colors"
                              style={{ backgroundColor: '#E0F2FE', color: '#0284C7' }}
                              onMouseEnter={(e) => {
                                e.target.style.backgroundColor = '#0284C7';
                                e.target.style.color = 'white';
                              }}
                              onMouseLeave={(e) => {
                                e.target.style.backgroundColor = '#E0F2FE';
                                e.target.style.color = '#0284C7';
                              }}
                              title="View Details"
                            >
                              <Eye className="w-4 h-4" />
                            </button>
                            {isPendingClaim(claim) && (
                              <button
                                onClick={() => handleProcessWithAI(claim.id)}
                                className="p-2 rounded-lg transition-colors"
                                style={{ backgroundColor: '#F0FDF4', color: '#10B981' }}
                                onMouseEnter={(e) => {
                                  e.target.style.backgroundColor = '#10B981';
                                  e.target.style.color = 'white';
                                }}
                                onMouseLeave={(e) => {
                                  e.target.style.backgroundColor = '#F0FDF4';
                                  e.target.style.color = '#10B981';
                                }}
                                title="Process with AI"
                              >
                                <Cpu className="w-4 h-4" />
                              </button>
                            )}
                            <button
                              onClick={() => handleEdit(claim)}
                              className="p-2 rounded-lg transition-colors"
                              style={{ backgroundColor: '#EBF5FF', color: '#3B82F6' }}
                              onMouseEnter={(e) => {
                                e.target.style.backgroundColor = '#3B82F6';
                                e.target.style.color = 'white';
                              }}
                              onMouseLeave={(e) => {
                                e.target.style.backgroundColor = '#EBF5FF';
                                e.target.style.color = '#3B82F6';
                              }}
                              title="Edit"
                            >
                              <Edit className="w-4 h-4" />
                            </button>
                            <button
                              onClick={() => handleDelete(claim.id)}
                              className="p-2 rounded-lg transition-colors"
                              style={{ backgroundColor: '#FEE2E2', color: '#EF4444' }}
                              onMouseEnter={(e) => {
                                e.target.style.backgroundColor = '#EF4444';
                                e.target.style.color = 'white';
                              }}
                              onMouseLeave={(e) => {
                                e.target.style.backgroundColor = '#FEE2E2';
                                e.target.style.color = '#EF4444';
                              }}
                              title="Delete"
                            >
                              <Trash2 className="w-4 h-4" />
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>

            {/* Pagination */}
            <div className="flex items-center justify-between px-6 py-4 border-t" style={{ borderColor: '#E5E7EB' }}>
              <div className="text-sm" style={{ color: '#7F8C8D' }}>
                Showing {startIndex + 1} to {Math.min(startIndex + itemsPerPage, filteredClaims.length)} of {filteredClaims.length} claims
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
                  disabled={currentPage === 1}
                  className="p-2 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  style={{ backgroundColor: '#F8F9FA', color: '#7F8C8D' }}
                >
                  <ChevronLeft className="w-5 h-5" />
                </button>
                <div className="flex gap-1">
                  {Array.from({ length: totalPages }, (_, i) => i + 1).map((page) => (
                    <button
                      key={page}
                      onClick={() => setCurrentPage(page)}
                      className="px-3 py-1 rounded-lg text-sm font-medium transition-all"
                      style={{
                        backgroundColor: currentPage === page ? '#2C3E50' : 'transparent',
                        color: currentPage === page ? '#FFFFFF' : '#7F8C8D',
                      }}
                    >
                      {page}
                    </button>
                  ))}
                </div>
                <button
                  onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
                  disabled={currentPage === totalPages}
                  className="p-2 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  style={{ backgroundColor: '#F8F9FA', color: '#7F8C8D' }}
                >
                  <ChevronRight className="w-5 h-5" />
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Add/Edit Modal */}
        <AddEditClaimModal
          isOpen={showModal}
          onClose={() => {
            setShowModal(false);
            setEditingClaim(null);
          }}
          onSuccess={handleModalSuccess}
          editingClaim={editingClaim}
        />

        {/* Claim Details Modal */}
        {selectedClaim && (
          <ClaimDetailsModal
            claim={selectedClaim}
            onClose={() => setSelectedClaim(null)}
            onRefresh={fetchClaims}
          />
        )}
      </div>
    </div>
  );
}