import { useState } from 'react';
import { api } from '../services/api';
import Sidebar from './Sidebar';
import {
  DollarSign,
  TrendingUp,
  Calculator,
} from 'lucide-react';

export default function ClaimsEstimator() {
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  const [formData, setFormData] = useState({
    vehicle_age_years: 5,
    vehicle_value: 15000,
    incident_type: 'Collision',
    incident_severity: 'Major Damage',
    repair_complexity: 'Medium',
    parts_availability: 'Available',
    labor_hours_estimate: 20,
    claimed_amount: 5000,
  });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');
    setResult(null);

    try {
      const data = await api.estimateClaimDirect(formData);
      setResult(data);
    } catch (err) {
      console.error('Claim estimation failed:', err);
      setError('Failed to estimate claim: ' + (err.message || 'Unknown error'));
    } finally {
      setIsLoading(false);
    }
  };

  const getEstimateAccuracy = (claimed, estimated) => {
    const diff = Math.abs(claimed - estimated);
    const percentDiff = (diff / claimed) * 100;
    if (percentDiff <= 10) return { level: 'High Accuracy', color: '#10B981', bg: '#D1FAE5' };
    if (percentDiff <= 25) return { level: 'Medium Accuracy', color: '#F59E0B', bg: '#FEF3C7' };
    return { level: 'Low Accuracy', color: '#EF4444', bg: '#FEE2E2' };
  };

  return (
    <div className="flex h-screen overflow-hidden" style={{ backgroundColor: '#F8F9FA' }}> 
      {/* Use the Sidebar component */}
      <Sidebar />

      {/* Main Content */}
      <div className="flex-1 p-8 overflow-y-auto">
        <div className="mb-8">
          <h2 className="text-3xl font-bold" style={{ color: '#2C3E50' }}>
            AI Claims Estimator
          </h2>
          <p className="mt-2" style={{ color: '#7F8C8D' }}>
            Estimate claim amounts using machine learning
          </p>
        </div>

        {error && (
          <div className="mb-6 p-4 rounded-lg" style={{ backgroundColor: '#FEE2E2', color: '#DC2626' }}>
            {error}
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Input Form */}
          <div className="lg:col-span-2">
            <div className="bg-white rounded-lg shadow-lg p-6">
              <div className="flex items-center mb-6">
                <div
                  className="w-12 h-12 rounded-full flex items-center justify-center"
                  style={{ backgroundColor: '#FEF3C7' }}
                >
                  <DollarSign className="w-6 h-6" style={{ color: '#F59E0B' }} />
                </div>
                <h3 className="ml-4 text-xl font-bold" style={{ color: '#2C3E50' }}>
                  Claim Information
                </h3>
              </div>

              <div>
                <div className="mb-6">
                  <h4 className="font-semibold mb-3" style={{ color: '#2C3E50' }}>
                    Vehicle Details
                  </h4>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium mb-2" style={{ color: '#2C3E50' }}>
                        Vehicle Age (years)
                      </label>
                      <input
                        type="number"
                        value={formData.vehicle_age_years}
                        onChange={(e) => setFormData({ ...formData, vehicle_age_years: parseInt(e.target.value) })}
                        className="w-full px-4 py-2 rounded-lg border focus:outline-none focus:ring-2"
                        style={{ borderColor: '#E5E7EB' }}
                        min="0"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium mb-2" style={{ color: '#2C3E50' }}>
                        Vehicle Value ($)
                      </label>
                      <input
                        type="number"
                        step="0.01"
                        value={formData.vehicle_value}
                        onChange={(e) => setFormData({ ...formData, vehicle_value: parseFloat(e.target.value) })}
                        className="w-full px-4 py-2 rounded-lg border focus:outline-none focus:ring-2"
                        style={{ borderColor: '#E5E7EB' }}
                        min="0"
                      />
                    </div>
                  </div>
                </div>

                <div className="mb-6">
                  <h4 className="font-semibold mb-3" style={{ color: '#2C3E50' }}>
                    Incident Details
                  </h4>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium mb-2" style={{ color: '#2C3E50' }}>
                        Incident Type
                      </label>
                      <select
                        value={formData.incident_type}
                        onChange={(e) => setFormData({ ...formData, incident_type: e.target.value })}
                        className="w-full px-4 py-2 rounded-lg border focus:outline-none focus:ring-2"
                        style={{ borderColor: '#E5E7EB' }}
                      >
                        <option value="Collision">Collision</option>
                        <option value="Theft">Theft</option>
                        <option value="Fire">Fire</option>
                        <option value="Vandalism">Vandalism</option>
                        <option value="Natural Disaster">Natural Disaster</option>
                        <option value="Other">Other</option>
                      </select>
                    </div>
                    <div>
                      <label className="block text-sm font-medium mb-2" style={{ color: '#2C3E50' }}>
                        Incident Severity
                      </label>
                      <select
                        value={formData.incident_severity}
                        onChange={(e) => setFormData({ ...formData, incident_severity: e.target.value })}
                        className="w-full px-4 py-2 rounded-lg border focus:outline-none focus:ring-2"
                        style={{ borderColor: '#E5E7EB' }}
                      >
                        <option value="Minor Damage">Minor Damage</option>
                        <option value="Major Damage">Major Damage</option>
                        <option value="Total Loss">Total Loss</option>
                        <option value="Trivial Damage">Trivial Damage</option>
                      </select>
                    </div>
                  </div>
                </div>

                <div className="mb-6">
                  <h4 className="font-semibold mb-3" style={{ color: '#2C3E50' }}>
                    Repair Information
                  </h4>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium mb-2" style={{ color: '#2C3E50' }}>
                        Repair Complexity
                      </label>
                      <select
                        value={formData.repair_complexity}
                        onChange={(e) => setFormData({ ...formData, repair_complexity: e.target.value })}
                        className="w-full px-4 py-2 rounded-lg border focus:outline-none focus:ring-2"
                        style={{ borderColor: '#E5E7EB' }}
                      >
                        <option value="Low">Low</option>
                        <option value="Medium">Medium</option>
                        <option value="High">High</option>
                      </select>
                    </div>
                    <div>
                      <label className="block text-sm font-medium mb-2" style={{ color: '#2C3E50' }}>
                        Parts Availability
                      </label>
                      <select
                        value={formData.parts_availability}
                        onChange={(e) => setFormData({ ...formData, parts_availability: e.target.value })}
                        className="w-full px-4 py-2 rounded-lg border focus:outline-none focus:ring-2"
                        style={{ borderColor: '#E5E7EB' }}
                      >
                        <option value="Available">Available</option>
                        <option value="Limited">Limited</option>
                        <option value="Rare">Rare</option>
                      </select>
                    </div>
                    <div>
                      <label className="block text-sm font-medium mb-2" style={{ color: '#2C3E50' }}>
                        Labor Hours Estimate
                      </label>
                      <input
                        type="number"
                        value={formData.labor_hours_estimate}
                        onChange={(e) => setFormData({ ...formData, labor_hours_estimate: parseInt(e.target.value) })}
                        className="w-full px-4 py-2 rounded-lg border focus:outline-none focus:ring-2"
                        style={{ borderColor: '#E5E7EB' }}
                        min="0"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium mb-2" style={{ color: '#2C3E50' }}>
                        Claimed Amount ($)
                      </label>
                      <input
                        type="number"
                        step="0.01"
                        value={formData.claimed_amount}
                        onChange={(e) => setFormData({ ...formData, claimed_amount: parseFloat(e.target.value) })}
                        className="w-full px-4 py-2 rounded-lg border focus:outline-none focus:ring-2"
                        style={{ borderColor: '#E5E7EB' }}
                        min="0"
                      />
                    </div>
                  </div>
                </div>

                <button
                  onClick={handleSubmit}
                  disabled={isLoading}
                  className="w-full py-3 px-4 rounded-lg text-white font-medium transition-colors disabled:opacity-50"
                  style={{ backgroundColor: '#FF6B4A' }}
                  onMouseEnter={(e) => {
                    if (!isLoading) e.target.style.backgroundColor = '#E55A3A';
                  }}
                  onMouseLeave={(e) => {
                    if (!isLoading) e.target.style.backgroundColor = '#FF6B4A';
                  }}
                >
                  {isLoading ? 'Estimating...' : 'Estimate Claim Amount'}
                </button>
              </div>
            </div>
          </div>

          {/* Results Panel */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-lg shadow-lg p-6">
              <div className="flex items-center mb-6">
                <div
                  className="w-12 h-12 rounded-full flex items-center justify-center"
                  style={{ backgroundColor: '#D1FAE5' }}
                >
                  <TrendingUp className="w-6 h-6" style={{ color: '#10B981' }} />
                </div>
                <h3 className="ml-4 text-xl font-bold" style={{ color: '#2C3E50' }}>
                  Estimate Results
                </h3>
              </div>

              {!result ? (
                <div className="text-center py-12">
                  <Calculator className="w-16 h-16 mx-auto mb-4" style={{ color: '#E5E7EB' }} />
                  <p style={{ color: '#7F8C8D' }}>
                    Fill in the claim information and click "Estimate Claim Amount" to see results
                  </p>
                </div>
              ) : (
                <div>
                  {/* Estimated Amount */}
                  <div className="mb-6 p-6 rounded-lg text-center" style={{ backgroundColor: '#F8F9FA' }}>
                    <p className="text-sm mb-2" style={{ color: '#7F8C8D' }}>
                      Estimated Amount
                    </p>
                    <p className="text-4xl font-bold mb-4" style={{ color: '#2C3E50' }}>
                      ${parseFloat(result.estimated_amount).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                    </p>
                    <div
                      className="inline-block px-4 py-2 rounded-full text-sm font-medium"
                      style={{
                        backgroundColor: getEstimateAccuracy(formData.claimed_amount, result.estimated_amount).bg,
                        color: getEstimateAccuracy(formData.claimed_amount, result.estimated_amount).color,
                      }}
                    >
                      {getEstimateAccuracy(formData.claimed_amount, result.estimated_amount).level}
                    </div>
                  </div>

                  {/* Comparison */}
                  <div className="mb-6">
                    <h4 className="font-semibold mb-3" style={{ color: '#2C3E50' }}>
                      Comparison
                    </h4>
                    <div className="space-y-3">
                      <div className="flex items-center justify-between p-3 rounded-lg" style={{ backgroundColor: '#F8F9FA' }}>
                        <span className="text-sm" style={{ color: '#7F8C8D' }}>Claimed Amount</span>
                        <span className="font-bold" style={{ color: '#2C3E50' }}>
                          ${parseFloat(formData.claimed_amount).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                        </span>
                      </div>
                      <div className="flex items-center justify-between p-3 rounded-lg" style={{ backgroundColor: '#F8F9FA' }}>
                        <span className="text-sm" style={{ color: '#7F8C8D' }}>Estimated Amount</span>
                        <span className="font-bold" style={{ color: '#2C3E50' }}>
                          ${parseFloat(result.estimated_amount).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                        </span>
                      </div>
                      <div className="flex items-center justify-between p-3 rounded-lg" style={{ backgroundColor: '#F8F9FA' }}>
                        <span className="text-sm" style={{ color: '#7F8C8D' }}>Difference</span>
                        <span 
                          className="font-bold" 
                          style={{ 
                            color: Math.abs(formData.claimed_amount - result.estimated_amount) > formData.claimed_amount * 0.2 ? '#EF4444' : '#10B981' 
                          }}
                        >
                          ${Math.abs(formData.claimed_amount - result.estimated_amount).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Recommendation */}
                  <div className="p-4 rounded-lg" style={{ backgroundColor: '#EBF5FF' }}>
                    <p className="text-sm font-medium mb-2" style={{ color: '#1E3A8A' }}>
                      Recommendation
                    </p>
                    <p className="text-sm" style={{ color: '#1E40AF' }}>
                      {Math.abs(formData.claimed_amount - result.estimated_amount) > formData.claimed_amount * 0.2
                        ? 'Significant difference detected. Recommend further investigation and adjuster review.'
                        : 'Claimed amount is within reasonable range of AI estimate. Proceed with standard approval process.'}
                    </p>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}