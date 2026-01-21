import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { api } from '../services/api';
import Sidebar from './Sidebar';
import { useNotification } from './notifications/useNotification';
import { useConfirm } from './notifications/useConfirm';
import {
  Search,
  Plus,
  Edit,
  Trash2,
  X,
} from 'lucide-react';

export default function Policies() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const { showNotification, NotificationContainer } = useNotification();
  const { showConfirm, ConfirmDialog } = useConfirm();
  
  const [policies, setPolicies] = useState([]);
  const [policyholders, setPolicyholders] = useState([]);
  const [vehicles, setVehicles] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [formData, setFormData] = useState({
    policyholder: '',
    vehicle: '',
    policy_type: 'COMPREHENSIVE',
    coverage_level: 'STANDARD',
    start_date: '',
    end_date: '',
    premium_amount: '',
    coverage_amount: '',
    deductible: '',
    status: 'ACTIVE',
    has_roadside_assistance: false,
    has_rental_coverage: false,
    has_glass_coverage: false,
  });

  useEffect(() => {
    fetchPolicies();
    fetchPolicyholders();
    fetchVehicles();
  }, []);

  const fetchPolicies = async () => {
    try {
      setIsLoading(true);
      const data = await api.getPolicies();
      setPolicies(data.results || data);
    } catch (err) {
      console.error('Failed to fetch policies:', err);
      showNotification('Failed to load policies', 'error');
    } finally {
      setIsLoading(false);
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

  const fetchVehicles = async () => {
    try {
      const data = await api.getVehicles();
      setVehicles(data.results || data);
    } catch (err) {
      console.error('Failed to fetch vehicles:', err);
    }
  };

  // Generate policy number matching training data format: POL-XXXXXXXXXXXX (max 20 chars)
  const generatePolicyNumber = () => {
    // Generate 12 random alphanumeric characters after POL-
    const randomPart = Math.random().toString(36).substr(2, 12).toUpperCase().padEnd(12, '0');
    return `POL-${randomPart}`;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      // Generate policy number if creating new policy
      const submitData = { ...formData };
      if (!editingId) {
        submitData.policy_number = generatePolicyNumber();
      }

      if (editingId) {
        await api.updatePolicy(editingId, submitData);
        showNotification('Policy updated successfully!', 'success');
      } else {
        await api.createPolicy(submitData);
        showNotification('Policy created successfully!', 'success');
      }
      setShowModal(false);
      resetForm();
      fetchPolicies();
    } catch (err) {
      console.error('Failed to save policy:', err);
      showNotification(err.data?.detail || err.message || 'Failed to save policy', 'error');
    }
  };

  const handleEdit = async (policy) => {
    setEditingId(policy.id);
    
    // First, fetch the full policy details from the backend
    // The list view doesn't include policyholder/vehicle IDs, only names
    try {
      const fullPolicy = await api.getPolicy(policy.id);
      
      setFormData({
        policyholder: String(fullPolicy.policyholder || ''),
        vehicle: String(fullPolicy.vehicle || ''),
        policy_type: fullPolicy.policy_type || 'COMPREHENSIVE',
        coverage_level: fullPolicy.coverage_level || 'STANDARD',
        start_date: fullPolicy.start_date || '',
        end_date: fullPolicy.end_date || '',
        premium_amount: fullPolicy.premium_amount || '',
        coverage_amount: fullPolicy.coverage_amount || '',
        deductible: fullPolicy.deductible || '',
        status: fullPolicy.status || 'ACTIVE',
        has_roadside_assistance: fullPolicy.has_roadside_assistance || false,
        has_rental_coverage: fullPolicy.has_rental_coverage || false,
        has_glass_coverage: fullPolicy.has_glass_coverage || false,
      });
      
      setShowModal(true);
    } catch (err) {
      console.error('Failed to fetch policy details:', err);
      showNotification('Failed to load policy details', 'error');
    }
  };

  const handleDelete = async (id) => {
    const confirmed = await showConfirm({
      title: 'Delete Policy',
      message: 'Are you sure you want to delete this policy? This action cannot be undone.',
      confirmText: 'Delete',
      cancelText: 'Cancel',
      type: 'danger',
    });

    if (confirmed) {
      try {
        await api.deletePolicy(id);
        showNotification('Policy deleted successfully!', 'success');
        fetchPolicies();
      } catch (err) {
        console.error('Failed to delete policy:', err);
        showNotification(err.message || 'Failed to delete policy', 'error');
      }
    }
  };

  const resetForm = () => {
    setEditingId(null);
    setFormData({
      policyholder: '',
      vehicle: '',
      policy_type: 'COMPREHENSIVE',
      coverage_level: 'STANDARD',
      start_date: '',
      end_date: '',
      premium_amount: '',
      coverage_amount: '',
      deductible: '',
      status: 'ACTIVE',
      has_roadside_assistance: false,
      has_rental_coverage: false,
      has_glass_coverage: false,
    });
  };

  const filteredPolicies = policies.filter((p) =>
    `${p.policy_number} ${p.policyholder_name || 'Unknown'} ${p.vehicle_display || 'Unknown'}`
      .toLowerCase()
      .includes(searchTerm.toLowerCase())
  );

  // Format display values
  const formatPolicyType = (type) => {
    const typeMap = {
      'COMPREHENSIVE': 'Comprehensive',
      'THIRD_PARTY': 'Third Party',
      'COLLISION': 'Collision',
      'LIABILITY': 'Liability',
    };
    return typeMap[type] || type;
  };

  const formatStatus = (status) => {
    const statusMap = {
      'ACTIVE': 'Active',
      'EXPIRED': 'Expired',
      'CANCELLED': 'Cancelled',
      'SUSPENDED': 'Suspended',
      'PENDING': 'Pending',
    };
    return statusMap[status] || status;
  };

  return (
    <div className="flex h-screen overflow-hidden" style={{ backgroundColor: '#F8F9FA' }}>
      <Sidebar />
      <NotificationContainer />
      <ConfirmDialog />

      <div className="flex-1 p-8 overflow-y-auto">
        <div className="mb-8">
          <h2 className="text-3xl font-bold" style={{ color: '#2C3E50' }}>
            Policies
          </h2>
          <p className="mt-2" style={{ color: '#7F8C8D' }}>
            Manage insurance policies
          </p>
        </div>

        {/* Search and Add */}
        <div className="bg-white p-6 rounded-lg shadow-lg mb-6">
          <div className="flex items-center justify-between gap-4">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5" style={{ color: '#7F8C8D' }} />
              <input
                type="text"
                placeholder="Search policies..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-3 rounded-lg border focus:outline-none focus:ring-2"
                style={{ borderColor: '#E5E7EB', backgroundColor: '#F8F9FA' }}
              />
            </div>
            <button
              onClick={() => {
                resetForm();
                setShowModal(true);
              }}
              className="flex items-center px-6 py-3 rounded-lg text-white font-medium transition-colors"
              style={{ backgroundColor: '#FF6B4A' }}
            >
              <Plus className="w-5 h-5 mr-2" />
              Add Policy
            </button>
          </div>
        </div>

        {/* Table */}
        {isLoading ? (
          <div className="text-center py-12">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2" style={{ borderColor: '#FF6B4A' }}></div>
            <p className="mt-4" style={{ color: '#7F8C8D' }}>Loading policies...</p>
          </div>
        ) : (
          <div className="bg-white rounded-lg shadow-lg overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead style={{ backgroundColor: '#F8F9FA' }}>
                  <tr>
                    <th className="px-6 py-4 text-left text-sm font-semibold" style={{ color: '#2C3E50' }}>Policy Number</th>
                    <th className="px-6 py-4 text-left text-sm font-semibold" style={{ color: '#2C3E50' }}>Policyholder</th>
                    <th className="px-6 py-4 text-left text-sm font-semibold" style={{ color: '#2C3E50' }}>Vehicle</th>
                    <th className="px-6 py-4 text-left text-sm font-semibold" style={{ color: '#2C3E50' }}>Type</th>
                    <th className="px-6 py-4 text-left text-sm font-semibold" style={{ color: '#2C3E50' }}>Premium</th>
                    <th className="px-6 py-4 text-left text-sm font-semibold" style={{ color: '#2C3E50' }}>Status</th>
                    <th className="px-6 py-4 text-left text-sm font-semibold" style={{ color: '#2C3E50' }}>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredPolicies.length === 0 ? (
                    <tr>
                      <td colSpan="7" className="px-6 py-8 text-center" style={{ color: '#7F8C8D' }}>
                        No policies found
                      </td>
                    </tr>
                  ) : (
                    filteredPolicies.map((policy) => (
                      <tr key={policy.id} className="border-t" style={{ borderColor: '#E5E7EB' }}>
                        <td className="px-6 py-4" style={{ color: '#2C3E50' }}>
                          {policy.policy_number}
                        </td>
                        <td className="px-6 py-4" style={{ color: '#7F8C8D' }}>{policy.policyholder_name || 'Unknown'}</td>
                        <td className="px-6 py-4" style={{ color: '#7F8C8D' }}>{policy.vehicle_display || 'Unknown'}</td>
                        <td className="px-6 py-4" style={{ color: '#7F8C8D' }}>{formatPolicyType(policy.policy_type)}</td>
                        <td className="px-6 py-4" style={{ color: '#7F8C8D' }}>
                          ${parseFloat(policy.premium_amount).toLocaleString()}
                        </td>
                        <td className="px-6 py-4">
                          <span
                            className="px-3 py-1 rounded-full text-xs font-medium"
                            style={{
                              backgroundColor: policy.status === 'ACTIVE' ? '#D1FAE5' : '#FEE2E2',
                              color: policy.status === 'ACTIVE' ? '#065F46' : '#991B1B',
                            }}
                          >
                            {formatStatus(policy.status)}
                          </span>
                        </td>
                        <td className="px-6 py-4">
                          <div className="flex items-center gap-2">
                            <button
                              onClick={() => handleEdit(policy)}
                              className="p-2 rounded-lg transition-colors"
                              style={{ backgroundColor: '#EBF5FF', color: '#3B82F6' }}
                            >
                              <Edit className="w-4 h-4" />
                            </button>
                            <button
                              onClick={() => handleDelete(policy.id)}
                              className="p-2 rounded-lg transition-colors"
                              style={{ backgroundColor: '#FEE2E2', color: '#EF4444' }}
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
          </div>
        )}

        {/* Modal */}
        {showModal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
            <div className="bg-white rounded-lg shadow-xl max-w-3xl w-full max-h-[90vh] overflow-y-auto">
              <div className="p-6 border-b" style={{ borderColor: '#E5E7EB' }}>
                <div className="flex items-center justify-between">
                  <h3 className="text-2xl font-bold" style={{ color: '#2C3E50' }}>
                    {editingId ? 'Edit Policy' : 'Add Policy'}
                  </h3>
                  <button
                    onClick={() => {
                      setShowModal(false);
                      resetForm();
                    }}
                    className="p-2 rounded-lg transition-colors"
                    style={{ backgroundColor: '#F8F9FA', color: '#7F8C8D' }}
                  >
                    <X className="w-5 h-5" />
                  </button>
                </div>
              </div>

              <form onSubmit={handleSubmit} className="p-6">
                <div className="grid grid-cols-2 gap-4 mb-4">
                  <div>
                    <label className="block text-sm font-medium mb-2" style={{ color: '#2C3E50' }}>
                      Policyholder *
                    </label>
                    <select
                      required
                      value={formData.policyholder}
                      onChange={(e) => setFormData({ ...formData, policyholder: e.target.value })}
                      className="w-full px-4 py-2 rounded-lg border focus:outline-none focus:ring-2"
                      style={{ borderColor: '#E5E7EB' }}
                    >
                      <option value="">Select Policyholder</option>
                      {policyholders.map((p) => (
                        <option key={p.id} value={String(p.id)}>
                          {p.full_name || `${p.first_name} ${p.last_name}`}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-2" style={{ color: '#2C3E50' }}>
                      Vehicle *
                    </label>
                    <select
                      required
                      value={formData.vehicle}
                      onChange={(e) => setFormData({ ...formData, vehicle: e.target.value })}
                      className="w-full px-4 py-2 rounded-lg border focus:outline-none focus:ring-2"
                      style={{ borderColor: '#E5E7EB' }}
                    >
                      <option value="">Select Vehicle</option>
                      {vehicles.map((v) => (
                        <option key={v.id} value={String(v.id)}>
                          {v.make} {v.model} ({v.registration_number})
                        </option>
                      ))}
                    </select>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4 mb-4">
                  <div>
                    <label className="block text-sm font-medium mb-2" style={{ color: '#2C3E50' }}>
                      Policy Type *
                    </label>
                    <select
                      required
                      value={formData.policy_type}
                      onChange={(e) => setFormData({ ...formData, policy_type: e.target.value })}
                      className="w-full px-4 py-2 rounded-lg border focus:outline-none focus:ring-2"
                      style={{ borderColor: '#E5E7EB' }}
                    >
                      <option value="COMPREHENSIVE">Comprehensive</option>
                      <option value="THIRD_PARTY">Third Party</option>
                      <option value="COLLISION">Collision</option>
                      <option value="LIABILITY">Liability</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-2" style={{ color: '#2C3E50' }}>
                      Coverage Level *
                    </label>
                    <select
                      required
                      value={formData.coverage_level}
                      onChange={(e) => setFormData({ ...formData, coverage_level: e.target.value })}
                      className="w-full px-4 py-2 rounded-lg border focus:outline-none focus:ring-2"
                      style={{ borderColor: '#E5E7EB' }}
                    >
                      <option value="BASIC">Basic</option>
                      <option value="STANDARD">Standard</option>
                      <option value="PREMIUM">Premium</option>
                    </select>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4 mb-4">
                  <div>
                    <label className="block text-sm font-medium mb-2" style={{ color: '#2C3E50' }}>
                      Start Date *
                    </label>
                    <input
                      type="date"
                      required
                      value={formData.start_date}
                      onChange={(e) => setFormData({ ...formData, start_date: e.target.value })}
                      className="w-full px-4 py-2 rounded-lg border focus:outline-none focus:ring-2"
                      style={{ borderColor: '#E5E7EB' }}
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-2" style={{ color: '#2C3E50' }}>
                      End Date *
                    </label>
                    <input
                      type="date"
                      required
                      value={formData.end_date}
                      onChange={(e) => setFormData({ ...formData, end_date: e.target.value })}
                      className="w-full px-4 py-2 rounded-lg border focus:outline-none focus:ring-2"
                      style={{ borderColor: '#E5E7EB' }}
                    />
                  </div>
                </div>

                <div className="grid grid-cols-3 gap-4 mb-4">
                  <div>
                    <label className="block text-sm font-medium mb-2" style={{ color: '#2C3E50' }}>
                      Premium Amount ($) *
                    </label>
                    <input
                      type="number"
                      step="0.01"
                      required
                      value={formData.premium_amount}
                      onChange={(e) => setFormData({ ...formData, premium_amount: e.target.value })}
                      className="w-full px-4 py-2 rounded-lg border focus:outline-none focus:ring-2"
                      style={{ borderColor: '#E5E7EB' }}
                      placeholder="0.00"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-2" style={{ color: '#2C3E50' }}>
                      Coverage Amount ($) *
                    </label>
                    <input
                      type="number"
                      step="0.01"
                      required
                      value={formData.coverage_amount}
                      onChange={(e) => setFormData({ ...formData, coverage_amount: e.target.value })}
                      className="w-full px-4 py-2 rounded-lg border focus:outline-none focus:ring-2"
                      style={{ borderColor: '#E5E7EB' }}
                      placeholder="0.00"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-2" style={{ color: '#2C3E50' }}>
                      Deductible ($) *
                    </label>
                    <input
                      type="number"
                      step="0.01"
                      required
                      value={formData.deductible}
                      onChange={(e) => setFormData({ ...formData, deductible: e.target.value })}
                      className="w-full px-4 py-2 rounded-lg border focus:outline-none focus:ring-2"
                      style={{ borderColor: '#E5E7EB' }}
                      placeholder="0.00"
                    />
                  </div>
                </div>

                <div className="mb-4">
                  <label className="block text-sm font-medium mb-2" style={{ color: '#2C3E50' }}>
                    Status *
                  </label>
                  <select
                    required
                    value={formData.status}
                    onChange={(e) => setFormData({ ...formData, status: e.target.value })}
                    className="w-full px-4 py-2 rounded-lg border focus:outline-none focus:ring-2"
                    style={{ borderColor: '#E5E7EB' }}
                  >
                    <option value="ACTIVE">Active</option>
                    <option value="PENDING">Pending</option>
                    <option value="EXPIRED">Expired</option>
                    <option value="CANCELLED">Cancelled</option>
                    <option value="SUSPENDED">Suspended</option>
                  </select>
                </div>

                <div className="mb-6">
                  <label className="block text-sm font-medium mb-3" style={{ color: '#2C3E50' }}>
                    Additional Coverage
                  </label>
                  <div className="space-y-2">
                    <label className="flex items-center">
                      <input
                        type="checkbox"
                        checked={formData.has_roadside_assistance}
                        onChange={(e) => setFormData({ ...formData, has_roadside_assistance: e.target.checked })}
                        className="mr-2"
                      />
                      <span style={{ color: '#7F8C8D' }}>Roadside Assistance</span>
                    </label>
                    <label className="flex items-center">
                      <input
                        type="checkbox"
                        checked={formData.has_rental_coverage}
                        onChange={(e) => setFormData({ ...formData, has_rental_coverage: e.target.checked })}
                        className="mr-2"
                      />
                      <span style={{ color: '#7F8C8D' }}>Rental Coverage</span>
                    </label>
                    <label className="flex items-center">
                      <input
                        type="checkbox"
                        checked={formData.has_glass_coverage}
                        onChange={(e) => setFormData({ ...formData, has_glass_coverage: e.target.checked })}
                        className="mr-2"
                      />
                      <span style={{ color: '#7F8C8D' }}>Glass Coverage</span>
                    </label>
                  </div>
                </div>

                <div className="flex justify-end gap-4">
                  <button
                    type="button"
                    onClick={() => {
                      setShowModal(false);
                      resetForm();
                    }}
                    className="px-6 py-2 rounded-lg font-medium transition-colors"
                    style={{ backgroundColor: '#F8F9FA', color: '#7F8C8D' }}
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="px-6 py-2 rounded-lg text-white font-medium transition-colors"
                    style={{ backgroundColor: '#FF6B4A' }}
                  >
                    {editingId ? 'Update' : 'Create'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}