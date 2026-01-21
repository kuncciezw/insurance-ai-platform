import { useState, useEffect } from 'react';
import Sidebar from './Sidebar';
import { Search, Filter, Eye, Flag, X, CheckCircle, AlertTriangle, Loader2 } from 'lucide-react';
import { api } from '../services/api';

export default function FraudDetection() {
  const [claims, setClaims] = useState([]);
  const [selectedClaim, setSelectedClaim] = useState(null);
  const [fraudAnalysis, setFraudAnalysis] = useState(null);
  const [riskFilter, setRiskFilter] = useState('All');
  const [searchTerm, setSearchTerm] = useState('');
  const [loading, setLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);
  const [error, setError] = useState(null);
  const [successMessage, setSuccessMessage] = useState(null);

  useEffect(() => {
    fetchClaims();
  }, []);

  // Auto-dismiss messages after 5 seconds
  useEffect(() => {
    if (successMessage || error) {
      const timer = setTimeout(() => {
        setSuccessMessage(null);
        setError(null);
      }, 5000);
      return () => clearTimeout(timer);
    }
  }, [successMessage, error]);

  const fetchClaims = async () => {
    try {
      setLoading(true);
      // Fetch pending claims from backend
      const response = await api.getClaims({ status: 'Pending' });
      
      // Handle both paginated and non-paginated responses
      const claimsData = response.results || response;
      setClaims(claimsData);
      setError(null);
    } catch (err) {
      console.error('Error fetching claims:', err);
      setError(err instanceof Error ? err.message : 'Failed to load claims');
    } finally {
      setLoading(false);
    }
  };

  const handleAnalyzeClaim = async (claim) => {
    setSelectedClaim(claim);
    setAnalyzing(true);
    setFraudAnalysis(null);
    
    try {
      // Call ML fraud analysis endpoint
      const analysis = await api.request('/fraud-detection/fraud/analyze-claim/', {
        method: 'POST',
        body: JSON.stringify({ claim_id: claim.id })
      });
      
      setFraudAnalysis(analysis);
      
      // Update the claim in the list with new fraud score
      setClaims(prevClaims => 
        prevClaims.map(c => 
          c.id === claim.id 
            ? { ...c, fraud_score: analysis.fraud_score, is_fraudulent: analysis.is_fraudulent }
            : c
        )
      );
    } catch (err) {
      console.error('Fraud analysis error:', err);
      setError(err instanceof Error ? err.message : 'Failed to analyze claim');
    } finally {
      setAnalyzing(false);
    }
  };

  const handleApproveClaim = async () => {
    if (!selectedClaim) return;
    
    try {
      setAnalyzing(true);
      setError(null);
      
      // Call approve endpoint
      await api.request(`/fraud-detection/claims/${selectedClaim.id}/approve/`, {
        method: 'POST',
        body: JSON.stringify({
          approved_amount: selectedClaim.claimed_amount
        })
      });
      
      // Update local state
      setClaims(prevClaims => 
        prevClaims.filter(c => c.id !== selectedClaim.id)
      );
      
      // Show success message
      setSuccessMessage('Claim approved successfully!');
      
      // Close panel
      setSelectedClaim(null);
      setFraudAnalysis(null);
      
    } catch (err) {
      console.error('Error approving claim:', err);
      setError(err instanceof Error ? err.message : 'Failed to approve claim');
    } finally {
      setAnalyzing(false);
    }
  };

  const handleRejectClaim = async () => {
    if (!selectedClaim) return;
    
    const reason = prompt('Please enter rejection reason:');
    if (!reason) return;
    
    try {
      setAnalyzing(true);
      setError(null);
      
      // Call reject endpoint
      await api.request(`/fraud-detection/claims/${selectedClaim.id}/reject/`, {
        method: 'POST',
        body: JSON.stringify({
          reason: reason
        })
      });
      
      // Update local state
      setClaims(prevClaims => 
        prevClaims.filter(c => c.id !== selectedClaim.id)
      );
      
      // Show success message
      setSuccessMessage('Claim rejected and flagged as fraudulent.');
      
      // Close panel
      setSelectedClaim(null);
      setFraudAnalysis(null);
      
    } catch (err) {
      console.error('Error rejecting claim:', err);
      setError(err instanceof Error ? err.message : 'Failed to reject claim');
    } finally {
      setAnalyzing(false);
    }
  };

  const handleRequestInvestigation = async () => {
    if (!selectedClaim) return;
    
    try {
      setAnalyzing(true);
      setError(null);
      
      // Update claim status to UNDER_REVIEW
      await api.updateClaim(selectedClaim.id, {
        claim_status: 'UNDER_REVIEW'
      });
      
      // Update local state
      setClaims(prevClaims => 
        prevClaims.map(c => 
          c.id === selectedClaim.id 
            ? { ...c, claim_status: 'UNDER_REVIEW' }
            : c
        )
      );
      
      // Show success message
      setSuccessMessage('Claim marked for investigation. An investigator will review this case.');
      
      // Close panel
      setSelectedClaim(null);
      setFraudAnalysis(null);
      
    } catch (err) {
      console.error('Error requesting investigation:', err);
      setError(err instanceof Error ? err.message : 'Failed to request investigation');
    } finally {
      setAnalyzing(false);
    }
  };

  const getRiskColor = (level) => {
    if (typeof level === 'number') {
      if (level < 0.3) return '#28A745';
      if (level < 0.5) return '#FFC107';
      if (level < 0.7) return '#FF6B4A';
      return '#DC3545';
    }
    
    switch (level.toUpperCase()) {
      case 'LOW':
        return '#28A745';
      case 'MEDIUM':
        return '#FFC107';
      case 'HIGH':
        return '#FF6B4A';
      case 'CRITICAL':
        return '#DC3545';
      default:
        return '#7F8C8D';
    }
  };

  const getRiskLevel = (score) => {
    if (score < 0.3) return 'Low';
    if (score < 0.5) return 'Medium';
    if (score < 0.7) return 'High';
    return 'Critical';
  };

  const filteredClaims = claims.filter((claim) => {
    const riskLevel = getRiskLevel(claim.fraud_score || 0);
    const matchesRisk = riskFilter === 'All' || riskLevel === riskFilter;
    const matchesSearch = 
      claim.claim_number?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      claim.policyholder_name?.toLowerCase().includes(searchTerm.toLowerCase());
    return matchesRisk && matchesSearch;
  });

  if (loading) {
    return (
      <div className="flex h-screen">
        <Sidebar />
        <div className="flex-1 flex items-center justify-center" style={{ backgroundColor: '#F8F9FA' }}>
          <div className="text-center">
            <Loader2 className="w-12 h-12 animate-spin mx-auto" style={{ color: '#FF6B4A' }} />
            <p className="mt-4" style={{ color: '#7F8C8D' }}>Loading claims...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar />
      
      <div className="flex-1 overflow-y-auto" style={{ backgroundColor: '#F8F9FA' }}>
        <div className="p-8">
          {/* Page Title */}
          <h1 className="text-3xl font-bold mb-8" style={{ color: '#2C3E50' }}>
            Fraud Detection Analysis
          </h1>

          {/* Filter Section */}
          <div className="bg-white rounded-xl shadow-sm p-6 mb-6">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div>
                <label className="block text-sm mb-2" style={{ color: '#7F8C8D' }}>
                  Search Claim ID
                </label>
                <div className="relative">
                  <input
                    type="text"
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    placeholder="Search by ID or name..."
                    className="w-full pl-10 pr-4 py-2 rounded-lg border focus:outline-none focus:ring-2"
                    style={{ borderColor: '#E0E0E0' }}
                  />
                  <Search className="absolute left-3 top-2.5 w-5 h-5" style={{ color: '#7F8C8D' }} />
                </div>
              </div>

              <div>
                <label className="block text-sm mb-2" style={{ color: '#7F8C8D' }}>
                  Risk Level
                </label>
                <div className="relative">
                  <select
                    value={riskFilter}
                    onChange={(e) => setRiskFilter(e.target.value)}
                    className="w-full px-4 py-2 rounded-lg border focus:outline-none focus:ring-2 appearance-none"
                    style={{ borderColor: '#E0E0E0' }}
                  >
                    <option>All</option>
                    <option>Low</option>
                    <option>Medium</option>
                    <option>High</option>
                    <option>Critical</option>
                  </select>
                  <Filter className="absolute right-3 top-2.5 w-5 h-5 pointer-events-none" style={{ color: '#7F8C8D' }} />
                </div>
              </div>

              <div className="md:col-span-2 flex items-end">
                <button
                  onClick={fetchClaims}
                  className="w-full py-2 px-4 rounded-lg text-white font-medium hover:shadow-lg transition-all"
                  style={{ backgroundColor: '#2C3E50' }}
                >
                  Refresh
                </button>
              </div>
            </div>
          </div>

          {/* Error Message */}
          {error && (
            <div className="mb-6 p-4 rounded-lg flex items-center justify-between" style={{ backgroundColor: '#FEE', color: '#DC3545', border: '1px solid #DC3545' }}>
              <span>{error}</span>
              <button onClick={() => setError(null)} className="ml-4">
                <X className="w-5 h-5" />
              </button>
            </div>
          )}

          {/* Success Message */}
          {successMessage && (
            <div className="mb-6 p-4 rounded-lg flex items-center justify-between" style={{ backgroundColor: '#D4EDDA', color: '#155724', border: '1px solid #C3E6CB' }}>
              <div className="flex items-center">
                <CheckCircle className="w-5 h-5 mr-2" />
                <span>{successMessage}</span>
              </div>
              <button onClick={() => setSuccessMessage(null)} className="ml-4">
                <X className="w-5 h-5" />
              </button>
            </div>
          )}

          {/* Results Table */}
          <div className="bg-white rounded-xl shadow-sm overflow-hidden">
            <div className="p-6 border-b" style={{ borderColor: '#E0E0E0' }}>
              <h2 className="text-xl font-bold" style={{ color: '#2C3E50' }}>
                Fraud Analysis Results ({filteredClaims.length})
              </h2>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead style={{ backgroundColor: '#F8F9FA' }}>
                  <tr>
                    <th className="px-6 py-3 text-left text-sm font-medium" style={{ color: '#7F8C8D' }}>
                      Claim ID
                    </th>
                    <th className="px-6 py-3 text-left text-sm font-medium" style={{ color: '#7F8C8D' }}>
                      Policyholder
                    </th>
                    <th className="px-6 py-3 text-left text-sm font-medium" style={{ color: '#7F8C8D' }}>
                      Amount
                    </th>
                    <th className="px-6 py-3 text-left text-sm font-medium" style={{ color: '#7F8C8D' }}>
                      Fraud Score
                    </th>
                    <th className="px-6 py-3 text-left text-sm font-medium" style={{ color: '#7F8C8D' }}>
                      Risk Level
                    </th>
                    <th className="px-6 py-3 text-left text-sm font-medium" style={{ color: '#7F8C8D' }}>
                      Date
                    </th>
                    <th className="px-6 py-3 text-left text-sm font-medium" style={{ color: '#7F8C8D' }}>
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {filteredClaims.map((claim) => {
                    const fraudScore = claim.fraud_score || 0;
                    const riskLevel = getRiskLevel(fraudScore);
                    return (
                      <tr
                        key={claim.id}
                        className="border-b hover:bg-gray-50 transition-colors"
                        style={{ borderColor: '#E0E0E0' }}
                      >
                        <td className="px-6 py-4 font-medium" style={{ color: '#2C3E50' }}>
                          {claim.claim_number}
                        </td>
                        <td className="px-6 py-4" style={{ color: '#2C3E50' }}>
                          {claim.policyholder_name}
                        </td>
                        <td className="px-6 py-4 font-medium" style={{ color: '#2C3E50' }}>
                          ${parseFloat(claim.claimed_amount).toLocaleString()}
                        </td>
                        <td className="px-6 py-4">
                          <div className="flex items-center space-x-2">
                            <div className="flex-1 bg-gray-200 rounded-full h-2">
                              <div
                                className="h-2 rounded-full"
                                style={{
                                  width: `${fraudScore * 100}%`,
                                  backgroundColor: getRiskColor(fraudScore),
                                }}
                              />
                            </div>
                            <span className="text-sm font-medium" style={{ color: '#2C3E50' }}>
                              {(fraudScore * 100).toFixed(0)}%
                            </span>
                          </div>
                        </td>
                        <td className="px-6 py-4">
                          <span
                            className="px-3 py-1 rounded-full text-sm font-medium text-white"
                            style={{ backgroundColor: getRiskColor(riskLevel) }}
                          >
                            {riskLevel}
                          </span>
                        </td>
                        <td className="px-6 py-4" style={{ color: '#7F8C8D' }}>
                          {new Date(claim.submitted_date).toLocaleDateString('en-US', {
                            month: 'short',
                            day: 'numeric',
                            year: 'numeric'
                          })}
                        </td>
                        <td className="px-6 py-4">
                          <div className="flex space-x-2">
                            <button
                              onClick={() => handleAnalyzeClaim(claim)}
                              className="p-2 rounded-lg hover:bg-gray-100 transition-colors"
                              title="Analyze Fraud"
                            >
                              <Eye className="w-5 h-5" style={{ color: '#17A2B8' }} />
                            </button>
                            {claim.is_fraudulent && (
                              <button
                                className="p-2 rounded-lg hover:bg-gray-100 transition-colors"
                                title="Flagged as Fraud"
                              >
                                <Flag className="w-5 h-5" style={{ color: '#DC3545' }} />
                              </button>
                            )}
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>

            {filteredClaims.length === 0 && (
              <div className="p-8 text-center" style={{ color: '#7F8C8D' }}>
                No claims found matching your criteria
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Side Panel */}
      {selectedClaim && (
        <div className="w-96 border-l bg-white overflow-y-auto" style={{ borderColor: '#E0E0E0' }}>
          <div className="p-6">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-bold" style={{ color: '#2C3E50' }}>
                Fraud Analysis
              </h2>
              <button
                onClick={() => {
                  setSelectedClaim(null);
                  setFraudAnalysis(null);
                }}
                className="p-2 rounded-lg hover:bg-gray-100 transition-colors"
              >
                <X className="w-5 h-5" style={{ color: '#7F8C8D' }} />
              </button>
            </div>

            {analyzing ? (
              <div className="text-center py-8">
                <Loader2 className="w-12 h-12 animate-spin mx-auto mb-4" style={{ color: '#FF6B4A' }} />
                <p style={{ color: '#7F8C8D' }}>Analyzing claim for fraud...</p>
              </div>
            ) : fraudAnalysis ? (
              <>
                {/* Claim Info */}
                <div className="mb-6">
                  <div className="flex items-center justify-between mb-4">
                    <span className="text-lg font-bold" style={{ color: '#2C3E50' }}>
                      {fraudAnalysis.claim_number}
                    </span>
                    <span
                      className="px-3 py-1 rounded-full text-sm font-medium text-white"
                      style={{ backgroundColor: getRiskColor(fraudAnalysis.fraud_analysis.risk_level) }}
                    >
                      {fraudAnalysis.fraud_analysis.risk_level}
                    </span>
                  </div>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span style={{ color: '#7F8C8D' }}>Amount:</span>
                      <span className="font-medium" style={{ color: '#2C3E50' }}>
                        ${parseFloat(fraudAnalysis.claimed_amount || selectedClaim.claimed_amount).toLocaleString()}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span style={{ color: '#7F8C8D' }}>Analyzed:</span>
                      <span style={{ color: '#2C3E50' }}>
                        {new Date(fraudAnalysis.analyzed_at).toLocaleTimeString()}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Fraud Score */}
                <div className="mb-6">
                  <h3 className="font-bold mb-3" style={{ color: '#2C3E50' }}>
                    Fraud Probability
                  </h3>
                  <div className="mb-2">
                    <div className="flex justify-between text-sm mb-1">
                      <span style={{ color: '#7F8C8D' }}>Overall Score</span>
                      <span className="font-medium" style={{ color: '#2C3E50' }}>
                        {(fraudAnalysis.fraud_analysis.fraud_probability * 100).toFixed(1)}%
                      </span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-3">
                      <div
                        className="h-3 rounded-full transition-all"
                        style={{
                          width: `${fraudAnalysis.fraud_analysis.fraud_probability * 100}%`,
                          backgroundColor: getRiskColor(fraudAnalysis.fraud_analysis.risk_level),
                        }}
                      />
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-2 mt-4 text-xs">
                    <div className="p-2 rounded" style={{ backgroundColor: '#F8F9FA' }}>
                      <span style={{ color: '#7F8C8D' }}>ML Score: </span>
                      <span className="font-medium" style={{ color: '#2C3E50' }}>
                        {(fraudAnalysis.fraud_analysis.xgboost_probability * 100).toFixed(1)}%
                      </span>
                    </div>
                    <div className="p-2 rounded" style={{ backgroundColor: '#F8F9FA' }}>
                      <span style={{ color: '#7F8C8D' }}>Anomaly: </span>
                      <span className="font-medium" style={{ color: '#2C3E50' }}>
                        {(fraudAnalysis.fraud_analysis.anomaly_score * 100).toFixed(1)}%
                      </span>
                    </div>
                  </div>
                </div>

                {/* Risk Indicators */}
                <div className="mb-6">
                  <h3 className="font-bold mb-3" style={{ color: '#2C3E50' }}>
                    Risk Indicators
                  </h3>
                  <div className="space-y-2">
                    {fraudAnalysis.risk_factors.map((factor, index) => (
                      <div key={index} className="flex items-start space-x-2">
                        {fraudAnalysis.fraud_analysis.fraud_probability > 0.5 ? (
                          <AlertTriangle className="w-5 h-5 flex-shrink-0 mt-0.5" style={{ color: '#DC3545' }} />
                        ) : (
                          <CheckCircle className="w-5 h-5 flex-shrink-0 mt-0.5" style={{ color: '#28A745' }} />
                        )}
                        <span className="text-sm" style={{ color: '#2C3E50' }}>{factor}</span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Recommendation */}
                <div className="p-4 rounded-lg mb-6" style={{ backgroundColor: '#F0F9FF', border: '1px solid #17A2B8' }}>
                  <h3 className="font-bold mb-2" style={{ color: '#2C3E50' }}>
                    Recommendation
                  </h3>
                  <p className="text-sm mb-2" style={{ color: '#2C3E50' }}>
                    <strong>Action:</strong> {fraudAnalysis.recommendation.replace(/_/g, ' ')}
                  </p>
                  <p className="text-sm" style={{ color: '#7F8C8D' }}>
                    {fraudAnalysis.explanation}
                  </p>
                </div>

                {/* Actions */}
                <div className="space-y-3">
                  <button
                    className="w-full py-2 px-4 rounded-lg font-medium transition-all hover:shadow-lg disabled:opacity-50 disabled:cursor-not-allowed"
                    style={{ 
                      backgroundColor: fraudAnalysis.fraud_analysis.fraud_probability > 0.6 ? '#DC3545' : '#28A745',
                      color: '#FFFFFF' 
                    }}
                    onClick={fraudAnalysis.fraud_analysis.fraud_probability > 0.6 ? handleRejectClaim : handleApproveClaim}
                    disabled={analyzing}
                  >
                    {analyzing ? 'Processing...' : (fraudAnalysis.fraud_analysis.fraud_probability > 0.6 ? 'Flag as Fraud' : 'Approve Claim')}
                  </button>
                  <button
                    className="w-full py-2 px-4 rounded-lg font-medium border transition-all hover:shadow disabled:opacity-50 disabled:cursor-not-allowed"
                    style={{ borderColor: '#E0E0E0', color: '#2C3E50' }}
                    onClick={handleRequestInvestigation}
                    disabled={analyzing}
                  >
                    Request Investigation
                  </button>
                </div>
              </>
            ) : (
              <div className="text-center py-8" style={{ color: '#7F8C8D' }}>
                <p>Click "Analyze" to see fraud detection results</p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}