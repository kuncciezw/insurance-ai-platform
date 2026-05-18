import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import Sidebar from './Sidebar';
import { 
  Shield, AlertTriangle, Eye, 
  Calendar, DollarSign, Loader2, RefreshCw 
} from 'lucide-react';
import { api } from '../services/api';
import { useCurrencyFormatter } from '../utils/currencyFormatter';

export default function FraudDetection() {
  const navigate = useNavigate();
  const { fmtMoney } = useCurrencyFormatter();

  const [stats, setStats] = useState(null);
  const [riskDistribution, setRiskDistribution] = useState(null);
  const [highRiskClaims, setHighRiskClaims] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [period, setPeriod] = useState('30days');
  const [currency, setCurrency] = useState('USD');

  useEffect(() => {
    loadDashboard();
  }, [period]);

  const loadDashboard = async () => {
    setIsLoading(true);
    try {
      const [statsData, riskData, claimsData] = await Promise.all([
        api.request('/fraud-detection/fraud/statistics/'),
        api.request(`/fraud-detection/stats/?period=${period}`),
        api.request('/fraud-detection/fraud/high-risk-claims/?threshold=0.6&limit=20'),
      ]);

      setStats(statsData);
      setRiskDistribution(riskData);
      setHighRiskClaims(claimsData.results || claimsData);
    } catch (err) {
      console.error('Failed to load dashboard:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const getRiskColor = (score) => {
    if (score >= 0.7) return { bg: '#FEE2E2', text: '#991B1B' };
    if (score >= 0.5) return { bg: '#FEF3C7', text: '#92400E' };
    return { bg: '#F3F4F6', text: '#6B7280' };
  };

  const fmtDate = (d) => {
    if (!d) return '—';
    return new Date(d).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
  };

  if (isLoading) {
    return (
      <div className="flex h-screen" style={{ backgroundColor: '#F8F9FA' }}>
        <Sidebar />
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center">
            <Loader2 className="w-10 h-10 animate-spin mx-auto mb-3" style={{ color: '#FF6B4A' }} />
            <p className="text-sm" style={{ color: '#7F8C8D' }}>Loading fraud analytics…</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-screen overflow-hidden" style={{ backgroundColor: '#F8F9FA' }}>
      <Sidebar />

      <div className="flex-1 overflow-y-auto">
        <div className="p-8">

          {/* Header */}
          <div className="flex items-start justify-between mb-8">
            <div>
              <h2 className="text-3xl font-bold" style={{ color: '#2C3E50' }}>
                Fraud Detection
              </h2>
              <p className="mt-1.5 text-sm" style={{ color: '#7F8C8D' }}>
                Monitor high-risk claims and fraud patterns
              </p>
            </div>

            <div className="flex items-center gap-3">
              {/* Currency toggle */}
              <div className="flex items-center gap-3 mr-2">
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

              {/* Period selector */}
              <select
                value={period}
                onChange={(e) => setPeriod(e.target.value)}
                className="px-4 py-2 rounded-xl border text-sm font-semibold focus:outline-none focus:ring-2 focus:ring-orange-300"
                style={{ borderColor: '#E5E7EB', color: '#2C3E50', height: '42px' }}>
                <option value="7days">Last 7 days</option>
                <option value="30days">Last 30 days</option>
                <option value="90days">Last 90 days</option>
              </select>

              <button
                onClick={loadDashboard}
                className="flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-semibold transition-all"
                style={{ backgroundColor: '#FF6B4A', color: 'white', height: '42px' }}
                onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = '#E55A3A')}
                onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = '#FF6B4A')}>
                <RefreshCw className="w-4 h-4" />
                Refresh
              </button>
            </div>
          </div>

          {/* KPI Cards - Simplified to 3 cards */}
          {stats && (
            <div className="grid grid-cols-3 gap-6 mb-8">
              {[
                {
                  label: 'Total Claims',
                  value: stats.total_claims?.toLocaleString() || '0',
                  icon: <Shield className="w-5 h-5" />,
                  color: '#2C3E50',
                  bg: '#F8F9FA',
                },
                {
                  label: 'High Risk',
                  value: stats.high_risk_claims?.toLocaleString() || '0',
                  subtext: `${((stats.high_risk_claims / (stats.total_claims || 1)) * 100).toFixed(1)}% of total`,
                  icon: <AlertTriangle className="w-5 h-5" />,
                  color: '#FF6B4A',
                  bg: '#FFF5F3',
                },
                {
                  label: 'Fraud Rate',
                  value: `${((stats.fraud_rate || 0) * 100).toFixed(1)}%`,
                  icon: <Shield className="w-5 h-5" />,
                  color: stats.fraud_rate > 0.1 ? '#EF4444' : '#7F8C8D',
                  bg: stats.fraud_rate > 0.1 ? '#FEE2E2' : '#F8F9FA',
                },
              ].map(({ label, value, subtext, icon, color, bg }) => (
                <div key={label} className="bg-white rounded-2xl shadow-sm p-6">
                  <div className="flex items-start gap-4">
                    <div className="w-12 h-12 rounded-xl flex items-center justify-center flex-shrink-0"
                         style={{ backgroundColor: bg, color }}>
                      {icon}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-xs font-medium mb-1" style={{ color: '#9CA3AF' }}>{label}</p>
                      <p className="text-2xl font-bold truncate" style={{ color: '#2C3E50' }}>{value}</p>
                      {subtext && (
                        <p className="text-xs mt-1" style={{ color: '#9CA3AF' }}>{subtext}</p>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* High-Risk Claims Table */}
          <div className="bg-white rounded-2xl shadow-sm overflow-hidden">
            <div className="px-6 py-5 border-b flex items-center justify-between"
                 style={{ borderColor: '#E5E7EB' }}>
              <div>
                <h3 className="text-lg font-bold" style={{ color: '#2C3E50' }}>
                  High-Risk Claims
                </h3>
                <p className="text-xs mt-0.5" style={{ color: '#7F8C8D' }}>
                  Claims with fraud score ≥ 60% · Click to view details
                </p>
              </div>
              <span className="text-xs px-3 py-1.5 rounded-full font-bold"
                    style={{ backgroundColor: '#FFF5F3', color: '#FF6B4A' }}>
                {highRiskClaims.length} claims
              </span>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full">
                <thead style={{ backgroundColor: '#F8F9FA', borderBottom: '2px solid #E5E7EB' }}>
                  <tr>
                    {['Claim #', 'Policyholder', 'Type', `Amount`, 'Fraud Score', 'Submitted', ''].map((h) => (
                      <th key={h}
                          className="px-6 py-4 text-left text-xs font-bold uppercase tracking-wider"
                          style={{ color: '#2C3E50' }}>
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {highRiskClaims.length === 0 ? (
                    <tr>
                      <td colSpan="7" className="px-6 py-16 text-center">
                        <Shield className="w-12 h-12 mx-auto mb-3" style={{ color: '#E5E7EB' }} />
                        <p className="text-sm font-semibold" style={{ color: '#2C3E50' }}>
                          No high-risk claims detected
                        </p>
                        <p className="text-xs mt-1" style={{ color: '#9CA3AF' }}>
                          All recent claims passed fraud checks
                        </p>
                      </td>
                    </tr>
                  ) : (
                    highRiskClaims.map((claim) => {
                      const fraudScore = claim.fraud_probability || 0;
                      const riskColor = getRiskColor(fraudScore);
                      return (
                        <tr key={claim.claim_id}
                            onClick={() => navigate(`/claims/${claim.claim_id}`)}
                            className="border-t transition-colors cursor-pointer group"
                            style={{ borderColor: '#F3F4F6' }}
                            onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = '#FFF5F3')}
                            onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = 'transparent')}>

                          <td className="px-6 py-4">
                            <span className="font-mono text-xs font-bold px-2.5 py-1 rounded-lg"
                                  style={{ backgroundColor: '#F3F4F6', color: '#2C3E50' }}>
                              {claim.claim_number}
                            </span>
                          </td>

                          <td className="px-6 py-4">
                            <p className="text-sm font-medium truncate max-w-48"
                               style={{ color: '#2C3E50' }}>
                              {claim.policyholder_name || '—'}
                            </p>
                          </td>

                          <td className="px-6 py-4">
                            <span className="text-sm" style={{ color: '#7F8C8D' }}>
                              {claim.claim_type || '—'}
                            </span>
                          </td>

                          <td className="px-6 py-4">
                            <span className="text-sm font-bold" style={{ color: '#2C3E50' }}>
                              {fmtMoney(claim.claimed_amount, currency)}
                            </span>
                          </td>

                          <td className="px-6 py-4">
                            <div className="flex items-center gap-3">
                              <div className="flex-1 max-w-24">
                                <div className="h-2 rounded-full" style={{ backgroundColor: '#F3F4F6' }}>
                                  <div className="h-2 rounded-full transition-all"
                                       style={{ 
                                         width: `${fraudScore * 100}%`,
                                         backgroundColor: fraudScore >= 0.7 ? '#EF4444' : fraudScore >= 0.5 ? '#FCD34D' : '#9CA3AF'
                                       }} />
                                </div>
                              </div>
                              <span className="px-2.5 py-1 rounded-full text-xs font-bold whitespace-nowrap min-w-14 text-center"
                                    style={{ backgroundColor: riskColor.bg, color: riskColor.text }}>
                                {(fraudScore * 100).toFixed(1)}%
                              </span>
                            </div>
                          </td>

                          <td className="px-6 py-4">
                            <div className="flex items-center gap-1.5 text-xs"
                                 style={{ color: '#9CA3AF' }}>
                              <Calendar className="w-3.5 h-3.5" />
                              {fmtDate(claim.submitted_date)}
                            </div>
                          </td>

                          <td className="px-6 py-4">
                            <button
                              className="p-2 rounded-lg transition-all opacity-0 group-hover:opacity-100"
                              style={{ backgroundColor: '#F8F9FA', color: '#7F8C8D' }}
                              onMouseEnter={(e) => {
                                e.currentTarget.style.backgroundColor = '#FF6B4A';
                                e.currentTarget.style.color = 'white';
                              }}
                              onMouseLeave={(e) => {
                                e.currentTarget.style.backgroundColor = '#F8F9FA';
                                e.currentTarget.style.color = '#7F8C8D';
                              }}>
                              <Eye className="w-4 h-4" />
                            </button>
                          </td>
                        </tr>
                      );
                    })
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}