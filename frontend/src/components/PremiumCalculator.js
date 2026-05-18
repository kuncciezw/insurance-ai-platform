import { useState } from 'react';
import Sidebar from './Sidebar';
import { Calculator, DollarSign, TrendingUp, Shield, AlertCircle, Loader2 } from 'lucide-react';
import { api } from '../services/api';
import { useCurrencyFormatter } from '../utils/currencyFormatter';

export default function PremiumCalculator() {
  const { fmtMoney } = useCurrencyFormatter();
  const [currency, setCurrency] = useState('USD');

  const [formData, setFormData] = useState({
    // Policy details
    policy_type: 'COMPREHENSIVE',
    coverage_level: 'STANDARD',
    coverage_amount: '50000',
    deductible: '500',
    
    // Customer info (minimal - only age, credit, experience)
    customer_age: '',
    customer_credit_score: '',
    customer_years_experience: '0',
    
    // Vehicle info
    vehicle_year: '',
    vehicle_make: '',
    vehicle_model: '',
    vehicle_value: '',
    vehicle_has_anti_theft: false,
    vehicle_is_modified: false,
    
    // Optional coverages
    has_roadside_assistance: false,
    has_rental_coverage: false,
    has_glass_coverage: false,
  });

  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleChange = (e) => {
    const { name, value, type } = e.target;
    if (type === 'checkbox') {
      setFormData({
        ...formData,
        [name]: e.target.checked,
      });
    } else {
      setFormData({
        ...formData,
        [name]: value,
      });
    }
  };

  const calculatePremium = async (e) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      // Convert form data to API format
      const apiData = {
        policy_type: formData.policy_type,
        coverage_level: formData.coverage_level,
        coverage_amount: parseFloat(formData.coverage_amount),
        deductible: parseFloat(formData.deductible),
        customer_age: parseInt(formData.customer_age),
        customer_credit_score: parseInt(formData.customer_credit_score),
        customer_years_experience: parseInt(formData.customer_years_experience),
        vehicle_year: parseInt(formData.vehicle_year),
        vehicle_make: formData.vehicle_make,
        vehicle_model: formData.vehicle_model,
        vehicle_value: parseFloat(formData.vehicle_value),
        vehicle_has_anti_theft: formData.vehicle_has_anti_theft,
        vehicle_is_modified: formData.vehicle_is_modified,
        has_roadside_assistance: formData.has_roadside_assistance,
        has_rental_coverage: formData.has_rental_coverage,
        has_glass_coverage: formData.has_glass_coverage,
      };

      const response = await api.calculatePremium(apiData);
      setResult(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to calculate premium');
    } finally {
      setLoading(false);
    }
  };

  const getRiskLevel = (premium) => {
    if (premium >= 2000) return { level: 'High Premium', color: '#EF4444', bg: '#FEE2E2' };
    if (premium >= 1000) return { level: 'Medium Premium', color: '#F59E0B', bg: '#FEF3C7' };
    return { level: 'Low Premium', color: '#10B981', bg: '#D1FAE5' };
  };

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar />
      
      <div className="flex-1 overflow-y-auto" style={{ backgroundColor: '#F8F9FA' }}>
        <div className="p-8">
          {/* Page Title & Currency Toggle */}
          <div className="flex items-start justify-between mb-8">
            <div className="flex items-center">
              <Calculator className="w-8 h-8 mr-3" style={{ color: '#FF6B4A' }} />
              <div>
                <h1 className="text-3xl font-bold" style={{ color: '#2C3E50' }}>
                  AI Premium Calculator
                </h1>
                <p className="mt-1" style={{ color: '#7F8C8D' }}>
                  Calculate insurance premiums using machine learning
                </p>
              </div>
            </div>
            <div className="flex items-center gap-3 mt-1">
              <span className="text-xs font-semibold uppercase tracking-wider" style={{ color: '#7F8C8D' }}>Currency</span>
              <div className="flex gap-1 p-1 rounded-xl" style={{ backgroundColor: '#E5E7EB' }}>
                {['USD', 'ZWG'].map((c) => (
                  <button key={c} onClick={() => setCurrency(c)}
                    className="px-4 py-1.5 rounded-lg text-sm font-bold transition-all duration-200"
                    style={{ backgroundColor: currency === c ? '#FF6B4A' : 'transparent', color: currency === c ? '#FFFFFF' : '#7F8C8D', boxShadow: currency === c ? '0 2px 6px rgba(255,107,74,0.35)' : 'none' }}>
                    {c}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Error Message */}
          {error && (
            <div className="mb-6 p-4 rounded-lg" style={{ backgroundColor: '#FEE2E2', color: '#DC2626' }}>
              {error}
            </div>
          )}

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Input Form */}
            <div className="lg:col-span-2">
              <div className="bg-white rounded-xl shadow-sm p-6">
                <div className="flex items-center mb-6">
                  <div
                    className="w-12 h-12 rounded-full flex items-center justify-center"
                    style={{ backgroundColor: '#EBF5FF' }}
                  >
                    <Calculator className="w-6 h-6" style={{ color: '#3B82F6' }} />
                  </div>
                  <h3 className="ml-4 text-xl font-bold" style={{ color: '#2C3E50' }}>
                    Policy Information
                  </h3>
                </div>

                <form onSubmit={calculatePremium}>
                  {/* Customer & Policy Details */}
                  <div className="mb-6">
                    <h4 className="font-semibold mb-4" style={{ color: '#2C3E50' }}>
                      Customer & Policy Details
                    </h4>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium mb-2" style={{ color: '#2C3E50' }}>
                          Age *
                        </label>
                        <input
                          type="number"
                          name="customer_age"
                          value={formData.customer_age}
                          onChange={handleChange}
                          className="w-full px-4 py-2 rounded-lg border focus:outline-none focus:ring-2"
                          style={{ borderColor: '#E0E0E0' }}
                          placeholder="30"
                          min="18"
                          max="100"
                          required
                        />
                      </div>

                      <div>
                        <label className="block text-sm font-medium mb-2" style={{ color: '#2C3E50' }}>
                          Credit Score *
                        </label>
                        <input
                          type="number"
                          name="customer_credit_score"
                          value={formData.customer_credit_score}
                          onChange={handleChange}
                          className="w-full px-4 py-2 rounded-lg border focus:outline-none focus:ring-2"
                          style={{ borderColor: '#E0E0E0' }}
                          placeholder="700"
                          min="300"
                          max="850"
                          required
                        />
                      </div>

                      <div>
                        <label className="block text-sm font-medium mb-2" style={{ color: '#2C3E50' }}>
                          Years of Driving Experience
                        </label>
                        <input
                          type="number"
                          name="customer_years_experience"
                          value={formData.customer_years_experience}
                          onChange={handleChange}
                          className="w-full px-4 py-2 rounded-lg border focus:outline-none focus:ring-2"
                          style={{ borderColor: '#E0E0E0' }}
                          placeholder="5"
                          min="0"
                        />
                      </div>

                      <div>
                        <label className="block text-sm font-medium mb-2" style={{ color: '#2C3E50' }}>
                          Policy Type *
                        </label>
                        <select
                          name="policy_type"
                          value={formData.policy_type}
                          onChange={handleChange}
                          className="w-full px-4 py-2 rounded-lg border focus:outline-none focus:ring-2"
                          style={{ borderColor: '#E0E0E0' }}
                          required
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
                          name="coverage_level"
                          value={formData.coverage_level}
                          onChange={handleChange}
                          className="w-full px-4 py-2 rounded-lg border focus:outline-none focus:ring-2"
                          style={{ borderColor: '#E0E0E0' }}
                          required
                        >
                          <option value="BASIC">Basic</option>
                          <option value="STANDARD">Standard</option>
                          <option value="PREMIUM">Premium</option>
                        </select>
                      </div>

                      <div>
                        <label className="block text-sm font-medium mb-2" style={{ color: '#2C3E50' }}>
                          Coverage Amount ({currency}) *
                        </label>
                        <input
                          type="number"
                          name="coverage_amount"
                          value={formData.coverage_amount}
                          onChange={handleChange}
                          className="w-full px-4 py-2 rounded-lg border focus:outline-none focus:ring-2"
                          style={{ borderColor: '#E0E0E0' }}
                          placeholder="50000"
                          min="1000"
                          required
                        />
                      </div>

                      <div>
                        <label className="block text-sm font-medium mb-2" style={{ color: '#2C3E50' }}>
                          Deductible ({currency}) *
                        </label>
                        <input
                          type="number"
                          name="deductible"
                          value={formData.deductible}
                          onChange={handleChange}
                          className="w-full px-4 py-2 rounded-lg border focus:outline-none focus:ring-2"
                          style={{ borderColor: '#E0E0E0' }}
                          placeholder="500"
                          min="0"
                          required
                        />
                      </div>
                    </div>
                  </div>

                  {/* Vehicle Information */}
                  <div className="mb-6">
                    <h4 className="font-semibold mb-4" style={{ color: '#2C3E50' }}>
                      Vehicle Information
                    </h4>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium mb-2" style={{ color: '#2C3E50' }}>
                          Make *
                        </label>
                        <input
                          type="text"
                          name="vehicle_make"
                          value={formData.vehicle_make}
                          onChange={handleChange}
                          className="w-full px-4 py-2 rounded-lg border focus:outline-none focus:ring-2"
                          style={{ borderColor: '#E0E0E0' }}
                          placeholder="Toyota"
                          required
                        />
                      </div>

                      <div>
                        <label className="block text-sm font-medium mb-2" style={{ color: '#2C3E50' }}>
                          Model *
                        </label>
                        <input
                          type="text"
                          name="vehicle_model"
                          value={formData.vehicle_model}
                          onChange={handleChange}
                          className="w-full px-4 py-2 rounded-lg border focus:outline-none focus:ring-2"
                          style={{ borderColor: '#E0E0E0' }}
                          placeholder="Corolla"
                          required
                        />
                      </div>

                      <div>
                        <label className="block text-sm font-medium mb-2" style={{ color: '#2C3E50' }}>
                          Year *
                        </label>
                        <input
                          type="number"
                          name="vehicle_year"
                          value={formData.vehicle_year}
                          onChange={handleChange}
                          className="w-full px-4 py-2 rounded-lg border focus:outline-none focus:ring-2"
                          style={{ borderColor: '#E0E0E0' }}
                          placeholder="2020"
                          min="1990"
                          max="2026"
                          required
                        />
                      </div>

                      <div>
                        <label className="block text-sm font-medium mb-2" style={{ color: '#2C3E50' }}>
                          Market Value ({currency}) *
                        </label>
                        <input
                          type="number"
                          name="vehicle_value"
                          value={formData.vehicle_value}
                          onChange={handleChange}
                          className="w-full px-4 py-2 rounded-lg border focus:outline-none focus:ring-2"
                          style={{ borderColor: '#E0E0E0' }}
                          placeholder="15000"
                          min="100"
                          required
                        />
                      </div>
                    </div>

                    <div className="mt-4">
                      <label className="block text-sm font-medium mb-2" style={{ color: '#2C3E50' }}>
                        Safety Features
                      </label>
                      <div className="space-y-2">
                        <label className="flex items-center">
                          <input
                            type="checkbox"
                            name="vehicle_has_anti_theft"
                            checked={formData.vehicle_has_anti_theft}
                            onChange={handleChange}
                            className="mr-2 w-4 h-4"
                          />
                          <span className="text-sm" style={{ color: '#2C3E50' }}>Anti-theft System (5% discount)</span>
                        </label>
                        <label className="flex items-center">
                          <input
                            type="checkbox"
                            name="vehicle_is_modified"
                            checked={formData.vehicle_is_modified}
                            onChange={handleChange}
                            className="mr-2 w-4 h-4"
                          />
                          <span className="text-sm" style={{ color: '#2C3E50' }}>Modified Vehicle</span>
                        </label>
                      </div>
                    </div>
                  </div>

                  {/* Optional Coverages */}
                  <div className="mb-6">
                    <h4 className="font-semibold mb-4" style={{ color: '#2C3E50' }}>
                      Optional Coverages
                    </h4>
                    <div className="space-y-2">
                      <label className="flex items-center">
                        <input
                          type="checkbox"
                          name="has_roadside_assistance"
                          checked={formData.has_roadside_assistance}
                          onChange={handleChange}
                          className="mr-2 w-4 h-4"
                        />
                        <span className="text-sm" style={{ color: '#2C3E50' }}>Roadside Assistance (+{fmtMoney(50, currency)}/year)</span>
                      </label>
                      <label className="flex items-center">
                        <input
                          type="checkbox"
                          name="has_rental_coverage"
                          checked={formData.has_rental_coverage}
                          onChange={handleChange}
                          className="mr-2 w-4 h-4"
                        />
                        <span className="text-sm" style={{ color: '#2C3E50' }}>Rental Coverage (+{fmtMoney(75, currency)}/year)</span>
                      </label>
                      <label className="flex items-center">
                        <input
                          type="checkbox"
                          name="has_glass_coverage"
                          checked={formData.has_glass_coverage}
                          onChange={handleChange}
                          className="mr-2 w-4 h-4"
                        />
                        <span className="text-sm" style={{ color: '#2C3E50' }}>Glass Coverage (+{fmtMoney(30, currency)}/year)</span>
                      </label>
                    </div>
                  </div>

                  {/* Submit Button */}
                  <button
                    type="submit"
                    disabled={loading}
                    className="w-full py-3 px-4 rounded-lg text-white font-medium transition-colors disabled:opacity-50 inline-flex items-center justify-center"
                    style={{ backgroundColor: '#FF6B4A' }}
                    onMouseEnter={(e) => {
                      if (!loading) e.currentTarget.style.backgroundColor = '#E55A3A';
                    }}
                    onMouseLeave={(e) => {
                      if (!loading) e.currentTarget.style.backgroundColor = '#FF6B4A';
                    }}
                  >
                    {loading ? (
                      <>
                        <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                        Calculating...
                      </>
                    ) : (
                      'Calculate Premium'
                    )}
                  </button>
                </form>
              </div>
            </div>

            {/* Results Panel */}
            <div className="lg:col-span-1">
              <div className="bg-white rounded-xl shadow-sm p-6">
                <div className="flex items-center mb-6">
                  <div
                    className="w-12 h-12 rounded-full flex items-center justify-center"
                    style={{ backgroundColor: '#D1FAE5' }}
                  >
                    <TrendingUp className="w-6 h-6" style={{ color: '#10B981' }} />
                  </div>
                  <h3 className="ml-4 text-xl font-bold" style={{ color: '#2C3E50' }}>
                    Premium Quote
                  </h3>
                </div>

                {!result ? (
                  <div className="text-center py-12">
                    <DollarSign className="w-16 h-16 mx-auto mb-4" style={{ color: '#E5E7EB' }} />
                    <p style={{ color: '#7F8C8D' }}>
                      Fill in the policy information and click "Calculate Premium" to see results
                    </p>
                  </div>
                ) : (
                  <div>
                    {/* Premium Amount */}
                    <div className="mb-6 p-6 rounded-lg text-center" style={{ backgroundColor: '#F8F9FA' }}>
                      <p className="text-sm mb-2" style={{ color: '#7F8C8D' }}>
                        Annual Premium
                      </p>
                      <p className="text-4xl font-bold mb-4" style={{ color: '#2C3E50' }}>
                        {fmtMoney(result.final_premium, currency)}
                      </p>
                      <div
                        className="inline-block px-4 py-2 rounded-full text-sm font-medium"
                        style={{
                          backgroundColor: getRiskLevel(result.final_premium).bg,
                          color: getRiskLevel(result.final_premium).color,
                        }}
                      >
                        {getRiskLevel(result.final_premium).level}
                      </div>
                    </div>

                    {/* Breakdown */}
                    <div className="mb-6">
                      <h4 className="font-semibold mb-3" style={{ color: '#2C3E50' }}>
                        Premium Breakdown
                      </h4>
                      <div className="space-y-3">
                        <div className="flex justify-between p-3 rounded-lg" style={{ backgroundColor: '#F8F9FA' }}>
                          <span className="text-sm" style={{ color: '#7F8C8D' }}>Base Premium (ML)</span>
                          <span className="font-medium" style={{ color: '#2C3E50' }}>
                            {fmtMoney(result.ml_predicted_premium, currency)}
                          </span>
                        </div>
                        {result.risk_adjustment > 0 && (
                          <div className="flex justify-between p-3 rounded-lg" style={{ backgroundColor: '#FEE2E2' }}>
                            <span className="text-sm" style={{ color: '#7F8C8D' }}>Risk Adjustment</span>
                            <span className="font-medium" style={{ color: '#DC3545' }}>
                              +{fmtMoney(result.risk_adjustment, currency)}
                            </span>
                          </div>
                        )}
                        {result.discount_amount > 0 && (
                          <div className="flex justify-between p-3 rounded-lg" style={{ backgroundColor: '#D1FAE5' }}>
                            <span className="text-sm" style={{ color: '#7F8C8D' }}>Discounts</span>
                            <span className="font-medium" style={{ color: '#10B981' }}>
                              -{fmtMoney(result.discount_amount, currency)}
                            </span>
                          </div>
                        )}
                      </div>
                    </div>

                    {/* Payment Options */}
                    <div className="mb-6">
                      <h4 className="font-semibold mb-3" style={{ color: '#2C3E50' }}>
                        Payment Options
                      </h4>
                      <div className="space-y-3">
                        <div className="flex items-center justify-between p-3 rounded-lg" style={{ backgroundColor: '#F8F9FA' }}>
                          <span className="text-sm" style={{ color: '#7F8C8D' }}>Monthly</span>
                          <span className="font-bold" style={{ color: '#2C3E50' }}>
                            {fmtMoney(result.final_premium / 12, currency)}
                          </span>
                        </div>
                        <div className="flex items-center justify-between p-3 rounded-lg" style={{ backgroundColor: '#F8F9FA' }}>
                          <span className="text-sm" style={{ color: '#7F8C8D' }}>Quarterly</span>
                          <span className="font-bold" style={{ color: '#2C3E50' }}>
                            {fmtMoney(result.final_premium / 4, currency)}
                          </span>
                        </div>
                        <div className="flex items-center justify-between p-3 rounded-lg" style={{ backgroundColor: '#F8F9FA' }}>
                          <span className="text-sm" style={{ color: '#7F8C8D' }}>Semi-Annual</span>
                          <span className="font-bold" style={{ color: '#2C3E50' }}>
                            {fmtMoney(result.final_premium / 2, currency)}
                          </span>
                        </div>
                      </div>
                    </div>

                    {/* Risk Factors */}
                    {result.risk_factors && Object.keys(result.risk_factors).length > 0 && (
                      <div className="mb-6">
                        <h4 className="font-semibold mb-3 flex items-center" style={{ color: '#2C3E50' }}>
                          <AlertCircle className="w-5 h-5 mr-2" style={{ color: '#FF6B4A' }} />
                          Risk Factors
                        </h4>
                        <div className="space-y-2">
                          {Object.entries(result.risk_factors).map(([key, value]) => (
                            <div key={key} className="flex items-start p-3 rounded-lg" style={{ backgroundColor: '#F8F9FA' }}>
                              <div className="w-2 h-2 rounded-full mt-2 mr-3" style={{ backgroundColor: '#FF6B4A' }} />
                              <div>
                                <span className="text-sm font-medium" style={{ color: '#2C3E50' }}>
                                  {value.reason || value}
                                </span>
                                {value.impact && (
                                  <span className="text-xs ml-2" style={{ color: '#DC3545' }}>
                                    {value.impact}
                                  </span>
                                )}
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Discounts */}
                    {result.discounts && Object.keys(result.discounts).length > 0 && (
                      <div className="mb-6">
                        <h4 className="font-semibold mb-3 flex items-center" style={{ color: '#2C3E50' }}>
                          <Shield className="w-5 h-5 mr-2" style={{ color: '#10B981' }} />
                          Applied Discounts
                        </h4>
                        <div className="space-y-2">
                          {Object.entries(result.discounts).map(([key, value]) => (
                            <div key={key} className="flex justify-between p-3 rounded-lg" style={{ backgroundColor: '#D1FAE5' }}>
                              <span className="text-sm" style={{ color: '#2C3E50' }}>{value.reason}</span>
                              <span className="font-medium" style={{ color: '#10B981' }}>
                                -{fmtMoney(value.amount, currency)}
                              </span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* ML Confidence */}
                    <div className="p-4 rounded-lg" style={{ backgroundColor: '#D1FAE5' }}>
                      <p className="text-sm font-medium mb-2" style={{ color: '#065F46' }}>
                        AI-Powered Pricing
                      </p>
                      <p className="text-sm mb-3" style={{ color: '#047857' }}>
                        This premium is calculated using XGBoost ML model based on vehicle details, driver profile, and historical data.
                      </p>
                      <div className="flex justify-between items-center">
                        <span className="text-sm font-medium" style={{ color: '#065F46' }}>
                          Model Confidence
                        </span>
                        <span className="text-lg font-bold" style={{ color: '#10B981' }}>
                          {(result.confidence_score * 100).toFixed(0)}%
                        </span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2 mt-2">
                        <div
                          className="h-2 rounded-full"
                          style={{
                            width: `${result.confidence_score * 100}%`,
                            backgroundColor: '#10B981',
                          }}
                        />
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}