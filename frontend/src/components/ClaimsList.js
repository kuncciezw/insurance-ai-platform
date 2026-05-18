import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../services/api';
import Sidebar from './Sidebar';
import {
  Search, Plus, Edit, Trash2, ChevronLeft, ChevronRight, Filter,
  ChevronRight as ArrowRight,
} from 'lucide-react';
import AddEditClaimModal from './AddEditClaimModal';
import { useNotification } from './notifications/useNotification';
import { useConfirm } from './notifications/useConfirm';

const STATUS_PALETTE = {
  SUBMITTED:    { bg: '#DBEAFE', text: '#1E3A8A' },
  UNDER_REVIEW: { bg: '#FEF3C7', text: '#92400E' },
  APPROVED:     { bg: '#D1FAE5', text: '#065F46' },
  REJECTED:     { bg: '#FEE2E2', text: '#991B1B' },
  PAID:         { bg: '#D1FAE5', text: '#065F46' },
  CLOSED:       { bg: '#F3F4F6', text: '#1F2937' },
};

const SEVERITY_PALETTE = {
  MINOR:      { bg: '#D1FAE5', text: '#065F46' },
  MODERATE:   { bg: '#FEF3C7', text: '#92400E' },
  MAJOR:      { bg: '#FEE2E2', text: '#991B1B' },
  TOTAL_LOSS: { bg: '#4B1010', text: '#FECACA' },
};

const STATUSES = ['All', 'SUBMITTED', 'UNDER_REVIEW', 'APPROVED', 'REJECTED', 'PAID', 'CLOSED'];
const ITEMS_PER_PAGE = 12;

