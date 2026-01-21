import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { api } from '../services/api';
import Sidebar from './Sidebar';
import {
  Users,
  FileText,
  AlertCircle,
  Shield,
} from 'lucide-react';

// Beautiful Line Chart Component (Prototype Style)
function LineChart({ data, period }) {
  const [hoveredIndex, setHoveredIndex] = useState(null);

  if (!data || data.length === 0) {
    return (
      <div className="h-full flex items-center justify-center" style={{ color: '#7F8C8D' }}>
        No claims data available
      </div>
    );
  }

  const maxValue = Math.max(...data.map(d => d.claims), 1);
  const padding = 50;
  const width = 600;
  const height = 300;
  const chartWidth = width - padding * 2;
  const chartHeight = height - padding * 2;

  const points = data.map((item, index) => {
    const x = padding + (chartWidth / (data.length - 1)) * index;
    const y = padding + chartHeight - (item.claims / maxValue) * chartHeight;
    return { x, y, claims: item.claims, label: item.month };
  });

  const linePath = points.reduce((path, point, index) => {
    if (index === 0) return `M ${point.x},${point.y}`;
    return `${path} L ${point.x},${point.y}`;
  }, '');

  return (
    <div className="relative">
      <svg width="100%" height={height} viewBox={`0 0 ${width} ${height}`}>
        {/* Grid lines */}
        {[0, 0.25, 0.5, 0.75, 1].map((ratio, i) => (
          <line
            key={i}
            x1={padding}
            y1={padding + chartHeight * (1 - ratio)}
            x2={width - padding}
            y2={padding + chartHeight * (1 - ratio)}
            stroke="#E0E0E0"
            strokeWidth="1"
            strokeDasharray="3 3"
          />
        ))}

        {/* Line */}
        <path
          d={linePath}
          fill="none"
          stroke="#FF6B4A"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
        />

        {/* Points */}
        {points.map((point, index) => (
          <g key={index}>
            <circle
              cx={point.x}
              cy={point.y}
              r={hoveredIndex === index ? 6 : 4}
              fill="#FF6B4A"
              stroke="white"
              strokeWidth="2"
              style={{ cursor: 'pointer', transition: 'all 0.2s' }}
              onMouseEnter={() => setHoveredIndex(index)}
              onMouseLeave={() => setHoveredIndex(null)}
            />
            
            {hoveredIndex === index && (
              <g>
                <rect
                  x={point.x - 30}
                  y={point.y - 40}
                  width="60"
                  height="28"
                  rx="4"
                  fill="#2C3E50"
                  opacity="0.9"
                />
                <text
                  x={point.x}
                  y={point.y - 22}
                  textAnchor="middle"
                  fill="white"
                  fontSize="12"
                  fontWeight="bold"
                >
                  {point.claims}
                </text>
              </g>
            )}
          </g>
        ))}

        {/* X-axis labels */}
        {data.map((item, index) => {
          const x = padding + (chartWidth / (data.length - 1)) * index;
          return (
            <text
              key={index}
              x={x}
              y={height - padding + 25}
              textAnchor="middle"
              fill="#7F8C8D"
              fontSize="12"
            >
              {item.month}
            </text>
          );
        })}

        {/* Y-axis labels */}
        {[0, 0.5, 1].map((ratio, i) => {
          const value = Math.round(maxValue * ratio);
          return (
            <text
              key={i}
              x={padding - 15}
              y={padding + chartHeight * (1 - ratio) + 4}
              textAnchor="end"
              fill="#7F8C8D"
              fontSize="11"
            >
              {value}
            </text>
          );
        })}
      </svg>
    </div>
  );
}

