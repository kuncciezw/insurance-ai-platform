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

export default function Policyholders() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const { showNotification, NotificationContainer } = useNotification();
  const { showConfirm, ConfirmDialog } = useConfirm();
  
  const [policyholders, setPolicyholders] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [formData, setFormData] = useState({
    policy_holder_id: '',
    first_name: '',
    last_name: '',
    date_of_birth: '',
    gender: 'M',
    email: '',
    phone_number: '',
    address_line1: '',
    address_line2: '',
    city: '',
    state: '',
    postal_code: '',
    country: 'Zimbabwe',
    marital_status: 'SINGLE',
    occupation: 'EMPLOYED',
    annual_income: 0,
    credit_score: 650,
    years_with_company: 0,
    is_active: true,
  });

  const generatePolicyHolderId = () => {
    // Generate ID in format: ZW-PH-XXXXXXXXXX (10 random digits)
    const randomDigits = Math.floor(1000000000 + Math.random() * 9000000000);
    return `ZW-PH-${randomDigits}`;
  };

  useEffect(() => {
    fetchPolicyholders();
  }, []);

  const fetchPolicyholders = async () => {
    try {
      setIsLoading(true);
      const data = await api.getPolicyholders();
      setPolicyholders(data.results || data);
    } catch (err) {
      console.error('Failed to fetch policyholders:', err);
      showNotification('Failed to load policyholders', 'error');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (editingId) {
        await api.updatePolicyholder(editingId, formData);
        showNotification('Policyholder updated successfully', 'success');
      } else {
        await api.createPolicyholder(formData);
        showNotification('Policyholder created successfully', 'success');
      }
      setShowModal(false);
      resetForm();
      fetchPolicyholders();
    } catch (err) {
      console.error('Failed to save policyholder:', err);
      showNotification(
        err.message || 'Failed to save policyholder. Please check all required fields.',
        'error'
      );
    }
  };

  const handleEdit = (policyholder) => {
    setEditingId(policyholder.id);
    setFormData({
      policy_holder_id: policyholder.policy_holder_id || '',
      first_name: policyholder.first_name || '',
      last_name: policyholder.last_name || '',
      date_of_birth: policyholder.date_of_birth || '',
      gender: policyholder.gender || 'M',
      email: policyholder.email || '',
      phone_number: policyholder.phone_number || '',
      address_line1: policyholder.address_line1 || '',
      address_line2: policyholder.address_line2 || '',
      city: policyholder.city || '',
      state: policyholder.state || '',
      postal_code: policyholder.postal_code || '',
      country: policyholder.country || 'Zimbabwe',
      marital_status: policyholder.marital_status || 'SINGLE',
      occupation: policyholder.occupation || 'EMPLOYED',
      annual_income: policyholder.annual_income || 0,
      credit_score: policyholder.credit_score || 650,
      years_with_company: policyholder.years_with_company || 0,
      is_active: policyholder.is_active !== undefined ? policyholder.is_active : true,
    });
    setShowModal(true);
  };

  const handleDelete = async (id) => {
    const confirmed = await showConfirm({
      title: 'Delete Policyholder',
      message: 'Are you sure you want to delete this policyholder? This action cannot be undone.',
      type: 'danger',
    });

    if (confirmed) {
      try {
        await api.deletePolicyholder(id);
        showNotification('Policyholder deleted successfully', 'success');
        fetchPolicyholders();
      } catch (err) {
        console.error('Failed to delete policyholder:', err);
        showNotification(err.message || 'Failed to delete policyholder', 'error');
      }
    }
  };

  const resetForm = () => {
    setEditingId(null);
    setFormData({
      policy_holder_id: generatePolicyHolderId(),
      first_name: '',
      last_name: '',
      date_of_birth: '',
      gender: 'M',
      email: '',
      phone_number: '',
      address_line1: '',
      address_line2: '',
      city: '',
      state: '',
      postal_code: '',
      country: 'Zimbabwe',
      marital_status: 'SINGLE',
      occupation: 'EMPLOYED',
      annual_income: 0,
      credit_score: 650,
      years_with_company: 0,
      is_active: true,
    });
  };

  const filteredPolicyholders = policyholders.filter((p) =>
    `${p.first_name} ${p.last_name} ${p.email} ${p.policy_holder_id}`
      .toLowerCase()
      .includes(searchTerm.toLowerCase())
  );

  return (
    <div className="flex h-screen overflow-hidden" style={{ backgroundColor: '#F8F9FA' }}>
      <Sidebar />
      <NotificationContainer />
      <ConfirmDialog />

      {/* Main Content */}
      <div className="flex-1 p-8 overflow-y-auto">
        <div className="mb-8">
          <h2 className="text-3xl font-bold" style={{ color: '#2C3E50' }}>
            Policyholders
          </h2>
          <p className="mt-2" style={{ color: '#7F8C8D' }}>
            Manage policyholder information
          </p>
        </div>

        {/* Search and Add */}
        <div className="bg-white p-6 rounded-lg shadow-lg mb-6">
          <div className="flex items-center justify-between gap-4">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5" style={{ color: '#7F8C8D' }} />
              <input
                type="text"
                placeholder="Search policyholders..."
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
                resetForm();
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
              Add Policyholder
            </button>
          </div>
        </div>

        {/* Table */}
        {isLoading ? (
          <div className="text-center py-12">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2" style={{ borderColor: '#FF6B4A' }}></div>
            <p className="mt-4" style={{ color: '#7F8C8D' }}>Loading policyholders...</p>
          </div>
        ) : (
          <div className="bg-white rounded-lg shadow-lg overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead style={{ backgroundColor: '#F8F9FA' }}>
                  <tr>
                    <th className="px-6 py-4 text-left text-sm font-semibold" style={{ color: '#2C3E50' }}>ID</th>
                    <th className="px-6 py-4 text-left text-sm font-semibold" style={{ color: '#2C3E50' }}>Name</th>
                    <th className="px-6 py-4 text-left text-sm font-semibold" style={{ color: '#2C3E50' }}>Email</th>
                    <th className="px-6 py-4 text-left text-sm font-semibold" style={{ color: '#2C3E50' }}>Phone</th>
                    <th className="px-6 py-4 text-left text-sm font-semibold" style={{ color: '#2C3E50' }}>City</th>
                    <th className="px-6 py-4 text-left text-sm font-semibold" style={{ color: '#2C3E50' }}>Status</th>
                    <th className="px-6 py-4 text-left text-sm font-semibold" style={{ color: '#2C3E50' }}>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredPolicyholders.length === 0 ? (
                    <tr>
                      <td colSpan="7" className="px-6 py-8 text-center" style={{ color: '#7F8C8D' }}>
                        No policyholders found
                      </td>
                    </tr>
                  ) : (
                    filteredPolicyholders.map((policyholder) => (
                      <tr key={policyholder.id} className="border-t" style={{ borderColor: '#E5E7EB' }}>
                        <td className="px-6 py-4" style={{ color: '#2C3E50' }}>
                          {policyholder.policy_holder_id}
                        </td>
                        <td className="px-6 py-4" style={{ color: '#2C3E50' }}>
                          {policyholder.full_name}
                        </td>
                        <td className="px-6 py-4" style={{ color: '#7F8C8D' }}>{policyholder.email}</td>
                        <td className="px-6 py-4" style={{ color: '#7F8C8D' }}>{policyholder.phone_number}</td>
                        <td className="px-6 py-4" style={{ color: '#7F8C8D' }}>{policyholder.city}</td>
                        <td className="px-6 py-4">
                          <span 
                            className="px-2 py-1 rounded-full text-xs font-medium"
                            style={{
                              backgroundColor: policyholder.is_active ? '#D1FAE5' : '#FEE2E2',
                              color: policyholder.is_active ? '#065F46' : '#991B1B'
                            }}
                          >
                            {policyholder.is_active ? 'Active' : 'Inactive'}
                          </span>
                        </td>
                        <td className="px-6 py-4">
                          <div className="flex items-center gap-2">
                            <button
                              onClick={() => handleEdit(policyholder)}
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
                            >
                              <Edit className="w-4 h-4" />
                            </button>
                            <button
                              onClick={() => handleDelete(policyholder.id)}
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
                    {editingId ? 'Edit Policyholder' : 'Add Policyholder'}
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

              <div className="p-6">
                {/* Policy Holder ID - Auto-generated, Read-only */}
                <div className="mb-4">
                  <label className="block text-sm font-medium mb-2" style={{ color: '#2C3E50' }}>
                    Policy Holder ID *
                  </label>
                  <input
                    type="text"
                    required
                    value={formData.policy_holder_id}
                    readOnly
                    className="w-full px-4 py-2 rounded-lg border focus:outline-none"
                    style={{ borderColor: '#E5E7EB', backgroundColor: '#F8F9FA', color: '#7F8C8D' }}
                    placeholder="Auto-generated"
                  />
                  <p className="mt-1 text-xs" style={{ color: '#7F8C8D' }}>
                    Auto-generated unique identifier
                  </p>
                </div>

                {/* First Name and Last Name */}
                <div className="grid grid-cols-2 gap-4 mb-4">
                  <div>
                    <label className="block text-sm font-medium mb-2" style={{ color: '#2C3E50' }}>
                      First Name *
                    </label>
                    <input
                      type="text"
                      required
                      value={formData.first_name}
                      onChange={(e) => setFormData({ ...formData, first_name: e.target.value })}
                      className="w-full px-4 py-2 rounded-lg border focus:outline-none focus:ring-2"
                      style={{ borderColor: '#E5E7EB' }}
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-2" style={{ color: '#2C3E50' }}>
                      Last Name *
                    </label>
                    <input
                      type="text"
                      required
                      value={formData.last_name}
                      onChange={(e) => setFormData({ ...formData, last_name: e.target.value })}
                      className="w-full px-4 py-2 rounded-lg border focus:outline-none focus:ring-2"
                      style={{ borderColor: '#E5E7EB' }}
                    />
                  </div>
                </div>

                {/* Date of Birth and Gender */}
                <div className="grid grid-cols-2 gap-4 mb-4">
                  <div>
                    <label className="block text-sm font-medium mb-2" style={{ color: '#2C3E50' }}>
                      Date of Birth *
                    </label>
                    <input
                      type="date"
                      required
                      value={formData.date_of_birth}
                      onChange={(e) => setFormData({ ...formData, date_of_birth: e.target.value })}
                      className="w-full px-4 py-2 rounded-lg border focus:outline-none focus:ring-2"
                      style={{ borderColor: '#E5E7EB' }}
                      max={new Date().toISOString().split('T')[0]}
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-2" style={{ color: '#2C3E50' }}>
                      Gender *
                    </label>
                    <select
                      required
                      value={formData.gender}
                      onChange={(e) => setFormData({ ...formData, gender: e.target.value })}
                      className="w-full px-4 py-2 rounded-lg border focus:outline-none focus:ring-2"
                      style={{ borderColor: '#E5E7EB' }}
                    >
                      <option value="M">Male</option>
                      <option value="F">Female</option>
                      <option value="O">Other</option>
                    </select>
                  </div>
                </div>

                {/* Email and Phone */}
                <div className="grid grid-cols-2 gap-4 mb-4">
                  <div>
                    <label className="block text-sm font-medium mb-2" style={{ color: '#2C3E50' }}>
                      Email *
                    </label>
                    <input
                      type="email"
                      required
                      value={formData.email}
                      onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                      className="w-full px-4 py-2 rounded-lg border focus:outline-none focus:ring-2"
                      style={{ borderColor: '#E5E7EB' }}
                      placeholder="email@example.com"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-2" style={{ color: '#2C3E50' }}>
                      Phone Number *
                    </label>
                    <input
                      type="text"
                      required
                      value={formData.phone_number}
                      onChange={(e) => setFormData({ ...formData, phone_number: e.target.value })}
                      className="w-full px-4 py-2 rounded-lg border focus:outline-none focus:ring-2"
                      style={{ borderColor: '#E5E7EB' }}
                      placeholder="+263 123 456 789"
                    />
                  </div>
                </div>

                {/* Address Line 1 */}
                <div className="mb-4">
                  <label className="block text-sm font-medium mb-2" style={{ color: '#2C3E50' }}>
                    Address Line 1 *
                  </label>
                  <input
                    type="text"
                    required
                    value={formData.address_line1}
                    onChange={(e) => setFormData({ ...formData, address_line1: e.target.value })}
                    className="w-full px-4 py-2 rounded-lg border focus:outline-none focus:ring-2"
                    style={{ borderColor: '#E5E7EB' }}
                    placeholder="Street address"
                  />
                </div>

                {/* Address Line 2 */}
                <div className="mb-4">
                  <label className="block text-sm font-medium mb-2" style={{ color: '#2C3E50' }}>
                    Address Line 2
                  </label>
                  <input
                    type="text"
                    value={formData.address_line2}
                    onChange={(e) => setFormData({ ...formData, address_line2: e.target.value })}
                    className="w-full px-4 py-2 rounded-lg border focus:outline-none focus:ring-2"
                    style={{ borderColor: '#E5E7EB' }}
                    placeholder="Apartment, suite, etc. (optional)"
                  />
                </div>

                {/* City, State, Postal Code */}
                <div className="grid grid-cols-3 gap-4 mb-4">
                  <div>
                    <label className="block text-sm font-medium mb-2" style={{ color: '#2C3E50' }}>
                      City *
                    </label>
                    <input
                      type="text"
                      required
                      value={formData.city}
                      onChange={(e) => setFormData({ ...formData, city: e.target.value })}
                      className="w-full px-4 py-2 rounded-lg border focus:outline-none focus:ring-2"
                      style={{ borderColor: '#E5E7EB' }}
                      placeholder="Harare"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-2" style={{ color: '#2C3E50' }}>
                      State/Province *
                    </label>
                    <input
                      type="text"
                      required
                      value={formData.state}
                      onChange={(e) => setFormData({ ...formData, state: e.target.value })}
                      className="w-full px-4 py-2 rounded-lg border focus:outline-none focus:ring-2"
                      style={{ borderColor: '#E5E7EB' }}
                      placeholder="Harare"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-2" style={{ color: '#2C3E50' }}>
                      Postal Code *
                    </label>
                    <input
                      type="text"
                      required
                      value={formData.postal_code}
                      onChange={(e) => setFormData({ ...formData, postal_code: e.target.value })}
                      className="w-full px-4 py-2 rounded-lg border focus:outline-none focus:ring-2"
                      style={{ borderColor: '#E5E7EB' }}
                      placeholder="00263"
                    />
                  </div>
                </div>

                {/* Country */}
                <div className="mb-4">
                  <label className="block text-sm font-medium mb-2" style={{ color: '#2C3E50' }}>
                    Country *
                  </label>
                  <input
                    type="text"
                    required
                    value={formData.country}
                    onChange={(e) => setFormData({ ...formData, country: e.target.value })}
                    className="w-full px-4 py-2 rounded-lg border focus:outline-none focus:ring-2"
                    style={{ borderColor: '#E5E7EB' }}
                  />
                </div>

                {/* Marital Status and Occupation */}
                <div className="grid grid-cols-2 gap-4 mb-4">
                  <div>
                    <label className="block text-sm font-medium mb-2" style={{ color: '#2C3E50' }}>
                      Marital Status *
                    </label>
                    <select
                      required
                      value={formData.marital_status}
                      onChange={(e) => setFormData({ ...formData, marital_status: e.target.value })}
                      className="w-full px-4 py-2 rounded-lg border focus:outline-none focus:ring-2"
                      style={{ borderColor: '#E5E7EB' }}
                    >
                      <option value="SINGLE">Single</option>
                      <option value="MARRIED">Married</option>
                      <option value="DIVORCED">Divorced</option>
                      <option value="WIDOWED">Widowed</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-2" style={{ color: '#2C3E50' }}>
                      Occupation *
                    </label>
                    <select
                      required
                      value={formData.occupation}
                      onChange={(e) => setFormData({ ...formData, occupation: e.target.value })}
                      className="w-full px-4 py-2 rounded-lg border focus:outline-none focus:ring-2"
                      style={{ borderColor: '#E5E7EB' }}
                    >
                      <option value="EMPLOYED">Employed</option>
                      <option value="SELF_EMPLOYED">Self-Employed</option>
                      <option value="UNEMPLOYED">Unemployed</option>
                      <option value="RETIRED">Retired</option>
                      <option value="STUDENT">Student</option>
                    </select>
                  </div>
                </div>

                {/* Annual Income and Credit Score */}
                <div className="grid grid-cols-2 gap-4 mb-4">
                  <div>
                    <label className="block text-sm font-medium mb-2" style={{ color: '#2C3E50' }}>
                      Annual Income ($) *
                    </label>
                    <input
                      type="number"
                      required
                      value={formData.annual_income}
                      onChange={(e) => setFormData({ ...formData, annual_income: parseFloat(e.target.value) })}
                      className="w-full px-4 py-2 rounded-lg border focus:outline-none focus:ring-2"
                      style={{ borderColor: '#E5E7EB' }}
                      min="0"
                      step="1000"
                      placeholder="e.g., 50000"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-2" style={{ color: '#2C3E50' }}>
                      Credit Score *
                    </label>
                    <input
                      type="number"
                      required
                      value={formData.credit_score}
                      onChange={(e) => setFormData({ ...formData, credit_score: parseInt(e.target.value) })}
                      className="w-full px-4 py-2 rounded-lg border focus:outline-none focus:ring-2"
                      style={{ borderColor: '#E5E7EB' }}
                      min="300"
                      max="850"
                      placeholder="300-850"
                    />
                  </div>
                </div>

                {/* Years with Company */}
                <div className="mb-4">
                  <label className="block text-sm font-medium mb-2" style={{ color: '#2C3E50' }}>
                    Years with Company *
                  </label>
                  <input
                    type="number"
                    required
                    value={formData.years_with_company}
                    onChange={(e) => setFormData({ ...formData, years_with_company: parseInt(e.target.value) })}
                    className="w-full px-4 py-2 rounded-lg border focus:outline-none focus:ring-2"
                    style={{ borderColor: '#E5E7EB' }}
                    min="0"
                    max="100"
                    placeholder="e.g., 5"
                  />
                </div>

                {/* Active Status */}
                <div className="mb-6">
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={formData.is_active}
                      onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                      className="w-4 h-4 rounded"
                      style={{ accentColor: '#FF6B4A' }}
                    />
                    <span style={{ color: '#2C3E50', fontWeight: 500 }}>Active Policyholder</span>
                  </label>
                </div>

                {/* Action Buttons */}
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
                    onClick={handleSubmit}
                    className="px-6 py-2 rounded-lg text-white font-medium transition-colors"
                    style={{ backgroundColor: '#FF6B4A' }}
                    onMouseEnter={(e) => {
                      e.target.style.backgroundColor = '#E55A3A';
                    }}
                    onMouseLeave={(e) => {
                      e.target.style.backgroundColor = '#FF6B4A';
                    }}
                  >
                    {editingId ? 'Update' : 'Create'}
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}