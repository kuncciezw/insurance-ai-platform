import { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { api } from '../services/api';
import Sidebar from './Sidebar';
import { generateFraudExplanation } from '../services/geminiExplainer';
import EmbeddedLossAssessor from './EmbeddedLossAssessor';
import { useNotification } from './notifications/useNotification';
import { useCurrencyFormatter } from '../utils/currencyFormatter';
import { usePricingSettings } from '../contexts/PricingSettingsContext';
import {
  ArrowLeft, AlertTriangle, CheckCircle, XCircle, FileText, Shield,
  User, Car, DollarSign, Calendar, MapPin, Clock, Activity,
  ChevronRight, Loader2, CreditCard, Phone, Mail, Hash,
  TrendingUp, ShieldCheck, Star, Award, Navigation, Lock, Gauge,
  Zap, Wrench, Download, ExternalLink, X, RefreshCw,
  ArrowUp, ArrowDown, Minus, Calculator, BookOpen, Fingerprint,
  Sparkles,
} from 'lucide-react';

// ── Helpers ──────────────────────────────────────────────────────────────────
const fmtDate     = (s) => !s ? '—' : new Date(s).toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });
const fmtDateTime = (s) => !s ? '—' : new Date(s).toLocaleString('en-US', { year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
const fmtPct = (v) => `${(v * 100).toFixed(1)}%`;

const STATUS_PALETTE = {
  SUBMITTED:    { bg: '#DBEAFE', color: '#1E3A8A', dot: '#3B82F6' },
  UNDER_REVIEW: { bg: '#FEF3C7', color: '#92400E', dot: '#F59E0B' },
  APPROVED:     { bg: '#D1FAE5', color: '#065F46', dot: '#10B981' },
  REJECTED:     { bg: '#FEE2E2', color: '#991B1B', dot: '#EF4444' },
  PAID:         { bg: '#D1FAE5', color: '#065F46', dot: '#10B981' },
  CLOSED:       { bg: '#F3F4F6', color: '#6B7280', dot: '#9CA3AF' },
};

const SEVERITY_COLOR = { MINOR: '#10B981', MODERATE: '#F59E0B', MAJOR: '#EF4444', TOTAL_LOSS: '#7F1D1D' };
const CREDIT_COLORS  = {
  EXCELLENT: { bar: '#10B981', label: '#065F46', bg: '#D1FAE5' },
  GOOD:      { bar: '#3B82F6', label: '#1E40AF', bg: '#DBEAFE' },
  FAIR:      { bar: '#F59E0B', label: '#92400E', bg: '#FEF3C7' },
  POOR:      { bar: '#EF4444', label: '#991B1B', bg: '#FEE2E2' },
  VERY_POOR: { bar: '#DC2626', label: '#7F1D1D', bg: '#FEE2E2' },
};

const creditPct = (score) => Math.round(((score - 300) / (850 - 300)) * 100);

// ── UI Components ────────────────────────────────────────────────────────────
function SectionCard({ icon, title, accent = '#FF6B4A', children }) {
  return (
    <div className="bg-white rounded-2xl shadow-sm overflow-hidden">
      <div className="px-6 py-4 flex items-center justify-between border-b" style={{ borderColor: '#F3F4F6' }}>
        <div className="flex items-center gap-3">
          <div className="w-7 h-7 rounded-lg flex items-center justify-center flex-shrink-0"
               style={{ backgroundColor: `${accent}18` }}>
            <span style={{ color: accent }}>{icon}</span>
          </div>
          <h3 className="text-sm font-bold uppercase tracking-wider" style={{ color: '#2C3E50' }}>{title}</h3>
        </div>
      </div>
      <div className="p-6">{children}</div>
    </div>
  );
}

function SectionCardWithAction({ icon, title, action, accent = '#FF6B4A', children }) {
  return (
    <div className="bg-white rounded-2xl shadow-sm overflow-hidden">
      <div className="px-6 py-4 flex items-center justify-between border-b" style={{ borderColor: '#F3F4F6' }}>
        <div className="flex items-center gap-3">
          <div className="w-7 h-7 rounded-lg flex items-center justify-center flex-shrink-0"
               style={{ backgroundColor: `${accent}18` }}>
            <span style={{ color: accent }}>{icon}</span>
          </div>
          <h3 className="text-sm font-bold uppercase tracking-wider" style={{ color: '#2C3E50' }}>{title}</h3>
        </div>
        {action && <div>{action}</div>}
      </div>
      <div className="p-6">{children}</div>
    </div>
  );
}

function InfoRow({ icon, label, value, mono = false, highlight = false }) {
  return (
    <div className="flex items-center justify-between py-2 border-b last:border-0" style={{ borderColor: '#F8F9FA' }}>
      <div className="flex items-center gap-2 text-xs flex-shrink-0 mr-4" style={{ color: '#9CA3AF' }}>
        <span className="w-3.5 h-3.5 flex items-center">{icon}</span>
        {label && <span className="font-medium whitespace-nowrap">{label}</span>}
      </div>
      <span className={`text-sm font-semibold text-right truncate ${mono ? 'font-mono text-xs' : ''}`}
            style={{ color: highlight ? '#FF6B4A' : '#2C3E50' }}>
        {value ?? '—'}
      </span>
    </div>
  );
}

function BoolBadge({ value, trueLabel = 'Yes', falseLabel = 'No' }) {
  return (
    <span className="px-2 py-0.5 rounded-full text-xs font-bold"
          style={{ backgroundColor: value ? '#D1FAE5' : '#F3F4F6', color: value ? '#065F46' : '#9CA3AF' }}>
      {value ? trueLabel : falseLabel}
    </span>
  );
}

function FeatureRow({ feature, rank }) {
  const impact  = feature.impact_weight ?? feature.impact ?? 0;
  const absImp  = Math.abs(impact);
  const isRaise = impact > 0;
  const barW    = Math.min((absImp / 0.3) * 100, 100);

  return (
    <div className="py-2.5 border-b last:border-0" style={{ borderColor: '#F8F9FA' }}>
      <div className="flex items-center justify-between mb-1.5">
        <div className="flex items-center gap-2 min-w-0">
          <span className="text-xs font-mono w-5 text-center flex-shrink-0" style={{ color: '#9CA3AF' }}>{rank}</span>
          {isRaise
            ? <ArrowUp   className="w-3 h-3 flex-shrink-0" style={{ color: '#EF4444' }} />
            : <ArrowDown className="w-3 h-3 flex-shrink-0" style={{ color: '#10B981' }} />}
          <span className="text-sm font-medium truncate" style={{ color: '#2C3E50' }}>
            {feature.label || feature.feature}
          </span>
        </div>
        <span className="text-xs font-bold ml-4 flex-shrink-0"
              style={{ color: isRaise ? '#EF4444' : '#10B981' }}>
          {isRaise ? '+' : ''}{impact.toFixed(4)}
        </span>
      </div>
      <div className="ml-7 h-1 rounded-full" style={{ backgroundColor: '#F3F4F6' }}>
        <div className="h-1 rounded-full transition-all duration-500"
             style={{ width: `${barW}%`, backgroundColor: isRaise ? '#EF4444' : '#10B981', opacity: 0.7 }} />
      </div>
    </div>
  );
}

export function PlainEnglishFraudExplanation({
  claim,
  policyholder,
  vehicle,
  policy,
  fraudAnalysis,
  currency,
  fmtMoney,
}) {
  const [explanation,  setExplanation]  = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [error,        setError]        = useState(null);
 
  // Prevent duplicate calls on re-renders without real data changes.
  // The `key` prop on the parent call site handles forced refreshes.
  const didRunRef = useRef(false);
 
  useEffect(() => {
    if (!claim?.id || !fraudAnalysis || didRunRef.current) return;
    didRunRef.current = true;
    runGeneration();
  }, [claim, fraudAnalysis]); // eslint-disable-line
 
  async function runGeneration() {
    setIsGenerating(true);
    setError(null);
    setExplanation('');
 
    try {
      const text = await generateFraudExplanation({
        claim,
        policyholder,
        vehicle,
        policy,
        fraudAnalysis,
        currency,
        fmtMoney,
      });
 
      if (!text) throw new Error('Empty response received.');
      setExplanation(text.trim());
    } catch (err) {
      console.error('PlainEnglishFraudExplanation error:', err);
      setError('Could not generate the explanation — try clicking Re-analyse.');
    } finally {
      setIsGenerating(false);
    }
  }
 
  if (isGenerating) {
    return (
      <div className="flex flex-col items-center justify-center gap-3 py-8">
        <div
          className="w-9 h-9 rounded-full flex items-center justify-center animate-pulse"
          style={{ backgroundColor: '#FFF5F2' }}
        >
          <Sparkles className="w-4 h-4" style={{ color: '#FF6B4A' }} />
        </div>
        <div className="text-center">
          <p className="text-sm font-medium" style={{ color: '#2C3E50' }}>
            Generating explanation…
          </p>
          <p className="text-xs mt-0.5" style={{ color: '#9CA3AF' }}>
            Reading claim details
          </p>
        </div>
        <Loader2 className="w-4 h-4 animate-spin" style={{ color: '#FF6B4A' }} />
      </div>
    );
  }
 
  if (error) {
    return (
      <div
        className="flex items-start gap-3 p-4 rounded-xl"
        style={{ backgroundColor: '#FEF3C7' }}
      >
        <AlertTriangle className="w-4 h-4 flex-shrink-0 mt-0.5" style={{ color: '#D97706' }} />
        <p className="text-sm" style={{ color: '#92400E' }}>{error}</p>
      </div>
    );
  }
 
  if (!explanation) return null;
 
  const paragraphs = explanation.split(/\n{2,}/).filter((p) => p.trim());
 
  return (
    <div className="space-y-4">
      {paragraphs.map((para, i) => (
        <p key={i} className="text-sm leading-relaxed" style={{ color: '#374151' }}>
          {para.trim()}
        </p>
      ))}
      <p
        className="text-xs flex items-center gap-1.5 pt-2 border-t"
        style={{ color: '#D1D5DB', borderColor: '#F3F4F6' }}
      >
        <Sparkles className="w-3 h-3" />
        AI-generated summary — verify with the Technical View for exact SHAP values
      </p>
    </div>
  );
}

// ── Override Panel ───────────────────────────────────────────────────────────
function OverridePanel({ claim, onOverride, onClose, isOverriding }) {
  const options = claim.claim_status === 'APPROVED'
    ? [{ status: 'REJECTED', label: 'Reject',  color: '#EF4444', bg: '#FEE2E2' }]
    : claim.claim_status === 'REJECTED'
    ? [{ status: 'APPROVED', label: 'Approve', color: '#10B981', bg: '#D1FAE5' }]
    : [
        { status: 'APPROVED', label: 'Approve', color: '#10B981', bg: '#D1FAE5' },
        { status: 'REJECTED', label: 'Reject',  color: '#EF4444', bg: '#FEE2E2' },
      ];

  return (
    <div className="mt-4 p-4 rounded-xl border-2" style={{ borderColor: '#E5E7EB', backgroundColor: '#FAFAFA' }}>
      <div className="flex items-center justify-between mb-3">
        <p className="text-xs font-bold uppercase tracking-wider" style={{ color: '#7F8C8D' }}>Adjuster Override</p>
        <button onClick={onClose} className="p-1 rounded hover:bg-gray-100">
          <X className="w-3.5 h-3.5" style={{ color: '#9CA3AF' }} />
        </button>
      </div>
      <p className="text-xs mb-3" style={{ color: '#9CA3AF' }}>
        This will override the automated decision. The action is logged and auditable.
      </p>
      <div className="flex gap-2">
        {options.map(({ status, label, color, bg }) => (
          <button
            key={status}
            onClick={() => onOverride(status)}
            disabled={isOverriding}
            className="flex-1 py-2 rounded-xl text-xs font-bold transition-all disabled:opacity-50"
            style={{ backgroundColor: bg, color }}>
            {isOverriding ? 'Saving…' : label}
          </button>
        ))}
      </div>
    </div>
  );
}

// ── Main component ───────────────────────────────────────────────────────────
export default function ClaimDetail() {
  const { id }   = useParams();
  const navigate = useNavigate();
  const { fmtMoney } = useCurrencyFormatter();
  const { showNotification, NotificationContainer } = useNotification();

  const [claim,         setClaim]         = useState(null);
  const [policyholder,  setPolicyholder]  = useState(null);
  const [vehicle,       setVehicle]       = useState(null);
  const [policy,        setPolicy]        = useState(null);
  const [fraudAnalysis, setFraudAnalysis] = useState(null);
  const [isLoading,     setIsLoading]     = useState(true);
  const [activeTab,     setActiveTab]     = useState('overview');
  const [currency,      setCurrency]      = useState('USD');
  const { settings: pricingSettings }     = usePricingSettings();

  const [showTechnical,    setShowTechnical]    = useState(false);
  const [showOverridePanel, setShowOverridePanel] = useState(false);
  const [isOverriding,      setIsOverriding]      = useState(false);

  // ── PATCH 2: new state for explicit re-analysis ───────────────────────────
  const [isReanalysing, setIsReanalysing] = useState(false);

  useEffect(() => { if (id) loadAll(); }, [id]); // eslint-disable-line

  const loadAll = async () => {
    setIsLoading(true);
    try {
      const c = await api.getClaim(id);
      setClaim(c);
      if (c.currency) setCurrency(c.currency);

      const [ph, veh, pol] = await Promise.all([
        api.getPolicyholder(c.policyholder).catch(() => null),
        api.getVehicle(c.vehicle).catch(() => null),
        api.getPolicy(c.policy).catch(() => null),
      ]);
      setPolicyholder(ph);
      setVehicle(veh);
      setPolicy(pol);

      // ── PATCH 1: read stored fraud analysis — never re-runs the pipeline ─
      // Previously called api.detectFraud() which re-ran ML + saved raw ML
      // score over the correct combined (ML + document) score on every load.
      try {
        const fa = await api.getClaimFraudAnalysis(id);
        setFraudAnalysis(fa);
      } catch { /* non-fatal — fraud panel will be empty until Re-analyse */ }

    } catch {
      showNotification('Failed to load claim details', 'error');
    } finally {
      setIsLoading(false);
    }
  };

  // ── PATCH 3: explicit re-analysis handler ─────────────────────────────────
  // This is the ONLY place detectFraud is called. It runs the full ML +
  // document pipeline, saves the combined score, then refreshes the page data.
  const handleReanalyse = async () => {
    setIsReanalysing(true);
    try {
      const fa = await api.detectFraud({ claim_id: id });
      setFraudAnalysis(fa);
      // Reload claim so the updated fraud_score renders in the hero + overview
      const c = await api.getClaim(id);
      setClaim(c);
      showNotification('Analysis updated successfully', 'success');
    } catch (err) {
      showNotification('Re-analysis failed: ' + (err.message || 'Unknown error'), 'error');
    } finally {
      setIsReanalysing(false);
    }
  };

  // ── Override handler ──────────────────────────────────────────────────────
  const handleOverride = async (newStatus) => {
    setIsOverriding(true);
    try {
      await api.updateClaim(id, { claim_status: newStatus });
      showNotification(`Claim ${newStatus.toLowerCase()} by adjuster override`, 'success');
      await loadAll();
      setShowOverridePanel(false);
    } catch (err) {
      showNotification('Override failed: ' + (err.message || 'Unknown error'), 'error');
    } finally {
      setIsOverriding(false);
    }
  };

  // ── Guards ────────────────────────────────────────────────────────────────
  if (isLoading) {
    return (
      <div className="flex h-screen" style={{ backgroundColor: '#F8F9FA' }}>
        <Sidebar />
        <div className="flex-1 flex items-center justify-center">
          <Loader2 className="w-8 h-8 animate-spin" style={{ color: '#FF6B4A' }} />
        </div>
      </div>
    );
  }

  if (!claim) {
    return (
      <div className="flex h-screen" style={{ backgroundColor: '#F8F9FA' }}>
        <Sidebar />
        <div className="flex-1 flex items-center justify-center flex-col gap-4">
          <FileText className="w-12 h-12" style={{ color: '#E5E7EB' }} />
          <p className="font-bold" style={{ color: '#2C3E50' }}>Claim not found</p>
          <button onClick={() => navigate('/claims')}
                  className="px-4 py-2 rounded-lg text-sm font-semibold text-white"
                  style={{ backgroundColor: '#FF6B4A' }}>
            Back to Claims
          </button>
        </div>
      </div>
    );
  }

  // ── Derived values ────────────────────────────────────────────────────────
  const sp         = STATUS_PALETTE[claim.claim_status] || STATUS_PALETTE.SUBMITTED;
  const sevColor   = SEVERITY_COLOR[claim.severity] || '#7F8C8D';
  const creditC    = CREDIT_COLORS[policyholder?.credit_rating] || CREDIT_COLORS.FAIR;
  const creditSc   = policyholder?.credit_score || 650;
  const fraudScore = claim.fraud_score ?? 0;
  const isApproved = claim.claim_status === 'APPROVED' || claim.claim_status === 'PAID';
  const isRejected = claim.claim_status === 'REJECTED';

  const rejectThresh  = pricingSettings?.threshold_fraud_reject;
  const warningThresh = pricingSettings?.threshold_variance_warning;
  const riskLabel     = fraudScore >= rejectThresh  ? 'Critical risk'
                      : fraudScore >= warningThresh ? 'High risk'
                      : fraudScore >= 0.3           ? 'Moderate risk'
                      : 'Low risk';

  const explanation    = fraudAnalysis?.model_explanation ?? {};
  const riskIncreasers = explanation.risk_increasers ?? [];
  const riskDecreasers = explanation.risk_decreasers ?? [];
  const topFeatures    = explanation.top_features    ?? [];

  const tabs = [
    { id: 'overview',     label: 'Overview',       icon: <Activity   className="w-3.5 h-3.5" /> },
    { id: 'policyholder', label: 'Policyholder',   icon: <User       className="w-3.5 h-3.5" /> },
    { id: 'vehicle',      label: 'Vehicle',        icon: <Car        className="w-3.5 h-3.5" /> },
    { id: 'fraud',        label: 'Fraud Analysis', icon: <Shield     className="w-3.5 h-3.5" /> },
    { id: 'assessment',   label: 'Loss Assessment',icon: <Calculator className="w-3.5 h-3.5" /> },
  ];

  const timeline = [
    { date: fmtDateTime(claim.incident_date),  event: 'Incident occurred', icon: AlertTriangle, done: true },
    { date: fmtDateTime(claim.submitted_date), event: 'Claim submitted',   icon: FileText,      done: true },
    { date: fmtDateTime(claim.reviewed_date) || 'Auto-processed',
      event: isRejected ? 'Auto-rejected by System' : isApproved ? 'Auto-approved by System' : 'Under review',
      icon: isRejected ? XCircle : isApproved ? CheckCircle : Clock,
      done: !!claim.reviewed_date },
    ...(claim.claim_status === 'PAID' || claim.claim_status === 'CLOSED'
      ? [{ date: fmtDateTime(claim.closed_date) || '—', event: 'Payment completed', icon: DollarSign, done: true }]
      : []),
  ];

  return (
    <div className="flex h-screen overflow-hidden" style={{ backgroundColor: '#F8F9FA' }}>
      <Sidebar />
      <NotificationContainer />

      <div className="flex-1 overflow-y-auto overflow-x-hidden">

        {/* ── Hero ─────────────────────────────────────────────────────── */}
        <div className="relative px-8 pt-8 pb-6"
             style={{ background: 'linear-gradient(135deg,#1a1a2e 0%,#2C3E50 60%,#34495e 100%)' }}>
          <div className="absolute top-0 right-0 w-56 h-56 rounded-full pointer-events-none"
               style={{ backgroundColor: '#FF6B4A', opacity: 0.06, transform: 'translate(30%,-30%)' }} />

          <button onClick={() => navigate('/claims')}
                  className="flex items-center gap-2 mb-5 text-sm font-semibold hover:opacity-70 transition-opacity"
                  style={{ color: 'rgba(255,255,255,0.65)' }}>
            <ArrowLeft className="w-4 h-4" /> Back to Claims
          </button>

          <div className="flex items-start justify-between gap-4">
            <div className="flex items-start gap-4">
              <div className="w-12 h-12 rounded-2xl flex items-center justify-center flex-shrink-0"
                   style={{ backgroundColor: '#FF6B4A', boxShadow: '0 4px 20px rgba(255,107,74,.4)' }}>
                <FileText className="w-6 h-6 text-white" />
              </div>
              <div>
                <div className="flex items-center gap-3 flex-wrap mb-1">
                  <h1 className="text-2xl font-bold text-white">{claim.claim_number}</h1>
                  <span className="px-3 py-1 rounded-full text-xs font-bold flex items-center gap-1.5"
                        style={{ backgroundColor: sp.bg, color: sp.color }}>
                    <span className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: sp.dot }} />
                    {claim.claim_status?.replace('_', ' ')}
                  </span>
                  {claim.is_fraudulent && (
                    <span className="px-3 py-1 rounded-full text-xs font-bold flex items-center gap-1.5"
                          style={{ backgroundColor: '#FEE2E2', color: '#991B1B' }}>
                      <AlertTriangle className="w-3 h-3" /> Risk Flagged
                    </span>
                  )}
                </div>
                <p className="text-sm" style={{ color: 'rgba(255,255,255,0.55)' }}>
                  {claim.claim_type} ·
                  <span style={{ color: sevColor }}> {claim.severity}</span>
                </p>
                <p className="mt-0.5 text-sm" style={{ color: 'rgba(255,255,255,0.75)' }}>
                  {claim.policyholder_name || '—'}
                  {claim.vehicle_display && (
                    <span style={{ color: 'rgba(255,255,255,0.4)' }}> · {claim.vehicle_display}</span>
                  )}
                </p>
              </div>
            </div>

            <div className="text-right flex-shrink-0">
              <div className="flex items-center gap-2 justify-end mb-1">
                <span className="text-xs font-medium" style={{ color: 'rgba(255,255,255,0.5)' }}>Claimed Amount</span>
                <div className="flex gap-0.5 p-0.5 rounded-lg" style={{ backgroundColor: 'rgba(255,255,255,0.1)' }}>
                  {['USD', 'ZWG'].map((c) => (
                    <button key={c} onClick={() => setCurrency(c)}
                            className="px-2 py-0.5 rounded-md text-xs font-bold transition-all"
                            style={{ backgroundColor: currency === c ? '#FF6B4A' : 'transparent', color: currency === c ? 'white' : 'rgba(255,255,255,0.5)' }}>
                      {c}
                    </button>
                  ))}
                </div>
              </div>
              <p className="text-3xl font-bold text-white">{fmtMoney(claim.claimed_amount, currency)}</p>
              <p className="text-xs mt-1" style={{ color: 'rgba(255,255,255,0.35)' }}>{fmtDate(claim.incident_date)}</p>
            </div>
          </div>

          <div className="grid grid-cols-4 gap-3 mt-6">
            {[
              { label: 'Approved', value: fmtMoney(claim.approved_amount, currency) },
              { label: 'Paid',     value: fmtMoney(claim.paid_amount, currency) },
              { label: 'Auto Decision', value: isApproved ? '✓ Approved' : isRejected ? '✗ Rejected' : 'Processing…' },
              { label: 'Policy',   value: claim.policy_number || '—' },
            ].map(({ label, value }) => (
              <div key={label} className="rounded-xl px-4 py-3" style={{ backgroundColor: 'rgba(255,255,255,0.08)' }}>
                <p className="text-xs mb-1" style={{ color: 'rgba(255,255,255,0.45)' }}>{label}</p>
                <p className="text-base font-bold text-white truncate">{value}</p>
              </div>
            ))}
          </div>
        </div>

        {/* ── Tabs ─────────────────────────────────────────────────────── */}
        <div className="bg-white border-b sticky top-0 z-10" style={{ borderColor: '#E5E7EB' }}>
          <div className="px-8 flex">
            {tabs.map((tab) => (
              <button key={tab.id} onClick={() => setActiveTab(tab.id)}
                      className="flex items-center gap-2 px-5 py-4 text-sm font-semibold border-b-2 transition-all whitespace-nowrap"
                      style={{
                        borderColor: activeTab === tab.id ? '#FF6B4A' : 'transparent',
                        color:       activeTab === tab.id ? '#FF6B4A' : '#7F8C8D',
                      }}>
                {tab.icon}{tab.label}
              </button>
            ))}
          </div>
        </div>

        {/* ── Tab Content ──────────────────────────────────────────────── */}
        <div className="p-8">

          {/* ══ OVERVIEW ═════════════════════════════════════════════════ */}
          {activeTab === 'overview' && (
            <div className="grid grid-cols-3 gap-6">
              <div className="col-span-2 space-y-6">

                <SectionCard icon={<AlertTriangle className="w-4 h-4" />} title="Incident Details" accent="#EF4444">
                  <div className="grid grid-cols-2 gap-x-8">
                    <InfoRow icon={<Calendar className="w-3.5 h-3.5" />}      label="Date"           value={fmtDateTime(claim.incident_date)} />
                    <InfoRow icon={<MapPin className="w-3.5 h-3.5" />}        label="Location"       value={claim.incident_location} />
                    <InfoRow icon={<AlertTriangle className="w-3.5 h-3.5" />} label="Type"           value={claim.claim_type} />
                    <InfoRow icon={<Activity className="w-3.5 h-3.5" />}      label="Severity"       value={claim.severity} highlight />
                    <InfoRow icon={<CreditCard className="w-3.5 h-3.5" />}    label="Payment Method" value={claim.payment_method?.replace('_', ' ')} />
                    <InfoRow icon={<Clock className="w-3.5 h-3.5" />}         label="Days Open"      value={`${claim.days_since_submission ?? '—'} days`} />
                  </div>
                  {claim.incident_evidence && (
                    <div className="mt-4 pt-4 border-t" style={{ borderColor: '#F3F4F6' }}>
                      <p className="text-xs font-medium mb-2" style={{ color: '#9CA3AF' }}>Evidence File</p>
                      <div className="flex items-center gap-2 flex-wrap">
                        <a href={claim.incident_evidence} target="_blank" rel="noopener noreferrer"
                           className="inline-flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-semibold text-white transition-opacity hover:opacity-90"
                           style={{ backgroundColor: '#FF6B4A' }}>
                          <ExternalLink className="w-3.5 h-3.5" /> View Evidence
                        </a>
                        <a href={claim.incident_evidence} download
                           className="inline-flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-semibold transition-colors"
                           style={{ backgroundColor: '#F3F4F6', color: '#6B7280' }}>
                          <Download className="w-3.5 h-3.5" /> Download
                        </a>
                      </div>
                    </div>
                  )}
                </SectionCard>

                <SectionCard icon={<Clock className="w-4 h-4" />} title="Claim Timeline" accent="#8B5CF6">
                  <div className="space-y-2">
                    {timeline.map((item, i) => {
                      const Icon = item.icon;
                      return (
                        <div key={i} className="flex items-start gap-3">
                          <div className="flex flex-col items-center">
                            <div className="w-7 h-7 rounded-full flex items-center justify-center"
                                 style={{ backgroundColor: item.done ? '#D1FAE5' : '#F3F4F6',
                                          color:           item.done ? '#10B981'  : '#9CA3AF' }}>
                              <Icon className="w-3.5 h-3.5" />
                            </div>
                            {i < timeline.length - 1 && (
                              <div className="w-px h-6 mt-1" style={{ backgroundColor: '#E5E7EB' }} />
                            )}
                          </div>
                          <div className="pt-1 pb-2">
                            <p className="text-sm font-semibold" style={{ color: '#2C3E50' }}>{item.event}</p>
                            <p className="text-xs mt-0.5" style={{ color: '#9CA3AF' }}>{item.date}</p>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </SectionCard>
              </div>

              <div className="space-y-6">
                <SectionCard icon={<Shield className="w-4 h-4" />} title="Risk Assessment" accent="#EF4444">
                  <div className="text-center py-4">
                    <p className="text-4xl font-bold" style={{ color: fraudScore > 0.5 ? '#EF4444' : '#10B981' }}>
                      {fmtPct(fraudScore)}
                    </p>
                    <p className="text-xs mt-1 font-medium" style={{ color: '#9CA3AF' }}>{riskLabel}</p>
                    <div className="mt-3">
                      <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold"
                            style={{
                              backgroundColor: isApproved ? '#D1FAE5' : isRejected ? '#FEE2E2' : '#FFFBEB',
                              color: isApproved ? '#065F46' : isRejected ? '#991B1B' : '#92400E'
                            }}>
                        {isApproved ? <CheckCircle className="w-3.5 h-3.5" /> : isRejected ? <XCircle className="w-3.5 h-3.5" /> : <Clock className="w-3.5 h-3.5" />}
                        {isApproved ? 'Auto-Approved' : isRejected ? 'Auto-Rejected' : 'Under Review'}
                      </span>
                    </div>
                  </div>
                  <div className="w-full h-2 rounded-full mb-4" style={{ backgroundColor: '#F3F4F6' }}>
                    <div className="h-2 rounded-full" style={{
                      width: fmtPct(fraudScore),
                      backgroundColor: fraudScore > 0.5 ? '#EF4444' : '#10B981',
                    }} />
                  </div>
                  <button onClick={() => setActiveTab('fraud')}
                          className="w-full text-xs font-semibold py-2 rounded-xl transition-colors flex items-center justify-center gap-1.5"
                          style={{ backgroundColor: '#F8F9FA', color: '#7F8C8D' }}>
                    Full Risk Analysis <ChevronRight className="w-3.5 h-3.5" />
                  </button>
                </SectionCard>

                {policy && (
                  <SectionCard icon={<FileText className="w-4 h-4" />} title="Policy" accent="#3B82F6">
                    <InfoRow icon={<Hash className="w-3.5 h-3.5" />}        label="Number"   value={policy.policy_number} mono />
                    <InfoRow icon={<Activity className="w-3.5 h-3.5" />}    label="Type"     value={policy.policy_type} />
                    <InfoRow icon={<ShieldCheck className="w-3.5 h-3.5" />} label="Coverage" value={policy.coverage_level} />
                    <InfoRow icon={<DollarSign className="w-3.5 h-3.5" />}  label="Premium"  value={fmtMoney(policy.premium_amount, currency)} highlight />
                    <button onClick={() => navigate(`/policies/${policy.id}`)}
                            className="mt-3 w-full flex items-center justify-center gap-1.5 py-2 rounded-xl text-xs font-semibold"
                            style={{ backgroundColor: '#EFF6FF', color: '#3B82F6' }}>
                      View Policy <ChevronRight className="w-3.5 h-3.5" />
                    </button>
                  </SectionCard>
                )}

                <button
                  onClick={() => setActiveTab('assessment')}
                  className="w-full p-4 rounded-2xl flex items-center gap-3 transition-all text-left shadow-sm"
                  style={{ backgroundColor: '#FFF5F2', border: '1.5px solid #FFD5C8' }}
                  onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = '#FFE8E0')}
                  onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = '#FFF5F2')}>
                  <div className="w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0"
                       style={{ backgroundColor: '#FF6B4A' }}>
                    <Calculator className="w-4 h-4 text-white" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-bold" style={{ color: '#2C3E50' }}>Run Loss Assessment</p>
                    <p className="text-xs mt-0.5" style={{ color: '#9CA3AF' }}>AI-powered cost estimation</p>
                  </div>
                  <ChevronRight className="w-4 h-4 flex-shrink-0" style={{ color: '#FF6B4A' }} />
                </button>
              </div>
            </div>
          )}

          {/* ══ FRAUD ANALYSIS ═══════════════════════════════════════════ */}
          {activeTab === 'fraud' && (
            <div className="grid grid-cols-3 gap-6">

              <div className="col-span-2 space-y-6">

                <SectionCard icon={<Shield className="w-4 h-4" />} title="Automated Decision" accent="#9CA3AF">

                  {/* ── PATCH 4: Re-analyse + Override buttons side by side ── */}
                  <div className="flex items-center justify-between mb-4">
                    <div>
                      <p className="text-sm font-bold text-gray-800">
                        {isApproved ? 'Approved' : isRejected ? 'Rejected' : 'Under Review'}
                      </p>
                      <p className="text-xs text-gray-500 mt-1">
                        Risk score: {fmtPct(fraudScore)}
                      </p>
                    </div>

                    <div className="flex items-center gap-2">
                      {/* Re-analyse — runs full ML + document pipeline on demand */}
                      <button
                        onClick={handleReanalyse}
                        disabled={isReanalysing}
                        className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors disabled:opacity-50">
                        {isReanalysing
                          ? <><Loader2 className="w-3 h-3 animate-spin" /> Analysing…</>
                          : <><RefreshCw className="w-3 h-3" /> Re-analyse</>}
                      </button>

                      {/* Override — unchanged */}
                      <button
                        onClick={() => setShowOverridePanel((p) => !p)}
                        className="px-3 py-1.5 text-xs font-semibold border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors">
                        {showOverridePanel ? 'Cancel' : 'Override Decision'}
                      </button>
                    </div>
                  </div>

                  {showOverridePanel && (
                    <div className="mb-4">
                      <OverridePanel
                        claim={claim}
                        onOverride={handleOverride}
                        onClose={() => setShowOverridePanel(false)}
                        isOverriding={isOverriding}
                      />
                    </div>
                  )}

                  {claim.fraud_reason && (
                    <div className="text-sm border-t pt-4">
                      <p className="text-xs font-bold text-gray-500 uppercase tracking-wider mb-1">Reason</p>
                      <p className="text-gray-700">{claim.fraud_reason}</p>
                    </div>
                  )}
                </SectionCard>

                {topFeatures.length > 0 && (
                  <SectionCardWithAction
                    icon={<Activity className="w-4 h-4" />}
                    title="Why the System Made This Decision"
                    accent="#3B82F6"
                    action={
                      <button
                        onClick={() => setShowTechnical(t => !t)}
                        className="text-xs px-3 py-1.5 rounded-lg border transition-colors flex items-center gap-1.5"
                        style={{ borderColor: '#E5E7EB', color: '#7F8C8D', backgroundColor: '#F9FAFB' }}>
                        {showTechnical ? <BookOpen className="w-3.5 h-3.5" /> : <Fingerprint className="w-3.5 h-3.5" />}
                        {showTechnical ? 'Plain English View' : 'Technical View'}
                      </button>
                    }>
                    {showTechnical ? (
                      <div>
                        {riskIncreasers.length > 0 && (
                          <div className="mb-5">
                            <p className="text-xs font-bold uppercase tracking-wider mb-2 flex items-center gap-1.5"
                               style={{ color: '#EF4444' }}>
                              <ArrowUp className="w-3.5 h-3.5" /> Raised Risk
                            </p>
                            {riskIncreasers.map((f, i) => <FeatureRow key={f.feature} feature={f} rank={f.rank ?? i + 1} />)}
                          </div>
                        )}
                        {riskDecreasers.length > 0 && (
                          <div>
                            <p className="text-xs font-bold uppercase tracking-wider mb-2 flex items-center gap-1.5"
                               style={{ color: '#10B981' }}>
                              <ArrowDown className="w-3.5 h-3.5" /> Lowered Risk
                            </p>
                            {riskDecreasers.map((f, i) => <FeatureRow key={f.feature} feature={f} rank={f.rank ?? i + 1} />)}
                          </div>
                        )}
                      </div>
                    ) : (
                      <PlainEnglishFraudExplanation
                        key={`${claim.id}-${claim.fraud_score}`}
                        claim={claim}
                        policyholder={policyholder}
                        vehicle={vehicle}
                        policy={policy}
                        fraudAnalysis={fraudAnalysis}
                        currency={currency}
                        fmtMoney={fmtMoney}
                      />
                    )}
                  </SectionCardWithAction>
                )}
              </div>

              <div className="space-y-6">
                <SectionCard icon={<FileText className="w-4 h-4" />} title="Claim Reference" accent="#9CA3AF">
                  <InfoRow icon={<Hash className="w-3.5 h-3.5" />}       label="Number"    value={claim.claim_number} mono />
                  <InfoRow icon={<Calendar className="w-3.5 h-3.5" />}   label="Submitted" value={fmtDate(claim.submitted_date)} />
                  <InfoRow icon={<Clock className="w-3.5 h-3.5" />}      label="Reviewed"  value={fmtDate(claim.reviewed_date)} />
                  <InfoRow icon={<DollarSign className="w-3.5 h-3.5" />} label="Approved"  value={fmtMoney(claim.approved_amount, currency)} />
                </SectionCard>

                {fraudAnalysis?.risk_factors?.length > 0 &&
                  fraudAnalysis.risk_factors[0] !== 'No significant risk factors detected' && (
                  <SectionCard icon={<AlertTriangle className="w-4 h-4" />} title="Risk Signals" accent="#F59E0B">
                    <div className="space-y-2">
                      {fraudAnalysis.risk_factors.map((factor, i) => (
                        <div key={i} className="flex items-start gap-3 py-2 border-b last:border-0"
                             style={{ borderColor: '#F8F9FA' }}>
                          <Minus className="w-3.5 h-3.5 flex-shrink-0 mt-0.5" style={{ color: '#F59E0B' }} />
                          <p className="text-sm" style={{ color: '#2C3E50' }}>{factor}</p>
                        </div>
                      ))}
                    </div>
                  </SectionCard>
                )}
              </div>
            </div>
          )}

          {/* ══ POLICYHOLDER ══════════════════════════════════════════════ */}
          {activeTab === 'policyholder' && policyholder && (
            <div className="grid grid-cols-2 gap-6">
              <SectionCard icon={<User className="w-4 h-4" />} title="Personal Information" accent="#3B82F6">
                <div className="flex items-center gap-4 mb-5 p-3 rounded-xl" style={{ backgroundColor: '#F8F9FA' }}>
                  <div className="w-11 h-11 rounded-full flex items-center justify-center text-base font-bold text-white flex-shrink-0"
                       style={{ backgroundColor: '#FF6B4A' }}>
                    {(policyholder.first_name?.[0] || '') + (policyholder.last_name?.[0] || '')}
                  </div>
                  <div>
                    <p className="font-bold text-sm" style={{ color: '#2C3E50' }}>
                      {policyholder.full_name || `${policyholder.first_name} ${policyholder.last_name}`}
                    </p>
                    <p className="text-xs" style={{ color: '#9CA3AF' }}>{policyholder.policy_holder_id}</p>
                  </div>
                </div>
                <InfoRow icon={<Calendar className="w-3.5 h-3.5" />}   label="Date of Birth"    value={fmtDate(policyholder.date_of_birth)} />
                <InfoRow icon={<User className="w-3.5 h-3.5" />}       label="Gender"           value={policyholder.gender === 'M' ? 'Male' : policyholder.gender === 'F' ? 'Female' : 'Other'} />
                <InfoRow icon={<Award className="w-3.5 h-3.5" />}      label="Age"              value={`${policyholder.age} years`} />
                <InfoRow icon={<Star className="w-3.5 h-3.5" />}       label="Marital Status"   value={policyholder.marital_status} />
                <InfoRow icon={<Activity className="w-3.5 h-3.5" />}   label="Occupation"       value={policyholder.occupation} />
                <InfoRow icon={<DollarSign className="w-3.5 h-3.5" />} label="Annual Income"    value={fmtMoney(policyholder.annual_income, currency)} />
                <InfoRow icon={<Clock className="w-3.5 h-3.5" />}      label="Years w/ Company" value={`${policyholder.years_with_company} years`} />
              </SectionCard>

              <div className="space-y-6">
                <SectionCard icon={<Mail className="w-4 h-4" />} title="Contact" accent="#8B5CF6">
                  <InfoRow icon={<Mail className="w-3.5 h-3.5" />}       label="Email"   value={policyholder.email} />
                  <InfoRow icon={<Phone className="w-3.5 h-3.5" />}      label="Phone"   value={policyholder.phone_number} />
                  <InfoRow icon={<MapPin className="w-3.5 h-3.5" />}     label="Address" value={policyholder.address_line1} />
                  <InfoRow icon={<MapPin className="w-3.5 h-3.5" />}     label="City"    value={`${policyholder.city}, ${policyholder.state}`} />
                  <InfoRow icon={<Navigation className="w-3.5 h-3.5" />} label="Country" value={policyholder.country} />
                </SectionCard>

                <SectionCard icon={<CreditCard className="w-4 h-4" />} title="Credit & Licenses" accent="#F59E0B">
                  <div className="mb-4">
                    <div className="flex items-center justify-between mb-1.5">
                      <span className="text-xs font-medium" style={{ color: '#9CA3AF' }}>Credit Score</span>
                      <div className="flex items-center gap-2">
                        <span className="text-xs px-2 py-0.5 rounded-full font-bold"
                              style={{ backgroundColor: creditC.bg, color: creditC.label }}>
                          {policyholder.credit_rating?.replace('_', ' ')}
                        </span>
                        <span className="text-sm font-bold" style={{ color: creditC.label }}>{creditSc}</span>
                      </div>
                    </div>
                    <div className="w-full h-1.5 rounded-full" style={{ backgroundColor: '#E5E7EB' }}>
                      <div className="h-1.5 rounded-full"
                           style={{ width: `${creditPct(creditSc)}%`, backgroundColor: creditC.bar }} />
                    </div>
                  </div>
                  <InfoRow icon={<CheckCircle className="w-3.5 h-3.5" />} label="Driving License"   value={<BoolBadge value={policyholder.has_driving_license} />} />
                  <InfoRow icon={<CheckCircle className="w-3.5 h-3.5" />} label="Defensive License" value={<BoolBadge value={policyholder.has_defensive_license} />} />
                  <InfoRow icon={<CheckCircle className="w-3.5 h-3.5" />} label="Medical License"   value={<BoolBadge value={policyholder.is_medical_license_valid} trueLabel="Valid" falseLabel="Invalid" />} />
                </SectionCard>
              </div>
            </div>
          )}

          {/* ══ VEHICLE ══════════════════════════════════════════════════ */}
          {activeTab === 'vehicle' && vehicle && (
            <div className="grid grid-cols-2 gap-6">
              <SectionCard icon={<Car className="w-4 h-4" />} title="Vehicle Identity" accent="#10B981">
                <div className="rounded-xl p-4 mb-5 text-center"
                     style={{ backgroundColor: '#F0FDF4', border: '1.5px solid #A7F3D0' }}>
                  <Car className="w-8 h-8 mx-auto mb-2" style={{ color: '#10B981' }} />
                  <p className="text-base font-bold" style={{ color: '#065F46' }}>
                    {vehicle.manufacture_year} {vehicle.make} {vehicle.model}
                  </p>
                  <p className="text-xs mt-0.5" style={{ color: '#6EE7B7' }}>{vehicle.vehicle_type}</p>
                </div>
                <InfoRow icon={<Hash className="w-3.5 h-3.5" />}       label="VIN"          value={vehicle.vin} mono />
                <InfoRow icon={<Hash className="w-3.5 h-3.5" />}       label="Registration" value={vehicle.registration_number} mono />
                <InfoRow icon={<Calendar className="w-3.5 h-3.5" />}   label="Year"         value={vehicle.manufacture_year} />
                <InfoRow icon={<Activity className="w-3.5 h-3.5" />}   label="Vehicle Age"  value={`${vehicle.vehicle_age} years`} />
                <InfoRow icon={<DollarSign className="w-3.5 h-3.5" />} label="Market Value" value={fmtMoney(vehicle.market_value, currency)} highlight />
              </SectionCard>

              <div className="space-y-6">
                <SectionCard icon={<Wrench className="w-4 h-4" />} title="Specifications" accent="#6366F1">
                  <InfoRow icon={<Gauge className="w-3.5 h-3.5" />}    label="Engine"   value={`${vehicle.engine_capacity} CC`} />
                  <InfoRow icon={<Zap className="w-3.5 h-3.5" />}      label="Fuel"     value={vehicle.fuel_type} />
                  <InfoRow icon={<User className="w-3.5 h-3.5" />}     label="Seats"    value={vehicle.seating_capacity} />
                  <InfoRow icon={<Activity className="w-3.5 h-3.5" />} label="Odometer" value={`${vehicle.odometer_reading?.toLocaleString()} mi`} />
                </SectionCard>

                <SectionCard icon={<Lock className="w-4 h-4" />} title="Safety & Condition" accent="#EF4444">
                  <div className="grid grid-cols-2 gap-3">
                    {[
                      { key: 'has_anti_theft', label: 'Anti-Theft', icon: <Lock     className="w-4 h-4" />, invert: false },
                      { key: 'has_airbags',    label: 'Airbags',    icon: <Shield   className="w-4 h-4" />, invert: false },
                      { key: 'has_abs',        label: 'ABS Brakes', icon: <Activity className="w-4 h-4" />, invert: false },
                      { key: 'is_modified',    label: 'Modified',   icon: <Wrench   className="w-4 h-4" />, invert: true  },
                    ].map(({ key, label, icon, invert }) => {
                      const val      = vehicle[key];
                      const positive = invert ? !val : val;
                      return (
                        <div key={key} className="rounded-xl p-3 flex items-center gap-2.5"
                             style={{ backgroundColor: positive ? '#F0FDF4' : '#F8F9FA',
                                      border: `1px solid ${positive ? '#A7F3D0' : '#E5E7EB'}` }}>
                          <div className="w-7 h-7 rounded-lg flex items-center justify-center flex-shrink-0"
                               style={{ backgroundColor: positive ? '#D1FAE5' : '#E5E7EB',
                                        color:           positive ? '#10B981'  : '#9CA3AF' }}>{icon}</div>
                          <div>
                            <p className="text-xs font-semibold" style={{ color: '#2C3E50' }}>{label}</p>
                            <BoolBadge value={val} />
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </SectionCard>
              </div>
            </div>
          )}

          {/* ══ LOSS ASSESSMENT ══════════════════════════════════════════ */}
          {activeTab === 'assessment' && (
            <EmbeddedLossAssessor claim={claim} vehicle={vehicle} currency={currency} />
          )}

        </div>
      </div>
    </div>
  );
}