import { useState, useEffect } from 'react';
import { api } from '../services/api';
import {
  X,
  User,
  Car,
  FileText,
  Shield,
  DollarSign,
  AlertTriangle,
  CheckCircle,
  XCircle,
  TrendingUp,
  Edit,
  MapPin,
  Calendar,
  Info,
  Phone,
  Mail,
  Cpu,
  Clock,
} from 'lucide-react';
import { useNotification } from './notifications/useNotification';
import { useConfirm } from './notifications/useConfirm';

export default function ClaimDetailsModal({ claim, onClose, onRefresh }) {
  const { showNotification, NotificationContainer } = useNotification();
  const { showConfirm, ConfirmDialog } = useConfirm();
  const [activeTab, setActiveTab] = useState('overview');
  const [isProcessing, setIsProcessing] = useState(false);
  const [aiResult, setAiResult] = useState(claim.ai_result || null);
  const [showOverride, setShowOverride] = useState(false);
  const [overrideReason, setOverrideReason] = useState('');
  const [claimDetails, setClaimDetails] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  const tabs = [
    { id: 'overview', label: 'Overview' },
    { id: 'policyholder', label: 'Policyholder' },
    { id: 'vehicle', label: 'Vehicle' },
    { id: 'fraud', label: 'Fraud Analysis' },
    { id: 'estimate', label: 'Cost Estimate' },
  ];

  useEffect(() => {
    fetchClaimDetails();
  }, [claim.id]);

  const fetchClaimDetails = async () => {
    try {
      setIsLoading(true);
      const data = await api.getClaim(claim.id);
      setClaimDetails(data);
    } catch (err) {
      console.error('Failed to fetch claim details:', err);
      showNotification('Failed to load claim details', 'error');
    } finally {
      setIsLoading(false);
    }
  };

  const handleProcessWithAI = async () => {
    try {
      setIsProcessing(true);
      const result = await api.autoProcessClaim(claim.id);
      setAiResult(result);
      showNotification('Claim processed successfully with AI', 'success');
    } catch (err) {
      console.error('AI processing failed:', err);
      showNotification('AI processing failed. Please try again.', 'error');
    } finally {
      setIsProcessing(false);
    }
  };

  const handleAcceptDecision = async () => {
    const confirmed = await showConfirm({
      title: 'Accept AI Decision',
      message: 'Are you sure you want to accept the AI recommendation? This will update the claim status.',
      type: 'warning'
    });

    if (!confirmed) return;

    try {
      const recommendation = aiResult?.processing_summary?.recommendation || aiResult?.recommendation;
      const estimatedCost = aiResult?.cost_estimation?.estimated_cost || aiResult?.estimated_amount;
      
      let newStatus;
      let approvedAmount;
      
      if (recommendation === 'AUTO_APPROVE') {
        newStatus = 'APPROVED';
        approvedAmount = estimatedCost || claim.claimed_amount;
      } else if (recommendation === 'REJECT_CLAIM') {
        newStatus = 'REJECTED';
        approvedAmount = 0;
      } else {
        newStatus = 'UNDER_REVIEW';
        approvedAmount = estimatedCost || claim.claimed_amount;
      }

      const updatedData = {
        claim_status: newStatus,
        approved_amount: parseFloat(approvedAmount),
      };

      await api.updateClaim(claim.id, updatedData);
      
      showNotification(`Claim ${newStatus.toLowerCase()} successfully!`, 'success');
      if (onRefresh) onRefresh();
      onClose();
    } catch (err) {
      console.error('Failed to accept AI decision:', err);
      
      let errorMessage = 'Failed to accept decision';
      if (err.data && typeof err.data === 'object') {
        const errors = Object.entries(err.data)
          .map(([field, messages]) => {
            const msgArray = Array.isArray(messages) ? messages : [messages];
            return `${field}: ${msgArray.join(', ')}`;
          })
          .join('\n');
        errorMessage += ':\n' + errors;
      } else if (err.message) {
        errorMessage += ': ' + err.message;
      }
      
      showNotification(errorMessage, 'error');
    }
  };

  const handleOverrideDecision = async () => {
    if (!overrideReason.trim()) {
      showNotification('Please provide a reason for overriding the AI decision', 'error');
      return;
    }

    const confirmed = await showConfirm({
      title: 'Override AI Decision',
      message: 'Are you sure you want to override the AI recommendation? This will require manual review.',
      type: 'warning'
    });

    if (!confirmed) return;

    try {
      showNotification('Override recorded. Please manually review the claim.', 'info');
      setShowOverride(false);
      onClose();
    } catch (err) {
      console.error('Failed to override decision:', err);
      showNotification('Failed to record override', 'error');
    }
  };

  const getStatusColor = (status) => {
    const colors = {
      SUBMITTED: '#3B82F6',
      'UNDER_REVIEW': '#F59E0B',
      APPROVED: '#10B981',
      REJECTED: '#EF4444',
      PAID: '#10B981',
      CLOSED: '#6B7280',
    };
    return colors[status] || '#6B7280';
  };

  const getRiskLevel = (score) => {
    if (score < 0.2) return { level: 'Low', color: '#10B981' };
    if (score < 0.4) return { level: 'Medium', color: '#F59E0B' };
    if (score < 0.6) return { level: 'High', color: '#FF6B4A' };
    return { level: 'Critical', color: '#EF4444' };
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { 
      year: 'numeric', 
      month: 'short', 
      day: 'numeric' 
    });
  };

  const formatDateTime = (dateString) => {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleString('en-US', { 
      year: 'numeric', 
      month: 'short', 
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  // Extract data from claimDetails or fall back to claim
  const displayClaim = claimDetails || claim;
  const fraudScore = aiResult?.fraud_analysis?.fraud_score || displayClaim.fraud_score || 0;
  const riskInfo = getRiskLevel(fraudScore);
  const estimatedCost = aiResult?.cost_estimation?.estimated_cost || displayClaim.approved_amount || displayClaim.claimed_amount || 0;
  const confidenceScore = aiResult?.processing_summary?.confidence === 'HIGH' ? 0.85 :
                         aiResult?.processing_summary?.confidence === 'MEDIUM' ? 0.70 : 0.60;
  const recommendation = aiResult?.processing_summary?.recommendation;
  const isApproved = recommendation === 'AUTO_APPROVE' || recommendation === 'APPROVED';
  const isRejected = recommendation === 'REJECT_CLAIM' || recommendation === 'REJECTED';

  // Build timeline events
  const getTimelineEvents = () => {
    const events = [
      { 
        date: formatDate(displayClaim.incident_date), 
        event: 'Incident Occurred', 
        status: 'complete',
        icon: AlertTriangle 
      },
      { 
        date: formatDateTime(displayClaim.submitted_date), 
        event: 'Claim Submitted', 
        status: 'complete',
        icon: FileText 
      },
    ];

    if (displayClaim.claim_status === 'UNDER_REVIEW') {
      events.push({
        date: formatDateTime(displayClaim.reviewed_date) || 'In Progress',
        event: 'Under Review',
        status: 'active',
        icon: Clock
      });
    } else if (displayClaim.reviewed_date) {
      events.push({
        date: formatDateTime(displayClaim.reviewed_date),
        event: 'Reviewed',
        status: 'complete',
        icon: CheckCircle
      });
    }

    if (displayClaim.claim_status === 'APPROVED') {
      events.push({
        date: formatDateTime(displayClaim.reviewed_date) || formatDate(new Date()),
        event: 'Claim Approved',
        status: 'complete',
        icon: CheckCircle
      });
    } else if (displayClaim.claim_status === 'REJECTED') {
      events.push({
        date: formatDateTime(displayClaim.reviewed_date) || formatDate(new Date()),
        event: 'Claim Rejected',
        status: 'complete',
        icon: XCircle
      });
    } else if (displayClaim.claim_status === 'PAID') {
      events.push({
        date: formatDateTime(displayClaim.closed_date) || formatDate(new Date()),
        event: 'Payment Completed',
        status: 'complete',
        icon: DollarSign
      });
    } else {
      events.push({
        date: 'Pending',
        event: 'Decision',
        status: 'pending',
        icon: Clock
      });
    }

    if (displayClaim.claim_status === 'PAID' && displayClaim.closed_date) {
      events.push({
        date: formatDateTime(displayClaim.closed_date),
        event: 'Claim Closed',
        status: 'complete',
        icon: CheckCircle
      });
    }

    return events;
  };

  if (isLoading) {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4" style={{ backgroundColor: 'rgba(0,0,0,0.5)' }}>
        <div className="bg-white rounded-xl shadow-2xl p-8">
          <div className="flex items-center gap-3">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2" style={{ borderColor: '#FF6B4A' }}></div>
            <p style={{ color: '#2C3E50' }}>Loading claim details...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4" style={{ backgroundColor: 'rgba(0,0,0,0.5)' }}>
      <NotificationContainer />
      <ConfirmDialog />
      
      <div className="bg-white rounded-xl shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b" style={{ borderColor: '#E5E7EB' }}>
          <div className="flex items-center gap-4">
            <h2 className="text-2xl font-bold" style={{ color: '#2C3E50' }}>
              {displayClaim.claim_number}
            </h2>
            <span
              className="px-3 py-1 rounded-full text-sm font-medium text-white"
              style={{ backgroundColor: getStatusColor(displayClaim.claim_status) }}
            >
              {displayClaim.claim_status}
            </span>
            {aiResult && (
              <span className="px-3 py-1 rounded-full text-xs font-medium" style={{ backgroundColor: '#D1FAE5', color: '#065F46' }}>
                <Cpu className="w-3 h-3 inline mr-1" />
                AI Processed
              </span>
            )}
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-lg hover:bg-gray-100 transition-colors"
          >
            <X className="w-6 h-6" style={{ color: '#7F8C8D' }} />
          </button>
        </div>

        {/* Tabs */}
        <div className="flex border-b" style={{ borderColor: '#E5E7EB' }}>
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className="px-6 py-3 font-medium transition-all relative"
              style={{
                color: activeTab === tab.id ? '#2C3E50' : '#7F8C8D',
              }}
            >
              {tab.label}
              {activeTab === tab.id && (
                <div
                  className="absolute bottom-0 left-0 right-0 h-0.5"
                  style={{ backgroundColor: '#FF6B4A' }}
                />
              )}
            </button>
          ))}
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {activeTab === 'overview' && (
            <div className="space-y-6">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm mb-1" style={{ color: '#7F8C8D' }}>Incident Date</p>
                  <p className="font-medium flex items-center" style={{ color: '#2C3E50' }}>
                    <Calendar className="w-4 h-4 mr-2" />
                    {formatDate(displayClaim.incident_date)}
                  </p>
                </div>
                <div>
                  <p className="text-sm mb-1" style={{ color: '#7F8C8D' }}>Submitted Date</p>
                  <p className="font-medium flex items-center" style={{ color: '#2C3E50' }}>
                    <Clock className="w-4 h-4 mr-2" />
                    {formatDateTime(displayClaim.submitted_date)}
                  </p>
                </div>
                <div>
                  <p className="text-sm mb-1" style={{ color: '#7F8C8D' }}>Location</p>
                  <p className="font-medium flex items-center" style={{ color: '#2C3E50' }}>
                    <MapPin className="w-4 h-4 mr-2" />
                    {displayClaim.incident_location || 'N/A'}
                  </p>
                </div>
                <div>
                  <p className="text-sm mb-1" style={{ color: '#7F8C8D' }}>Claim Type</p>
                  <p className="font-medium" style={{ color: '#2C3E50' }}>
                    {displayClaim.claim_type}
                  </p>
                </div>
                <div>
                  <p className="text-sm mb-1" style={{ color: '#7F8C8D' }}>Claimed Amount</p>
                  <p className="text-xl font-bold" style={{ color: '#2C3E50' }}>
                    ${parseFloat(displayClaim.claimed_amount || 0).toLocaleString()}
                  </p>
                </div>
                <div>
                  <p className="text-sm mb-1" style={{ color: '#7F8C8D' }}>Estimated Settlement</p>
                  <p className="text-xl font-bold" style={{ color: '#10B981' }}>
                    ${parseFloat(estimatedCost).toLocaleString()}
                  </p>
                </div>
              </div>

              <div>
                <p className="text-sm mb-2" style={{ color: '#7F8C8D' }}>Description</p>
                <p className="p-4 rounded-lg" style={{ backgroundColor: '#F8F9FA', color: '#2C3E50' }}>
                  {displayClaim.incident_description || 'No description provided'}
                </p>
              </div>

              {/* AI Processing Summary */}
              {aiResult && (
                <div className="p-4 rounded-lg border" style={{ 
                  borderColor: isApproved ? '#10B981' : isRejected ? '#EF4444' : '#F59E0B',
                  backgroundColor: isApproved ? '#D1FAE5' : isRejected ? '#FEE2E2' : '#FEF3C7'
                }}>
                  <div className="flex items-start">
                    {isApproved ? (
                      <CheckCircle className="w-5 h-5 mr-3 flex-shrink-0 mt-0.5" style={{ color: '#10B981' }} />
                    ) : isRejected ? (
                      <XCircle className="w-5 h-5 mr-3 flex-shrink-0 mt-0.5" style={{ color: '#EF4444' }} />
                    ) : (
                      <AlertTriangle className="w-5 h-5 mr-3 flex-shrink-0 mt-0.5" style={{ color: '#F59E0B' }} />
                    )}
                    <div className="flex-1">
                      <p className="font-bold mb-2" style={{ color: '#2C3E50' }}>
                        AI Recommendation: {recommendation}
                      </p>
                      <p className="text-sm mb-2" style={{ color: '#7F8C8D' }}>
                        {aiResult.processing_summary?.reasoning}
                      </p>
                      <div className="flex items-center gap-4 mt-3 text-sm">
                        <span style={{ color: '#7F8C8D' }}>
                          Priority: <strong style={{ color: '#2C3E50' }}>{aiResult.processing_summary?.priority}</strong>
                        </span>
                        <span style={{ color: '#7F8C8D' }}>
                          Confidence: <strong style={{ color: '#2C3E50' }}>{aiResult.processing_summary?.confidence}</strong>
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Timeline */}
              <div>
                <h3 className="font-bold mb-4" style={{ color: '#2C3E50' }}>Claim Timeline</h3>
                <div className="space-y-4">
                  {getTimelineEvents().map((item, index) => {
                    const Icon = item.icon;
                    return (
                      <div key={index} className="flex items-start">
                        <div className="flex flex-col items-center mr-4">
                          <div
                            className="w-8 h-8 rounded-full flex items-center justify-center"
                            style={{
                              backgroundColor: item.status === 'complete' ? '#D1FAE5' :
                                item.status === 'active' ? '#FEF3C7' : '#F3F4F6',
                              color: item.status === 'complete' ? '#10B981' :
                                item.status === 'active' ? '#F59E0B' : '#9CA3AF'
                            }}
                          >
                            <Icon className="w-4 h-4" />
                          </div>
                          {index < getTimelineEvents().length - 1 && (
                            <div
                              className="w-0.5 h-12"
                              style={{ backgroundColor: '#E5E7EB' }}
                            />
                          )}
                        </div>
                        <div className="flex-1 pb-4">
                          <p className="font-medium" style={{ color: '#2C3E50' }}>{item.event}</p>
                          <p className="text-sm" style={{ color: '#7F8C8D' }}>{item.date}</p>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          )}

          {activeTab === 'policyholder' && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm mb-1" style={{ color: '#7F8C8D' }}>Full Name</p>
                  <p className="font-medium flex items-center" style={{ color: '#2C3E50' }}>
                    <User className="w-4 h-4 mr-2" />
                    {displayClaim.policyholder_name || 'N/A'}
                  </p>
                </div>
                <div>
                  <p className="text-sm mb-1" style={{ color: '#7F8C8D' }}>Policy Number</p>
                  <p className="font-medium flex items-center" style={{ color: '#2C3E50' }}>
                    <FileText className="w-4 h-4 mr-2" />
                    {displayClaim.policy_number || 'N/A'}
                  </p>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'vehicle' && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm mb-1" style={{ color: '#7F8C8D' }}>Vehicle</p>
                  <p className="font-medium flex items-center" style={{ color: '#2C3E50' }}>
                    <Car className="w-4 h-4 mr-2" />
                    {displayClaim.vehicle_display || 'N/A'}
                  </p>
                </div>
                <div>
                  <p className="text-sm mb-1" style={{ color: '#7F8C8D' }}>Claim Type</p>
                  <p className="font-medium" style={{ color: '#2C3E50' }}>
                    {displayClaim.claim_type || 'N/A'}
                  </p>
                </div>
                <div>
                  <p className="text-sm mb-1" style={{ color: '#7F8C8D' }}>Severity</p>
                  <p className="font-medium" style={{ color: '#2C3E50' }}>
                    {displayClaim.severity || 'N/A'}
                  </p>
                </div>
                <div>
                  <p className="text-sm mb-1" style={{ color: '#7F8C8D' }}>Police Report Filed</p>
                  <p className="font-medium" style={{ color: '#2C3E50' }}>
                    {displayClaim.police_report_filed ? 'Yes' : 'No'}
                  </p>
                </div>
              </div>

              <div>
                <p className="text-sm mb-2" style={{ color: '#7F8C8D' }}>Damage Description</p>
                <p className="p-4 rounded-lg" style={{ backgroundColor: '#F8F9FA', color: '#2C3E50' }}>
                  {displayClaim.incident_description || 'No damage description provided'}
                </p>
              </div>

              <div className="grid grid-cols-3 gap-4">
                <div className="p-3 rounded-lg" style={{ backgroundColor: '#F8F9FA' }}>
                  <p className="text-xs mb-1" style={{ color: '#7F8C8D' }}>Vehicles Involved</p>
                  <p className="text-lg font-bold" style={{ color: '#2C3E50' }}>
                    {displayClaim.number_of_vehicles_involved || 0}
                  </p>
                </div>
                <div className="p-3 rounded-lg" style={{ backgroundColor: '#F8F9FA' }}>
                  <p className="text-xs mb-1" style={{ color: '#7F8C8D' }}>Injuries</p>
                  <p className="text-lg font-bold" style={{ color: '#2C3E50' }}>
                    {displayClaim.number_of_injuries || 0}
                  </p>
                </div>
                <div className="p-3 rounded-lg" style={{ backgroundColor: '#F8F9FA' }}>
                  <p className="text-xs mb-1" style={{ color: '#7F8C8D' }}>Witnesses</p>
                  <p className="text-lg font-bold" style={{ color: '#2C3E50' }}>
                    {displayClaim.number_of_witnesses || 0}
                  </p>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'fraud' && (
            <div className="space-y-6">
              <div className="flex items-center justify-between p-4 rounded-lg" style={{ backgroundColor: '#F8F9FA' }}>
                <div>
                  <p className="text-sm mb-1" style={{ color: '#7F8C8D' }}>Fraud Risk Level</p>
                  <p className="text-2xl font-bold" style={{ color: riskInfo.color }}>
                    {riskInfo.level}
                  </p>
                </div>
                <div className="text-right">
                  <p className="text-sm mb-1" style={{ color: '#7F8C8D' }}>Fraud Score</p>
                  <p className="text-2xl font-bold" style={{ color: '#2C3E50' }}>
                    {(fraudScore * 100).toFixed(1)}%
                  </p>
                </div>
              </div>

              <div>
                <h3 className="font-bold mb-3" style={{ color: '#2C3E50' }}>Risk Indicators</h3>
                <div className="space-y-2">
                  {fraudScore > 0.5 ? (
                    <>
                      <div className="flex items-start p-3 rounded-lg" style={{ backgroundColor: '#FEE2E2' }}>
                        <AlertTriangle className="w-5 h-5 mr-3 flex-shrink-0 mt-0.5" style={{ color: '#EF4444' }} />
                        <div>
                          <p className="font-medium" style={{ color: '#2C3E50' }}>High Risk Detected</p>
                          <p className="text-sm" style={{ color: '#7F8C8D' }}>
                            ML model has flagged this claim as potentially fraudulent
                          </p>
                        </div>
                      </div>
                      {aiResult?.fraud_analysis?.risk_factors && 
                       Array.isArray(aiResult.fraud_analysis.risk_factors) &&
                       aiResult.fraud_analysis.risk_factors.map((factor, index) => (
                        <div key={index} className="flex items-start p-3 rounded-lg" style={{ backgroundColor: '#FEE2E2' }}>
                          <AlertTriangle className="w-5 h-5 mr-3 flex-shrink-0 mt-0.5" style={{ color: '#EF4444' }} />
                          <div>
                            <p className="text-sm" style={{ color: '#7F8C8D' }}>{factor}</p>
                          </div>
                        </div>
                      ))}
                    </>
                  ) : (
                    <div className="flex items-start p-3 rounded-lg" style={{ backgroundColor: '#D1FAE5' }}>
                      <CheckCircle className="w-5 h-5 mr-3 flex-shrink-0 mt-0.5" style={{ color: '#10B981' }} />
                      <div>
                        <p className="font-medium" style={{ color: '#2C3E50' }}>Normal Claim Pattern</p>
                        <p className="text-sm" style={{ color: '#7F8C8D' }}>
                          No unusual patterns detected by the ML model
                        </p>
                      </div>
                    </div>
                  )}
                </div>
              </div>

              <div className="p-4 rounded-lg border" style={{ borderColor: '#E5E7EB', backgroundColor: '#EBF5FF' }}>
                <div className="flex items-start">
                  <Info className="w-5 h-5 mr-3 flex-shrink-0 mt-0.5" style={{ color: '#3B82F6' }} />
                  <div>
                    <p className="font-medium mb-1" style={{ color: '#2C3E50' }}>ML Model Explanation</p>
                    <p className="text-sm" style={{ color: '#7F8C8D' }}>
                      {fraudScore > 0.5
                        ? 'The XGBoost ML model detected anomalies based on claim history, timing patterns, and documentation analysis.'
                        : 'The XGBoost ML model found this claim to be consistent with legitimate claims based on historical patterns and complete documentation.'}
                    </p>
                  </div>
                </div>
              </div>

              {!aiResult && (
                <div className="text-center">
                  <button
                    onClick={handleProcessWithAI}
                    disabled={isProcessing}
                    className="px-6 py-3 rounded-lg text-white font-medium disabled:opacity-50 transition-all hover:shadow-lg"
                    style={{ backgroundColor: '#10B981' }}
                  >
                    <Cpu className="w-5 h-5 inline mr-2" />
                    {isProcessing ? 'Processing...' : 'Run AI Analysis'}
                  </button>
                </div>
              )}
            </div>
          )}

          {activeTab === 'estimate' && (
            <div className="space-y-6">
              <div className="grid grid-cols-2 gap-4">
                <div className="p-4 rounded-lg" style={{ backgroundColor: '#F8F9FA' }}>
                  <p className="text-sm mb-1" style={{ color: '#7F8C8D' }}>Claimed Amount</p>
                  <p className="text-2xl font-bold" style={{ color: '#2C3E50' }}>
                    ${parseFloat(displayClaim.claimed_amount || 0).toLocaleString()}
                  </p>
                </div>
                <div className="p-4 rounded-lg" style={{ backgroundColor: '#D1FAE5' }}>
                  <p className="text-sm mb-1" style={{ color: '#7F8C8D' }}>AI Estimated Settlement</p>
                  <p className="text-2xl font-bold" style={{ color: '#10B981' }}>
                    ${parseFloat(estimatedCost).toLocaleString()}
                  </p>
                </div>
              </div>

              {aiResult && (
                <>
                  <div>
                    <h3 className="font-bold mb-3" style={{ color: '#2C3E50' }}>AI Decision</h3>
                    <div className="text-center p-6 rounded-lg" style={{ 
                      backgroundColor: isApproved ? '#D1FAE5' : isRejected ? '#FEE2E2' : '#FEF3C7'
                    }}>
                      <div className="flex items-center justify-center mb-2">
                        {isApproved ? (
                          <CheckCircle className="w-8 h-8" style={{ color: '#10B981' }} />
                        ) : isRejected ? (
                          <XCircle className="w-8 h-8" style={{ color: '#EF4444' }} />
                        ) : (
                          <AlertTriangle className="w-8 h-8" style={{ color: '#F59E0B' }} />
                        )}
                      </div>
                      <p className="text-2xl font-bold" style={{ 
                        color: isApproved ? '#065F46' : isRejected ? '#991B1B' : '#92400E'
                      }}>
                        {recommendation}
                      </p>
                      <p className="text-sm mt-2" style={{ color: '#7F8C8D' }}>
                        Confidence: {(confidenceScore * 100).toFixed(0)}%
                      </p>
                    </div>
                  </div>

                  <div>
                    <h3 className="font-bold mb-3" style={{ color: '#2C3E50' }}>AI Explanation</h3>
                    <div className="p-4 rounded-lg" style={{ backgroundColor: '#F8F9FA' }}>
                      <p className="text-sm mb-3" style={{ color: '#2C3E50' }}>
                        {aiResult.processing_summary?.reasoning || 'No detailed explanation provided'}
                      </p>
                      
                      {/* Action Items */}
                      {aiResult.action_items && aiResult.action_items.length > 0 && (
                        <div className="mt-4">
                          <p className="font-medium mb-2" style={{ color: '#2C3E50' }}>Required Actions:</p>
                          <ul className="space-y-2">
                            {aiResult.action_items.map((item, index) => (
                              <li key={index} className="flex items-start text-sm">
                                <span className="mr-2">•</span>
                                <div>
                                  <span className="font-medium" style={{ color: '#2C3E50' }}>{item.action}</span>
                                  <span style={{ color: '#7F8C8D' }}> - {item.reason}</span>
                                </div>
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Accept AI Decision Button */}
                  <div className="text-center">
                    <button
                      onClick={handleAcceptDecision}
                      className="px-6 py-3 rounded-lg text-white font-medium transition-all hover:shadow-lg"
                      style={{ backgroundColor: '#10B981' }}
                    >
                      <CheckCircle className="w-5 h-5 inline mr-2" />
                      Accept AI Decision
                    </button>
                  </div>
                </>
              )}

              {!aiResult && (
                <div className="text-center">
                  <button
                    onClick={handleProcessWithAI}
                    disabled={isProcessing}
                    className="px-6 py-3 rounded-lg text-white font-medium disabled:opacity-50 transition-all hover:shadow-lg"
                    style={{ backgroundColor: '#10B981' }}
                  >
                    <Cpu className="w-5 h-5 inline mr-2" />
                    {isProcessing ? 'Processing...' : 'Generate AI Estimate'}
                  </button>
                </div>
              )}

              {/* Override Form */}
              {aiResult && !showOverride && (
                <div className="text-center">
                  <button
                    onClick={() => setShowOverride(true)}
                    className="px-6 py-2 rounded-lg font-medium transition-colors"
                    style={{ backgroundColor: '#FEF3C7', color: '#92400E' }}
                  >
                    <Edit className="w-4 h-4 inline mr-2" />
                    Override AI Decision
                  </button>
                </div>
              )}

              {showOverride && (
                <div className="p-4 border rounded-lg" style={{ borderColor: '#E5E7EB' }}>
                  <label className="block text-sm font-medium mb-2" style={{ color: '#2C3E50' }}>
                    Reason for Override
                  </label>
                  <textarea
                    value={overrideReason}
                    onChange={(e) => setOverrideReason(e.target.value)}
                    className="w-full px-3 py-2 border rounded-lg text-sm mb-2"
                    style={{ borderColor: '#E5E7EB' }}
                    rows="3"
                    placeholder="Explain why you're overriding the AI decision..."
                  />
                  <div className="flex gap-2">
                    <button
                      onClick={handleOverrideDecision}
                      className="flex-1 py-2 px-4 rounded-lg text-white font-medium"
                      style={{ backgroundColor: '#EF4444' }}
                    >
                      Submit Override
                    </button>
                    <button
                      onClick={() => setShowOverride(false)}
                      className="flex-1 py-2 px-4 rounded-lg font-medium"
                      style={{ backgroundColor: '#F8F9FA', color: '#7F8C8D' }}
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Footer Actions */}
        <div className="flex items-center justify-end p-6 border-t gap-3" style={{ borderColor: '#E5E7EB' }}>
          {!aiResult && (
            <button
              onClick={handleProcessWithAI}
              disabled={isProcessing}
              className="px-6 py-2 rounded-lg text-white font-medium transition-all disabled:opacity-50"
              style={{ backgroundColor: '#10B981' }}
            >
              <Cpu className="w-4 h-4 inline mr-2" />
              {isProcessing ? 'Processing...' : 'Process with AI'}
            </button>
          )}
          <button
            onClick={onClose}
            className="px-6 py-2 rounded-lg font-medium transition-all"
            style={{ backgroundColor: '#2C3E50', color: 'white' }}
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}