export default function ClaimsList() {
  const navigate = useNavigate();
  const { showNotification, NotificationContainer } = useNotification();
  const { showConfirm, ConfirmDialog } = useConfirm();

  const [claims,        setClaims]        = useState([]);
  const [isLoading,     setIsLoading]     = useState(true);
  const [searchTerm,    setSearchTerm]    = useState('');
  const [statusFilter,  setStatusFilter]  = useState('All');
  const [showModal,     setShowModal]     = useState(false);
  const [editingClaim,  setEditingClaim]  = useState(null);
  const [currentPage,   setCurrentPage]   = useState(1);

  useEffect(() => { fetchClaims(); }, []);

  const fetchClaims = async () => {
    setIsLoading(true);
    try {
      const data = await api.getClaims();
      setClaims(data.results || data);
    } catch (err) {
      showNotification('Failed to load claims', 'error');
    } finally {
      setIsLoading(false);
    }
  };

  const handleEdit = (e, claim) => {
    e.stopPropagation();
    setEditingClaim(claim);
    setShowModal(true);
  };

  const handleDelete = async (e, id) => {
    e.stopPropagation();
    const confirmed = await showConfirm({
      title:   'Delete Claim',
      message: 'Are you sure you want to delete this claim? This action cannot be undone.',
      type:    'danger',
    });
    if (!confirmed) return;
    try {
      await api.deleteClaim(id);
      showNotification('Claim deleted', 'success');
      fetchClaims();
    } catch {
      showNotification('Failed to delete claim', 'error');
    }
  };

  // ── KEY CHANGE: navigate to new claim detail; just refresh on edit ────────
  const handleModalSuccess = (newClaim) => {
    if (newClaim?.id) {
      // New claim was submitted and auto-processed — go straight to the result
      navigate(`/claims/${newClaim.id}`);
    } else {
      // Edit — simply refresh the list in place
      showNotification('Claim updated', 'success');
      fetchClaims();
    }
  };

  const filteredClaims = claims.filter((c) => {
    const matchSearch = `${c.claim_number} ${c.policy_number || ''} ${c.policyholder_name || ''} ${c.claim_type || ''}`
      .toLowerCase().includes(searchTerm.toLowerCase());
    const matchStatus = statusFilter === 'All' || (c.claim_status || c.status) === statusFilter;
    return matchSearch && matchStatus;
  });

  const totalPages = Math.max(1, Math.ceil(filteredClaims.length / ITEMS_PER_PAGE));
  const startIdx   = (currentPage - 1) * ITEMS_PER_PAGE;
  const paginated  = filteredClaims.slice(startIdx, startIdx + ITEMS_PER_PAGE);

  useEffect(() => setCurrentPage(1), [searchTerm, statusFilter]);

  const fraudColor = (score) => {
    if (score == null) return { bg: '#F3F4F6', text: '#6B7280' };
    if (score > 0.7)   return { bg: '#FEE2E2', text: '#991B1B' };
    if (score > 0.4)   return { bg: '#FEF3C7', text: '#92400E' };
    return               { bg: '#D1FAE5', text: '#065F46' };
  };

  return (
    <div className="flex h-screen overflow-hidden" style={{ backgroundColor: '#F8F9FA' }}>
      <Sidebar />
      <NotificationContainer />
      <ConfirmDialog />

      <div className="flex-1 overflow-y-auto">
        <div className="p-8">

          {/* ── Header ─────────────────────────────────────────────────────── */}
          <div className="mb-8">
            <h2 className="text-3xl font-bold" style={{ color: '#2C3E50' }}>Claims Management</h2>
            <p className="mt-1.5 text-sm" style={{ color: '#7F8C8D' }}>
              First Notice of Loss &amp; claim tracking · Click any row to view full details
            </p>
          </div>

          {/* ── Search + Add ────────────────────────────────────────────────── */}
          <div className="bg-white rounded-xl shadow-sm px-5 py-4 mb-4 flex items-center gap-4">
            <div className="flex-1 relative">
              <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4" style={{ color: '#7F8C8D' }} />
              <input
                type="text"
                placeholder="Search by claim number, policy, policyholder…"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-2.5 rounded-lg border text-sm focus:outline-none focus:ring-2"
                style={{ borderColor: '#E5E7EB', backgroundColor: '#F8F9FA' }}
                onFocus={(e) => { e.target.style.borderColor = '#FF6B4A'; e.target.style.backgroundColor = 'white'; }}
                onBlur={(e)  => { e.target.style.borderColor = '#E5E7EB'; e.target.style.backgroundColor = '#F8F9FA'; }}
              />
            </div>
            <button
              onClick={() => { setEditingClaim(null); setShowModal(true); }}
              className="flex items-center px-5 py-2.5 rounded-xl text-white font-semibold text-sm transition-all"
              style={{ backgroundColor: '#FF6B4A', boxShadow: '0 2px 8px rgba(255,107,74,0.3)' }}
              onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = '#E55A3A')}
              onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = '#FF6B4A')}>
              <Plus className="w-4 h-4 mr-2" />
              New Claim
            </button>
          </div>

          {/* ── Status Filter ───────────────────────────────────────────────── */}
          <div className="bg-white rounded-xl shadow-sm px-5 py-3 mb-6 flex items-center gap-3 flex-wrap">
            <Filter className="w-4 h-4 flex-shrink-0" style={{ color: '#7F8C8D' }} />
            <span className="text-xs font-semibold uppercase tracking-wider flex-shrink-0" style={{ color: '#7F8C8D' }}>Status</span>
            <div className="flex gap-2 flex-wrap">
              {STATUSES.map((s) => (
                <button key={s} onClick={() => setStatusFilter(s)}
                        className="px-3 py-1 rounded-lg text-xs font-semibold transition-all"
                        style={{
                          backgroundColor: statusFilter === s ? '#2C3E50' : 'transparent',
                          color:           statusFilter === s ? '#FFFFFF' : '#7F8C8D',
                          border:          statusFilter === s ? 'none'    : '1px solid #E5E7EB',
                        }}>
                  {s === 'UNDER_REVIEW' ? 'Under Review' : s === 'All' ? 'All' : s.replace('_', ' ')}
                </button>
              ))}
            </div>
            <span className="ml-auto text-xs" style={{ color: '#9CA3AF' }}>
              {filteredClaims.length} claim{filteredClaims.length !== 1 ? 's' : ''}
            </span>
          </div>

          {/* ── Table ──────────────────────────────────────────────────────── */}
          {isLoading ? (
            <div className="text-center py-20">
              <div className="inline-block animate-spin rounded-full h-10 w-10 border-b-2 mb-3"
                   style={{ borderColor: '#FF6B4A' }} />
              <p className="text-sm" style={{ color: '#7F8C8D' }}>Loading claims…</p>
            </div>
          ) : (
            <div className="bg-white rounded-xl shadow-sm overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead style={{ backgroundColor: '#F8F9FA', borderBottom: '2px solid #E5E7EB' }}>
                    <tr>
                      {['Claim #', 'Policy', 'Type', 'Severity', 'Fraud Score', 'Status', 'Submitted', 'Actions'].map((h) => (
                        <th key={h}
                            className="px-5 py-4 text-left text-xs font-bold uppercase tracking-wider"
                            style={{ color: '#2C3E50' }}>
                          {h}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {paginated.length === 0 ? (
                      <tr>
                        <td colSpan="8" className="px-6 py-16 text-center text-sm" style={{ color: '#7F8C8D' }}>
                          {searchTerm || statusFilter !== 'All'
                            ? 'No claims match your filters.'
                            : 'No claims yet. Submit the first one!'}
                        </td>
                      </tr>
                    ) : (
                      paginated.map((claim) => {
                        const sp = STATUS_PALETTE[claim.claim_status]   || STATUS_PALETTE.SUBMITTED;
                        const sv = SEVERITY_PALETTE[claim.severity]     || SEVERITY_PALETTE.MINOR;
                        const fc = fraudColor(claim.fraud_score);
                        const submitted = claim.submitted_date
                          ? new Date(claim.submitted_date).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
                          : '—';

                        return (
                          <tr key={claim.id}
                              onClick={() => navigate(`/claims/${claim.id}`)}
                              className="border-t transition-colors cursor-pointer group"
                              style={{ borderColor: '#F3F4F6' }}
                              onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = '#FFF5F3')}
                              onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = 'transparent')}>

                            <td className="px-5 py-4">
                              <div className="flex items-center gap-2">
                                <span className="font-mono text-xs font-bold px-2.5 py-1 rounded-lg"
                                      style={{ backgroundColor: '#F3F4F6', color: '#2C3E50' }}>
                                  {claim.claim_number}
                                </span>
                                <ArrowRight className="w-3.5 h-3.5 opacity-0 group-hover:opacity-100 transition-opacity"
                                            style={{ color: '#FF6B4A' }} />
                              </div>
                            </td>

                            <td className="px-5 py-4">
                              <p className="text-sm font-medium" style={{ color: '#2C3E50' }}>
                                {claim.policy_number || '—'}
                              </p>
                              {claim.policyholder_name && (
                                <p className="text-xs mt-0.5 truncate max-w-32" style={{ color: '#9CA3AF' }}>
                                  {claim.policyholder_name}
                                </p>
                              )}
                            </td>

                            <td className="px-5 py-4 text-sm" style={{ color: '#7F8C8D' }}>
                              {claim.claim_type || '—'}
                            </td>

                            <td className="px-5 py-4">
                              <span className="px-2.5 py-1 rounded-full text-xs font-bold"
                                    style={{ backgroundColor: sv.bg, color: sv.text }}>
                                {claim.severity || '—'}
                              </span>
                            </td>

                            <td className="px-5 py-4">
                              {claim.fraud_score != null ? (
                                <span className="px-2.5 py-1 rounded-full text-xs font-bold"
                                      style={{ backgroundColor: fc.bg, color: fc.text }}>
                                  {(claim.fraud_score * 100).toFixed(1)}%
                                </span>
                              ) : (
                                <span className="text-xs" style={{ color: '#D1D5DB' }}>Pending</span>
                              )}
                            </td>

                            <td className="px-5 py-4">
                              <span className="px-2.5 py-1 rounded-full text-xs font-bold"
                                    style={{ backgroundColor: sp.bg, color: sp.text }}>
                                {(claim.claim_status || '—').replace('_', ' ')}
                              </span>
                            </td>

                            <td className="px-5 py-4 text-xs" style={{ color: '#9CA3AF' }}>
                              {submitted}
                            </td>

                            <td className="px-5 py-4">
                              <div className="flex items-center gap-2">
                                <button
                                  onClick={(e) => handleEdit(e, claim)}
                                  className="p-2 rounded-lg transition-colors"
                                  style={{ backgroundColor: '#EBF5FF', color: '#3B82F6' }}
                                  title="Edit claim"
                                  onMouseEnter={(e) => { e.currentTarget.style.backgroundColor = '#3B82F6'; e.currentTarget.style.color = 'white'; }}
                                  onMouseLeave={(e) => { e.currentTarget.style.backgroundColor = '#EBF5FF'; e.currentTarget.style.color = '#3B82F6'; }}>
                                  <Edit className="w-3.5 h-3.5" />
                                </button>
                                <button
                                  onClick={(e) => handleDelete(e, claim.id)}
                                  className="p-2 rounded-lg transition-colors"
                                  style={{ backgroundColor: '#FEE2E2', color: '#EF4444' }}
                                  title="Delete claim"
                                  onMouseEnter={(e) => { e.currentTarget.style.backgroundColor = '#EF4444'; e.currentTarget.style.color = 'white'; }}
                                  onMouseLeave={(e) => { e.currentTarget.style.backgroundColor = '#FEE2E2'; e.currentTarget.style.color = '#EF4444'; }}>
                                  <Trash2 className="w-3.5 h-3.5" />
                                </button>
                              </div>
                            </td>
                          </tr>
                        );
                      })
                    )}
                  </tbody>
                </table>
              </div>

              {/* ── Pagination ─────────────────────────────────────────────── */}
              {totalPages > 1 && (
                <div className="flex items-center justify-between px-5 py-4 border-t"
                     style={{ borderColor: '#E5E7EB' }}>
                  <p className="text-xs" style={{ color: '#9CA3AF' }}>
                    Showing {startIdx + 1}–{Math.min(startIdx + ITEMS_PER_PAGE, filteredClaims.length)} of {filteredClaims.length}
                  </p>
                  <div className="flex items-center gap-1.5">
                    <button onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                            disabled={currentPage === 1}
                            className="p-2 rounded-lg disabled:opacity-40"
                            style={{ backgroundColor: '#F3F4F6', color: '#6B7280' }}>
                      <ChevronLeft className="w-4 h-4" />
                    </button>
                    {Array.from({ length: totalPages }, (_, i) => i + 1).map((pg) => (
                      <button key={pg} onClick={() => setCurrentPage(pg)}
                              className="px-3 py-1 rounded-lg text-sm font-semibold transition-all"
                              style={{
                                backgroundColor: currentPage === pg ? '#2C3E50' : 'transparent',
                                color:           currentPage === pg ? 'white'   : '#7F8C8D',
                              }}>
                        {pg}
                      </button>
                    ))}
                    <button onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
                            disabled={currentPage === totalPages}
                            className="p-2 rounded-lg disabled:opacity-40"
                            style={{ backgroundColor: '#F3F4F6', color: '#6B7280' }}>
                      <ChevronRight className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* ── Modal ─────────────────────────────────────────────────────────── */}
      <AddEditClaimModal
        isOpen={showModal}
        onClose={() => { setShowModal(false); setEditingClaim(null); }}
        onSuccess={handleModalSuccess}
        editingClaim={editingClaim}
      />
    </div>
  );
}