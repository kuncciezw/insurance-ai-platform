import { useState, useEffect } from 'react';
import { X } from 'lucide-react';
import { api } from '../services/api';

export default function AddEditClaimModal({ isOpen, onClose, onSuccess, editingClaim = null }) {
  const [policies, setPolicies] = useState([]);
  const [formData, setFormData] = useState({
    claim_number: '',
    policy: '',
    policyholder: '',
    vehicle: '',
    claim_type: 'ACCIDENT',
    claim_status: 'SUBMITTED',
    severity: 'MINOR',
    incident_date: '',
    incident_location: '',
    incident_description: '',
    police_report_filed: false,
    police_report_number: '',
    witnesses_present: false,
    number_of_witnesses: 0,
    number_of_vehicles_involved: 1,
    number_of_injuries: 0,
    third_party_involved: false,
    claimed_amount: '',
    approved_amount: '',
    paid_amount: '',
  });

  useEffect(() => {
    if (isOpen) {
      fetchPolicies();
      if (editingClaim) {
        loadClaimData(editingClaim);
      } else {
        resetForm();
      }
    }
  }, [isOpen, editingClaim]);

  const fetchPolicies = async () => {
    try {
      const data = await api.getPolicies();
      setPolicies(data.results || data);
    } catch (err) {
      console.error('Failed to fetch policies:', err);
    }
  };

  const loadClaimData = (claim) => {
    setFormData({
      claim_number: claim.claim_number || '',
      policy: claim.policy,
      policyholder: claim.policyholder,
      vehicle: claim.vehicle,
      claim_type: claim.claim_type || 'ACCIDENT',
      claim_status: claim.claim_status || 'SUBMITTED',
      severity: claim.severity || 'MINOR',
      incident_date: claim.incident_date ? claim.incident_date.split('T')[0] : '',
      incident_location: claim.incident_location || '',
      incident_description: claim.incident_description || '',
      police_report_filed: claim.police_report_filed || false,
      police_report_number: claim.police_report_number || '',
      witnesses_present: claim.witnesses_present || false,
      number_of_witnesses: claim.number_of_witnesses || 0,
      number_of_vehicles_involved: claim.number_of_vehicles_involved || 1,
      number_of_injuries: claim.number_of_injuries || 0,
      third_party_involved: claim.third_party_involved || false,
      claimed_amount: claim.claimed_amount || '',
      approved_amount: claim.approved_amount || '',
      paid_amount: claim.paid_amount || '',
    });
  };

  const resetForm = () => {
    setFormData({
      claim_number: '',
      policy: '',
      policyholder: '',
      vehicle: '',
      claim_type: 'ACCIDENT',
      claim_status: 'SUBMITTED',
      severity: 'MINOR',
      incident_date: '',
      incident_location: '',
      incident_description: '',
      police_report_filed: false,
      police_report_number: '',
      witnesses_present: false,
      number_of_witnesses: 0,
      number_of_vehicles_involved: 1,
      number_of_injuries: 0,
      third_party_involved: false,
      claimed_amount: '',
      approved_amount: '',
      paid_amount: '',
    });
  };

  const handlePolicyChange = async (policyId) => {
    if (!policyId) {
      setFormData({
        ...formData,
        policy: '',
        policyholder: '',
        vehicle: '',
      });
      return;
    }

    try {
      const policyDetails = await api.getPolicy(policyId);
      console.log('📋 Selected Policy Details:', policyDetails);
      
      setFormData({
        ...formData,
        policy: policyId,
        policyholder: policyDetails.policyholder,
        vehicle: policyDetails.vehicle,
      });
      
      console.log('✅ Auto-filled policyholder:', policyDetails.policyholder);
      console.log('✅ Auto-filled vehicle:', policyDetails.vehicle);
    } catch (err) {
      console.error('Failed to fetch policy details:', err);
      const selectedPolicy = policies.find(p => p.id === policyId);
      if (selectedPolicy) {
        setFormData({
          ...formData,
          policy: policyId,
          policyholder: selectedPolicy.policyholder,
          vehicle: selectedPolicy.vehicle,
        });
      }
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const submitData = {
        policy: formData.policy,
        policyholder: formData.policyholder,
        vehicle: formData.vehicle,
        claim_type: formData.claim_type,
        claim_status: formData.claim_status || 'SUBMITTED',
        severity: formData.severity,
        incident_date: formData.incident_date,
        incident_location: formData.incident_location,
        incident_description: formData.incident_description,
        police_report_filed: formData.police_report_filed,
        police_report_number: formData.police_report_number || '',
        witnesses_present: formData.witnesses_present,
        number_of_witnesses: formData.number_of_witnesses,
        number_of_vehicles_involved: formData.number_of_vehicles_involved,
        number_of_injuries: formData.number_of_injuries,
        third_party_involved: formData.third_party_involved,
        claimed_amount: formData.claimed_amount,
        approved_amount: formData.approved_amount || '0.00',
        paid_amount: formData.paid_amount || '0.00',
      };

      // Generate a short claim number (max 20 chars): CLM-XXXXXXXXXX
      submitData.claim_number = editingClaim 
        ? formData.claim_number 
        : `CLM-${Date.now().toString().slice(-10)}`;

      console.log('📤 Submitting claim data:', submitData);

      if (editingClaim) {
        await api.updateClaim(editingClaim.id, submitData);
      } else {
        await api.createClaim(submitData);
      }
      
      onSuccess();
      onClose();
    } catch (err) {
      console.error('Failed to save claim:', err);
      alert('Failed to save claim: ' + (err.message || 'Unknown error'));
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6 border-b" style={{ borderColor: '#E5E7EB' }}>
          <div className="flex items-center justify-between">
            <h3 className="text-2xl font-bold" style={{ color: '#2C3E50' }}>
              {editingClaim ? 'Edit Claim' : 'Add Claim'}
            </h3>
            <button
              onClick={onClose}
              className="p-2 rounded-lg transition-colors"
              style={{ backgroundColor: '#F8F9FA', color: '#7F8C8D' }}
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="p-6">
          {/* Policy Selection */}
          <div className="mb-4">
            <label className="block text-sm font-medium mb-2" style={{ color: '#2C3E50' }}>
              Policy *
            </label>
            <select
              required
              value={formData.policy}
              onChange={(e) => handlePolicyChange(e.target.value)}
              className="w-full px-4 py-2 rounded-lg border focus:outline-none focus:ring-2"
              style={{ borderColor: '#E5E7EB' }}
            >
              <option value="">Select Policy</option>
              {policies.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.policy_number} - {p.policyholder_name || 'Unknown'}
                </option>
              ))}
            </select>
            {formData.policy && formData.policyholder && formData.vehicle && (
              <p className="mt-2 text-xs" style={{ color: '#10B981' }}>
              </p>
            )}
          </div>

          {/* Basic Claim Information */}
          <div className="grid grid-cols-3 gap-4 mb-4">
            <div>
              <label className="block text-sm font-medium mb-2" style={{ color: '#2C3E50' }}>
                Claim Type *
              </label>
              <select
                required
                value={formData.claim_type}
                onChange={(e) => setFormData({ ...formData, claim_type: e.target.value })}
                className="w-full px-4 py-2 rounded-lg border focus:outline-none focus:ring-2"
                style={{ borderColor: '#E5E7EB' }}
              >
                <option value="ACCIDENT">Accident</option>
                <option value="THEFT">Theft</option>
                <option value="VANDALISM">Vandalism</option>
                <option value="NATURAL_DISASTER">Natural Disaster</option>
                <option value="FIRE">Fire</option>
                <option value="OTHER">Other</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium mb-2" style={{ color: '#2C3E50' }}>
                Severity *
              </label>
              <select
                required
                value={formData.severity}
                onChange={(e) => setFormData({ ...formData, severity: e.target.value })}
                className="w-full px-4 py-2 rounded-lg border focus:outline-none focus:ring-2"
                style={{ borderColor: '#E5E7EB' }}
              >
                <option value="MINOR">Minor</option>
                <option value="MODERATE">Moderate</option>
                <option value="MAJOR">Major</option>
                <option value="TOTAL_LOSS">Total Loss</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium mb-2" style={{ color: '#2C3E50' }}>
                Status *
              </label>
              <select
                required
                value={formData.claim_status}
                onChange={(e) => setFormData({ ...formData, claim_status: e.target.value })}
                className="w-full px-4 py-2 rounded-lg border focus:outline-none focus:ring-2"
                style={{ borderColor: '#E5E7EB' }}
              >
                <option value="SUBMITTED">Submitted</option>
                <option value="UNDER_REVIEW">Under Review</option>
                <option value="APPROVED">Approved</option>
                <option value="REJECTED">Rejected</option>
                <option value="PAID">Paid</option>
                <option value="CLOSED">Closed</option>
              </select>
            </div>
          </div>

          {/* Incident Details */}
          <div className="grid grid-cols-2 gap-4 mb-4">
            <div>
              <label className="block text-sm font-medium mb-2" style={{ color: '#2C3E50' }}>
                Incident Date *
              </label>
              <input
                type="date"
                required
                value={formData.incident_date}
                onChange={(e) => setFormData({ ...formData, incident_date: e.target.value })}
                className="w-full px-4 py-2 rounded-lg border focus:outline-none focus:ring-2"
                style={{ borderColor: '#E5E7EB' }}
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-2" style={{ color: '#2C3E50' }}>
                Incident Location *
              </label>
              <input
                type="text"
                required
                value={formData.incident_location}
                onChange={(e) => setFormData({ ...formData, incident_location: e.target.value })}
                className="w-full px-4 py-2 rounded-lg border focus:outline-none focus:ring-2"
                style={{ borderColor: '#E5E7EB' }}
                placeholder="e.g., Harare"
              />
            </div>
          </div>

          <div className="mb-4">
            <label className="block text-sm font-medium mb-2" style={{ color: '#2C3E50' }}>
              Incident Description *
            </label>
            <textarea
              required
              value={formData.incident_description}
              onChange={(e) => setFormData({ ...formData, incident_description: e.target.value })}
              className="w-full px-4 py-2 rounded-lg border focus:outline-none focus:ring-2"
              style={{ borderColor: '#E5E7EB' }}
              rows="3"
              placeholder="Describe the incident..."
            />
          </div>

          {/* Police Report Details */}
          <div className="grid grid-cols-2 gap-4 mb-4">
            <div>
              <label className="flex items-center gap-2 text-sm font-medium" style={{ color: '#2C3E50' }}>
                <input
                  type="checkbox"
                  checked={formData.police_report_filed}
                  onChange={(e) => setFormData({ ...formData, police_report_filed: e.target.checked })}
                  className="rounded"
                />
                Police Report Filed
              </label>
            </div>
            {formData.police_report_filed && (
              <div>
                <label className="block text-sm font-medium mb-2" style={{ color: '#2C3E50' }}>
                  Police Report Number
                </label>
                <input
                  type="text"
                  value={formData.police_report_number}
                  onChange={(e) => setFormData({ ...formData, police_report_number: e.target.value })}
                  className="w-full px-4 py-2 rounded-lg border focus:outline-none focus:ring-2"
                  style={{ borderColor: '#E5E7EB' }}
                  placeholder="PR-12345"
                />
              </div>
            )}
          </div>

          {/* Witness Information */}
          <div className="grid grid-cols-2 gap-4 mb-4">
            <div>
              <label className="flex items-center gap-2 text-sm font-medium" style={{ color: '#2C3E50' }}>
                <input
                  type="checkbox"
                  checked={formData.witnesses_present}
                  onChange={(e) => setFormData({ ...formData, witnesses_present: e.target.checked })}
                  className="rounded"
                />
                Witnesses Present
              </label>
            </div>
            {formData.witnesses_present && (
              <div>
                <label className="block text-sm font-medium mb-2" style={{ color: '#2C3E50' }}>
                  Number of Witnesses
                </label>
                <input
                  type="number"
                  min="0"
                  value={formData.number_of_witnesses}
                  onChange={(e) => setFormData({ ...formData, number_of_witnesses: parseInt(e.target.value) || 0 })}
                  className="w-full px-4 py-2 rounded-lg border focus:outline-none focus:ring-2"
                  style={{ borderColor: '#E5E7EB' }}
                />
              </div>
            )}
          </div>

          {/* Incident Details */}
          <div className="grid grid-cols-3 gap-4 mb-4">
            <div>
              <label className="block text-sm font-medium mb-2" style={{ color: '#2C3E50' }}>
                Vehicles Involved
              </label>
              <input
                type="number"
                min="1"
                value={formData.number_of_vehicles_involved}
                onChange={(e) => setFormData({ ...formData, number_of_vehicles_involved: parseInt(e.target.value) || 1 })}
                className="w-full px-4 py-2 rounded-lg border focus:outline-none focus:ring-2"
                style={{ borderColor: '#E5E7EB' }}
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-2" style={{ color: '#2C3E50' }}>
                Number of Injuries
              </label>
              <input
                type="number"
                min="0"
                value={formData.number_of_injuries}
                onChange={(e) => setFormData({ ...formData, number_of_injuries: parseInt(e.target.value) || 0 })}
                className="w-full px-4 py-2 rounded-lg border focus:outline-none focus:ring-2"
                style={{ borderColor: '#E5E7EB' }}
              />
            </div>
            <div className="flex items-center">
              <label className="flex items-center gap-2 text-sm font-medium" style={{ color: '#2C3E50' }}>
                <input
                  type="checkbox"
                  checked={formData.third_party_involved}
                  onChange={(e) => setFormData({ ...formData, third_party_involved: e.target.checked })}
                  className="rounded"
                />
                Third Party Involved
              </label>
            </div>
          </div>

          {/* Financial Details */}
          <div className="grid grid-cols-3 gap-4 mb-6">
            <div>
              <label className="block text-sm font-medium mb-2" style={{ color: '#2C3E50' }}>
                Claimed Amount ($) *
              </label>
              <input
                type="number"
                step="0.01"
                min="0"
                required
                value={formData.claimed_amount}
                onChange={(e) => setFormData({ ...formData, claimed_amount: e.target.value })}
                className="w-full px-4 py-2 rounded-lg border focus:outline-none focus:ring-2"
                style={{ borderColor: '#E5E7EB' }}
                placeholder="0.00"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-2" style={{ color: '#2C3E50' }}>
                Approved Amount ($)
              </label>
              <input
                type="number"
                step="0.01"
                min="0"
                value={formData.approved_amount}
                onChange={(e) => setFormData({ ...formData, approved_amount: e.target.value })}
                className="w-full px-4 py-2 rounded-lg border focus:outline-none focus:ring-2"
                style={{ borderColor: '#E5E7EB' }}
                placeholder="0.00"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-2" style={{ color: '#2C3E50' }}>
                Paid Amount ($)
              </label>
              <input
                type="number"
                step="0.01"
                min="0"
                value={formData.paid_amount}
                onChange={(e) => setFormData({ ...formData, paid_amount: e.target.value })}
                className="w-full px-4 py-2 rounded-lg border focus:outline-none focus:ring-2"
                style={{ borderColor: '#E5E7EB' }}
                placeholder="0.00"
              />
            </div>
          </div>

          <div className="flex justify-end gap-4">
            <button
              type="button"
              onClick={onClose}
              className="px-6 py-2 rounded-lg font-medium transition-colors"
              style={{ backgroundColor: '#F8F9FA', color: '#7F8C8D' }}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-6 py-2 rounded-lg text-white font-medium transition-colors"
              style={{ backgroundColor: '#FF6B4A' }}
              onMouseEnter={(e) => {
                e.target.style.backgroundColor = '#E55A3A';
              }}
              onMouseLeave={(e) => {
                e.target.style.backgroundColor = '#FF6B4A';
              }}
            >
              {editingClaim ? 'Update' : 'Create'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}