// Beautiful Donut Chart Component (Prototype Style)
function DonutChart({ data, period }) {
  const [hoveredSegment, setHoveredSegment] = useState(null);

  if (!data) {
    return (
      <div className="h-full flex items-center justify-center" style={{ color: '#7F8C8D' }}>
        No fraud data available
      </div>
    );
  }

  const total = data.low_risk + data.medium_risk + data.high_risk;
  
  const segments = [
    { label: 'Legitimate', value: data.low_risk, percentage: total > 0 ? (data.low_risk / total) * 100 : 0, color: '#28A745' },
    { label: 'Suspicious', value: data.medium_risk, percentage: total > 0 ? (data.medium_risk / total) * 100 : 0, color: '#FFC107' },
    { label: 'Fraudulent', value: data.high_risk, percentage: total > 0 ? (data.high_risk / total) * 100 : 0, color: '#DC3545' }
  ];

  const size = 220;
  const center = size / 2;
  const radius = 80;
  const innerRadius = 55;

  let currentAngle = -90;
  const segmentPaths = segments.map((segment, index) => {
    const angle = (segment.percentage / 100) * 360;
    const startAngle = currentAngle;
    const endAngle = currentAngle + angle;
    currentAngle = endAngle;

    const isHovered = hoveredSegment === index;
    const outerR = isHovered ? radius + 5 : radius;

    const x1 = center + outerR * Math.cos((Math.PI * startAngle) / 180);
    const y1 = center + outerR * Math.sin((Math.PI * startAngle) / 180);
    const x2 = center + outerR * Math.cos((Math.PI * endAngle) / 180);
    const y2 = center + outerR * Math.sin((Math.PI * endAngle) / 180);
    const x3 = center + innerRadius * Math.cos((Math.PI * endAngle) / 180);
    const y3 = center + innerRadius * Math.sin((Math.PI * endAngle) / 180);
    const x4 = center + innerRadius * Math.cos((Math.PI * startAngle) / 180);
    const y4 = center + innerRadius * Math.sin((Math.PI * startAngle) / 180);

    const largeArc = angle > 180 ? 1 : 0;

    const path = `
      M ${x1} ${y1}
      A ${outerR} ${outerR} 0 ${largeArc} 1 ${x2} ${y2}
      L ${x3} ${y3}
      A ${innerRadius} ${innerRadius} 0 ${largeArc} 0 ${x4} ${y4}
      Z
    `;

    return { path, ...segment, isHovered };
  });

  return (
    <div className="flex flex-col items-center">
      <svg width={size} height={size}>
        {segmentPaths.map((segment, index) => (
          <path
            key={index}
            d={segment.path}
            fill={segment.color}
            stroke="white"
            strokeWidth="3"
            style={{
              cursor: 'pointer',
              transition: 'all 0.3s',
              filter: segment.isHovered ? 'brightness(1.1)' : 'none'
            }}
            onMouseEnter={() => setHoveredSegment(index)}
            onMouseLeave={() => setHoveredSegment(null)}
          />
        ))}
        
        <circle cx={center} cy={center} r={innerRadius - 5} fill="white" />
        <text
          x={center}
          y={center - 5}
          textAnchor="middle"
          fill="#2C3E50"
          fontSize="20"
          fontWeight="bold"
        >
          {data.fraud_rate || 0}%
        </text>
        <text
          x={center}
          y={center + 12}
          textAnchor="middle"
          fill="#7F8C8D"
          fontSize="11"
        >
          Fraud Rate
        </text>
      </svg>

      <div className="mt-4 flex flex-wrap justify-center gap-4">
        {segments.map((segment, index) => (
          <div
            key={index}
            className="flex items-center gap-2 cursor-pointer"
            onMouseEnter={() => setHoveredSegment(index)}
            onMouseLeave={() => setHoveredSegment(null)}
            style={{
              opacity: hoveredSegment === null || hoveredSegment === index ? 1 : 0.5,
              transition: 'opacity 0.2s'
            }}
          >
            <div
              className="w-3 h-3 rounded-full"
              style={{ backgroundColor: segment.color }}
            />
            <div className="text-sm">
              <span style={{ color: '#2C3E50', fontWeight: '500' }}>
                {segment.label}:
              </span>
              <span style={{ color: '#2C3E50', fontWeight: 'bold', marginLeft: '4px' }}>
                {segment.percentage.toFixed(1)}%
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default function Dashboard() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [stats, setStats] = useState(null);
  const [claimsData, setClaimsData] = useState([]);
  const [fraudData, setFraudData] = useState(null);
  const [recentClaims, setRecentClaims] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [claimsPeriod, setClaimsPeriod] = useState('1year');
  const [fraudPeriod, setFraudPeriod] = useState('30days');

  useEffect(() => {
    fetchDashboardData();
    fetchRecentClaims();
  }, []);

  useEffect(() => {
    fetchClaimsActivity();
  }, [claimsPeriod]);

  useEffect(() => {
    fetchFraudStats();
  }, [fraudPeriod]);

  const fetchDashboardData = async () => {
    try {
      setIsLoading(true);
      const data = await api.getDashboardStats();
      setStats(data);
      setError('');
    } catch (err) {
      console.error('Failed to fetch dashboard stats:', err);
      setError('Failed to load dashboard statistics');
    } finally {
      setIsLoading(false);
    }
  };

  const fetchClaimsActivity = async () => {
    try {
      const data = await api.getClaimsActivity(claimsPeriod);
      // Transform data for custom chart
      const transformedData = (data || []).map(item => ({
        month: item.label,
        claims: item.count
      }));
      setClaimsData(transformedData);
    } catch (err) {
      console.error('Failed to fetch claims activity:', err);
    }
  };

  const fetchFraudStats = async () => {
    try {
      const data = await api.getFraudStats(fraudPeriod);
      setFraudData(data);
    } catch (err) {
      console.error('Failed to fetch fraud stats:', err);
    }
  };

  const fetchRecentClaims = async () => {
    try {
      const response = await api.getClaims({ 
        ordering: '-submitted_date,claim_number',
        limit: 6 
      });
      
      // Transform the data to match our table format
      const transformedClaims = (response.results || []).slice(0, 5).map(claim => ({
        id: claim.claim_number,
        policyholder: claim.policyholder_name || 'Unknown',
        date: new Date(claim.submitted_date).toLocaleDateString('en-US', { 
          month: 'short', 
          day: 'numeric', 
          year: 'numeric' 
        }),
        amount: `$${Number(claim.claimed_amount).toLocaleString()}`,
        status: claim.claim_status === 'SUBMITTED' ? 'Pending' : 
                claim.claim_status === 'APPROVED' ? 'Approved' : 
                claim.claim_status === 'REJECTED' ? 'Rejected' :
                claim.claim_status === 'UNDER_REVIEW' ? 'Pending' :
                claim.claim_status
      }));
      
      setRecentClaims(transformedClaims);
    } catch (err) {
      console.error('Failed to fetch recent claims:', err);
      setRecentClaims([]);
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'Pending':
        return '#FFC107';
      case 'Approved':
        return '#28A745';
      case 'Rejected':
        return '#DC3545';
      default:
        return '#7F8C8D';
    }
  };

  const statsCards = [
    {
      title: 'Total Policyholders',
      value: stats?.total_policyholders || 0,
      icon: Users,
      color: '#17A2B8',
      bgColor: '#17A2B820'
    },
    {
      title: 'Active Policies',
      value: stats?.active_policies || 0,
      icon: FileText,
      color: '#28A745',
      bgColor: '#28A74520'
    },
    {
      title: 'Pending Claims',
      value: stats?.pending_claims || 0,
      icon: AlertCircle,
      color: '#FFC107',
      bgColor: '#FFC10720'
    },
    {
      title: 'Fraud Alerts',
      value: stats?.fraudulent_claims || 0,
      icon: Shield,
      color: '#DC3545',
      bgColor: '#DC354520'
    },
  ];

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ backgroundColor: '#F8F9FA' }}>
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2" style={{ borderColor: '#FF6B4A' }}></div>
          <p className="mt-4" style={{ color: '#7F8C8D' }}>Loading dashboard...</p>
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
            Dashboard
          </h1>

          {error && (
            <div className="mb-6 p-4 rounded-lg" style={{ backgroundColor: '#FEE2E2', color: '#DC2626' }}>
              {error}
            </div>
          )}

          {/* Stats Grid - Prototype Style */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            {statsCards.map((card) => {
              const Icon = card.icon;
              return (
                <div
                  key={card.title}
                  className="bg-white rounded-xl p-6 shadow-sm hover:shadow-md transition-shadow"
                >
                  <div className="flex items-start justify-between mb-4">
                    <div
                      className="w-12 h-12 rounded-lg flex items-center justify-center"
                      style={{ backgroundColor: card.bgColor }}
                    >
                      <Icon className="w-6 h-6" style={{ color: card.color }} />
                    </div>
                  </div>
                  <h3 className="text-2xl font-bold mb-1" style={{ color: '#2C3E50' }}>
                    {card.value.toLocaleString()}
                  </h3>
                  <p className="text-sm" style={{ color: '#7F8C8D' }}>
                    {card.title}
                  </p>
                </div>
              );
            })}
          </div>

          {/* Recent Claims Activity Table */}
          <div className="bg-white rounded-xl shadow-sm mb-8 overflow-hidden">
            <div className="p-6 border-b" style={{ borderColor: '#E0E0E0' }}>
              <h2 className="text-xl font-bold" style={{ color: '#2C3E50' }}>
                Recent Claims Activity
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
                      Date
                    </th>
                    <th className="px-6 py-3 text-left text-sm font-medium" style={{ color: '#7F8C8D' }}>
                      Amount
                    </th>
                    <th className="px-6 py-3 text-left text-sm font-medium" style={{ color: '#7F8C8D' }}>
                      Status
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {recentClaims.length > 0 ? (
                    recentClaims.map((claim) => (
                      <tr
                        key={claim.id}
                        className="border-b hover:bg-gray-50 transition-colors"
                        style={{ borderColor: '#E0E0E0' }}
                      >
                        <td className="px-6 py-4 font-medium" style={{ color: '#2C3E50' }}>
                          {claim.id}
                        </td>
                        <td className="px-6 py-4" style={{ color: '#2C3E50' }}>
                          {claim.policyholder}
                        </td>
                        <td className="px-6 py-4" style={{ color: '#7F8C8D' }}>
                          {claim.date}
                        </td>
                        <td className="px-6 py-4 font-medium" style={{ color: '#2C3E50' }}>
                          {claim.amount}
                        </td>
                        <td className="px-6 py-4">
                          <span
                            className="px-3 py-1 rounded-full text-sm font-medium text-white"
                            style={{ backgroundColor: getStatusColor(claim.status) }}
                          >
                            {claim.status}
                          </span>
                        </td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan="5" className="px-6 py-8 text-center" style={{ color: '#7F8C8D' }}>
                        No recent claims found
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>

          {/* Charts Section */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Claims Activity Line Chart */}
            <div className="bg-white rounded-xl shadow-sm p-6">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-xl font-bold" style={{ color: '#2C3E50' }}>
                  Claims by Month
                </h2>
                <div className="flex items-center gap-2">
                  <label className="text-sm font-medium" style={{ color: '#7F8C8D' }}>
                    Period:
                  </label>
                  <select
                    value={claimsPeriod}
                    onChange={(e) => setClaimsPeriod(e.target.value)}
                    className="px-3 py-1 rounded-lg border text-sm"
                    style={{ borderColor: '#E5E7EB', color: '#2C3E50' }}
                  >
                    <option value="7days">7 Days</option>
                    <option value="30days">30 Days</option>
                    <option value="1year">1 Year</option>
                  </select>
                </div>
              </div>
              <LineChart data={claimsData} period={claimsPeriod} />
            </div>

            {/* Fraud Detection Donut Chart */}
            <div className="bg-white rounded-xl shadow-sm p-6">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-xl font-bold" style={{ color: '#2C3E50' }}>
                  Fraud Detection Rate
                </h2>
                <div className="flex items-center gap-2">
                  <label className="text-sm font-medium" style={{ color: '#7F8C8D' }}>
                    Period:
                  </label>
                  <select
                    value={fraudPeriod}
                    onChange={(e) => setFraudPeriod(e.target.value)}
                    className="px-3 py-1 rounded-lg border text-sm"
                    style={{ borderColor: '#E5E7EB', color: '#2C3E50' }}
                  >
                    <option value="7days">Last 7 Days</option>
                    <option value="30days">Last 30 Days</option>
                    <option value="90days">Last 90 Days</option>
                    <option value="1year">Last Year</option>
                  </select>
                </div>
              </div>
              <DonutChart data={fraudData} period={fraudPeriod} />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}