import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { api } from '../services/api';
import Sidebar from './Sidebar';
import { useCurrencyFormatter } from '../utils/currencyFormatter';
import { useNotification } from './notifications/useNotification';
import {
  ArrowLeft, Shield, User, Car, FileText, Calendar, DollarSign,
  AlertTriangle, CheckCircle, Clock, TrendingUp, ShieldCheck, Info,
  Phone, Mail, MapPin, CreditCard, Award, Loader2, ChevronRight,
  Zap, Star, Activity, Lock, Gauge, Wrench, Navigation, Hash,
} from 'lucide-react';

// ─── Constants ─────────────────────────────────────────────────────────────
const fmtDate = (dateStr) => {
  if (!dateStr) return '—';
  return new Date(dateStr).toLocaleDateString('en-US', {
    year: 'numeric', month: 'long', day: 'numeric',
  });
};

const STATUS_PALETTE = {
  ACTIVE:    { bg: '#D1FAE5', color: '#065F46', dot: '#10B981' },
  EXPIRED:   { bg: '#FEE2E2', color: '#991B1B', dot: '#EF4444' },
  CANCELLED: { bg: '#FEE2E2', color: '#991B1B', dot: '#EF4444' },
  SUSPENDED: { bg: '#FEF3C7', color: '#92400E', dot: '#F59E0B' },
  PENDING:   { bg: '#DBEAFE', color: '#1E40AF', dot: '#3B82F6' },
};

const CLAIM_STATUS_PALETTE = {
  SUBMITTED:    { bg: '#DBEAFE', color: '#1E40AF' },
  UNDER_REVIEW: { bg: '#FEF3C7', color: '#92400E' },
  APPROVED:     { bg: '#D1FAE5', color: '#065F46' },
  REJECTED:     { bg: '#FEE2E2', color: '#991B1B' },
  PAID:         { bg: '#D1FAE5', color: '#065F46' },
  CLOSED:       { bg: '#F3F4F6', color: '#6B7280' },
};

const CREDIT_COLORS = {
  EXCELLENT: { bar: '#10B981', label: '#065F46', bg: '#D1FAE5' },
  GOOD:      { bar: '#3B82F6', label: '#1E40AF', bg: '#DBEAFE' },
  FAIR:      { bar: '#F59E0B', label: '#92400E', bg: '#FEF3C7' },
  POOR:      { bar: '#EF4444', label: '#991B1B', bg: '#FEE2E2' },
  VERY_POOR: { bar: '#DC2626', label: '#7F1D1D', bg: '#FEE2E2' },
};

const creditPct = (score) => Math.round(((score - 300) / (850 - 300)) * 100);

// ─── Section Card ───────────────────────────────────────────────────────────
function SectionCard({ icon, title, accent = '#FF6B4A', children, badge }) {
  return (
    <div className="bg-white rounded-2xl shadow-sm overflow-hidden min-w-0">
      <div className="px-6 py-4 flex items-center justify-between border-b" style={{ borderColor: '#F3F4F6' }}>
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-xl flex items-center justify-center flex-shrink-0" style={{ backgroundColor: `${accent}15` }}>
            <span style={{ color: accent }}>{icon}</span>
          </div>
          <h3 className="text-sm font-bold uppercase tracking-wider" style={{ color: '#2C3E50' }}>{title}</h3>
        </div>
        {badge}
      </div>
      <div className="p-6">{children}</div>
    </div>
  );
}

// ─── Info Row ───────────────────────────────────────────────────────────────
function InfoRow({ icon, label, value, mono = false, highlight = false }) {
  return (
    <div className="flex items-center justify-between py-2 border-b last:border-0" style={{ borderColor: '#F8F9FA' }}>
      <div className="flex items-center gap-2 text-xs flex-shrink-0 mr-4" style={{ color: '#9CA3AF' }}>
        <span className="w-3.5 h-3.5 flex items-center justify-center flex-shrink-0">{icon}</span>
        {label && <span className="font-medium whitespace-nowrap">{label}</span>}
      </div>
      <span className={`text-sm font-semibold text-right min-w-0 truncate ${mono ? 'font-mono text-xs' : ''}`} style={{ color: highlight ? '#FF6B4A' : '#2C3E50' }}>
        {value || '—'}
      </span>
    </div>
  );
}

// ─── Boolean Badge ──────────────────────────────────────────────────────────
function BoolBadge({ value, trueLabel = 'Yes', falseLabel = 'No' }) {
  return (
    <span className="px-2 py-0.5 rounded-full text-xs font-bold" style={{ backgroundColor: value ? '#D1FAE5' : '#F3F4F6', color: value ? '#065F46' : '#9CA3AF' }}>
      {value ? trueLabel : falseLabel}
    </span>
  );
}

// ─── Main Component ─────────────────────────────────────────────────────────
export default function PolicyDetail() {
  const { id }       = useParams();
  const navigate     = useNavigate();
  const { fmtMoney } = useCurrencyFormatter();
  const { showNotification, NotificationContainer } = useNotification();

  const [policy,       setPolicy]       = useState(null);
  const [policyholder, setPolicyholder] = useState(null);
  const [vehicle,      setVehicle]      = useState(null);
  const [claims,       setClaims]       = useState([]);
  const [isLoading,    setIsLoading]    = useState(true);
  const [currency,     setCurrency]     = useState('USD');
  const [activeTab,    setActiveTab]    = useState('overview');

  useEffect(() => { if (id) loadAll(); }, [id]); // eslint-disable-line

  const loadAll = async () => {
    setIsLoading(true);
    try {
      const pol = await api.getPolicy(id);
      setPolicy(pol);
      const [ph, veh, claimsData] = await Promise.all([
        api.getPolicyholder(pol.policyholder),
        api.getVehicle(pol.vehicle),
        api.getClaims({ policy: id }).catch(() => []),
      ]);
      setPolicyholder(ph);
      setVehicle(veh);
      const list = claimsData.results || claimsData;
      setClaims(
        Array.isArray(list)
          ? list.filter((c) => String(c.policy) === String(id) || String(c.policy_number) === String(pol.policy_number))
          : []
      );
      if (pol.currency) setCurrency(pol.currency);
    } catch {
      showNotification('Failed to load policy details', 'error');
    } finally {
      setIsLoading(false);
    }
  };

  // ── Loading / Not Found ───────────────────────────────────────────────────
  if (isLoading) {
    return (
      <div className="flex h-screen overflow-hidden" style={{ backgroundColor: '#F8F9FA' }}>
        <Sidebar />
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center">
            <Loader2 className="inline-block w-10 h-10 animate-spin mb-3" style={{ color: '#FF6B4A' }} />
            <p className="text-sm" style={{ color: '#7F8C8D' }}>Loading policy details…</p>
          </div>
        </div>
      </div>
    );
  }

  if (!policy) {
    return (
      <div className="flex h-screen overflow-hidden" style={{ backgroundColor: '#F8F9FA' }}>
        <Sidebar />
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center">
            <Shield className="inline-block w-12 h-12 mb-3" style={{ color: '#E5E7EB' }} />
            <p className="text-lg font-bold" style={{ color: '#2C3E50' }}>Policy not found</p>
            <button onClick={() => navigate('/policies')} className="mt-4 px-4 py-2 rounded-lg text-sm font-semibold text-white" style={{ backgroundColor: '#FF6B4A' }}>
              Back to Policies
            </button>
          </div>
        </div>
      </div>
    );
  }

  const sp             = STATUS_PALETTE[policy.status] || STATUS_PALETTE.PENDING;
  const creditColors   = CREDIT_COLORS[policyholder?.credit_rating] || CREDIT_COLORS.FAIR;
  const creditScore    = policyholder?.credit_score || 650;
  const daysLeft       = policy.days_until_expiry ?? 0;
  const isExpiringSoon = daysLeft > 0 && daysLeft <= 30;

  const tabs = [
    { id: 'overview',     label: 'Overview',              icon: <Activity className="w-3.5 h-3.5" /> },
    { id: 'policyholder', label: 'Policyholder',          icon: <User className="w-3.5 h-3.5" /> },
    { id: 'vehicle',      label: 'Vehicle',               icon: <Car className="w-3.5 h-3.5" /> },
    { id: 'claims',       label: `Claims (${claims.length})`, icon: <FileText className="w-3.5 h-3.5" /> },
  ];

  return (
    <div className="flex h-screen overflow-hidden" style={{ backgroundColor: '#F8F9FA' }}>
      <Sidebar />
      <NotificationContainer />

      {/* No horizontal scroll on main column */}
      <div className="flex-1 overflow-y-auto overflow-x-hidden min-w-0">

        {/* ── Hero Banner ───────────────────────────────────────────────── */}
        <div className="relative px-8 pt-8 pb-6" style={{ background: 'linear-gradient(135deg, #1a1a2e 0%, #2C3E50 60%, #34495e 100%)' }}>
          <div className="absolute top-0 right-0 w-64 h-64 rounded-full pointer-events-none" style={{ backgroundColor: '#FF6B4A', opacity: 0.05, transform: 'translate(30%,-30%)' }} />
          <div className="absolute bottom-0 left-1/3 w-32 h-32 rounded-full pointer-events-none" style={{ backgroundColor: '#FF6B4A', opacity: 0.05, transform: 'translateY(50%)' }} />

          <button onClick={() => navigate('/policies')} className="flex items-center gap-2 mb-6 text-sm font-semibold transition-opacity hover:opacity-70" style={{ color: 'rgba(255,255,255,0.7)' }}>
            <ArrowLeft className="w-4 h-4" /> Back to Policies
          </button>

          <div className="flex items-start justify-between gap-4 min-w-0">
            <div className="flex items-start gap-5 min-w-0">
              <div className="w-14 h-14 rounded-2xl flex items-center justify-center flex-shrink-0" style={{ backgroundColor: '#FF6B4A', boxShadow: '0 4px 20px rgba(255,107,74,0.4)' }}>
                <Shield className="w-7 h-7 text-white" />
              </div>
              <div className="min-w-0">
                <div className="flex items-center gap-3 flex-wrap mb-1">
                  <h1 className="text-2xl font-bold text-white truncate">{policy.policy_number}</h1>
                  <span className="px-3 py-1 rounded-full text-xs font-bold flex items-center gap-1.5 flex-shrink-0" style={{ backgroundColor: sp.bg, color: sp.color }}>
                    <span className="w-1.5 h-1.5 rounded-full inline-block" style={{ backgroundColor: sp.dot }} />
                    {policy.status}
                  </span>
                  {isExpiringSoon && (
                    <span className="px-3 py-1 rounded-full text-xs font-bold flex items-center gap-1.5 flex-shrink-0" style={{ backgroundColor: '#FEF3C7', color: '#92400E' }}>
                      <AlertTriangle className="w-3 h-3" /> Expires in {daysLeft} days
                    </span>
                  )}
                </div>
                <p className="text-sm" style={{ color: 'rgba(255,255,255,0.6)' }}>
                  {policy.policy_type?.replace('_', ' ')} · {policy.coverage_level} Coverage
                </p>
                {policyholder && (
                  <p className="mt-1 text-sm font-medium truncate" style={{ color: 'rgba(255,255,255,0.8)' }}>
                    {policyholder.full_name || `${policyholder.first_name} ${policyholder.last_name}`}
                    {vehicle && <span style={{ color: 'rgba(255,255,255,0.45)' }}> · {vehicle.make} {vehicle.model} ({vehicle.manufacture_year})</span>}
                  </p>
                )}
              </div>
            </div>

            {/* Premium */}
            <div className="text-right flex-shrink-0">
              <div className="flex items-center gap-2 justify-end mb-1">
                <span className="text-xs font-medium" style={{ color: 'rgba(255,255,255,0.5)' }}>Annual Premium</span>
                <div className="flex gap-0.5 p-0.5 rounded-lg" style={{ backgroundColor: 'rgba(255,255,255,0.1)' }}>
                  {['USD', 'ZWG'].map((c) => (
                    <button key={c} onClick={() => setCurrency(c)} className="px-2 py-0.5 rounded-md text-xs font-bold transition-all" style={{ backgroundColor: currency === c ? '#FF6B4A' : 'transparent', color: currency === c ? 'white' : 'rgba(255,255,255,0.5)' }}>{c}</button>
                  ))}
                </div>
              </div>
              <p className="text-3xl font-bold text-white">{fmtMoney(policy.premium_amount, currency)}</p>
              <p className="text-xs mt-1" style={{ color: 'rgba(255,255,255,0.4)' }}>{fmtDate(policy.start_date)} → {fmtDate(policy.end_date)}</p>
            </div>
          </div>

          {/* Metric strip */}
          <div className="grid grid-cols-4 gap-3 mt-6">
            {[
              { label: 'Coverage Amount',   value: fmtMoney(policy.coverage_amount, currency), icon: <ShieldCheck className="w-4 h-4" /> },
              { label: 'Deductible',        value: fmtMoney(policy.deductible, currency),       icon: <TrendingUp className="w-4 h-4" /> },
              { label: 'Total Claims',      value: claims.length,                               icon: <FileText className="w-4 h-4" /> },
              { label: 'Days Until Expiry', value: daysLeft > 0 ? `${daysLeft} days` : 'Expired', icon: <Calendar className="w-4 h-4" /> },
            ].map(({ label, value, icon }) => (
              <div key={label} className="rounded-xl px-4 py-3" style={{ backgroundColor: 'rgba(255,255,255,0.08)' }}>
                <div className="flex items-center gap-2 mb-1" style={{ color: 'rgba(255,255,255,0.5)' }}>
                  {icon}<span className="text-xs font-medium">{label}</span>
                </div>
                <p className="text-lg font-bold text-white">{value}</p>
              </div>
            ))}
          </div>
        </div>

        {/* ── Tabs ──────────────────────────────────────────────────────── */}
        <div className="bg-white border-b sticky top-0 z-10" style={{ borderColor: '#E5E7EB' }}>
          <div className="px-8 flex">
            {tabs.map((tab) => (
              <button key={tab.id} onClick={() => setActiveTab(tab.id)} className="flex items-center gap-2 px-5 py-4 text-sm font-semibold border-b-2 transition-all whitespace-nowrap" style={{ borderColor: activeTab === tab.id ? '#FF6B4A' : 'transparent', color: activeTab === tab.id ? '#FF6B4A' : '#7F8C8D' }}>
                {tab.icon}{tab.label}
              </button>
            ))}
          </div>
        </div>

        {/* ── Tab Content ───────────────────────────────────────────────── */}
        <div className="p-8">

          {/* ══ OVERVIEW ══ */}
          {activeTab === 'overview' && (
            <div className="grid grid-cols-3 gap-6 min-w-0">

              {/* Left: Add-ons + Claims */}
              <div className="col-span-2 space-y-6 min-w-0">

                {/* Add-ons — compact horizontal row */}
                <SectionCard icon={<Zap className="w-4 h-4" />} title="Coverage Add-ons" accent="#8B5CF6">
                  <div className="flex gap-3">
                    {[
                      { key: 'has_roadside_assistance', label: 'Roadside Assistance', icon: <Navigation className="w-3.5 h-3.5" /> },
                      { key: 'has_rental_coverage',     label: 'Rental Coverage',     icon: <Car className="w-3.5 h-3.5" /> },
                      { key: 'has_glass_coverage',      label: 'Glass Coverage',       icon: <Shield className="w-3.5 h-3.5" /> },
                    ].map(({ key, label, icon }) => {
                      const active = policy[key];
                      return (
                        <div key={key} className="flex items-center gap-2.5 px-3.5 py-2.5 rounded-xl flex-1 min-w-0" style={{ backgroundColor: active ? '#EDE9FE' : '#F8F9FA', border: `1.5px solid ${active ? '#A78BFA' : '#E5E7EB'}` }}>
                          <div className="w-7 h-7 rounded-lg flex items-center justify-center flex-shrink-0" style={{ backgroundColor: active ? '#DDD6FE' : '#E5E7EB', color: active ? '#7C3AED' : '#9CA3AF' }}>{icon}</div>
                          <div className="min-w-0">
                            <p className="text-xs font-semibold truncate" style={{ color: active ? '#5B21B6' : '#6B7280' }}>{label}</p>
                            <p className="text-xs" style={{ color: active ? '#7C3AED' : '#9CA3AF' }}>{active ? 'Included' : 'Not included'}</p>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </SectionCard>

                {/* Recent Claims */}
                {claims.length > 0 ? (
                  <SectionCard icon={<FileText className="w-4 h-4" />} title="Recent Claims" accent="#EF4444"
                    badge={<button onClick={() => setActiveTab('claims')} className="text-xs font-semibold flex items-center gap-1" style={{ color: '#FF6B4A' }}>View all <ChevronRight className="w-3.5 h-3.5" /></button>}
                  >
                    <div className="space-y-2">
                      {claims.slice(0, 3).map((claim) => {
                        const csp = CLAIM_STATUS_PALETTE[claim.claim_status] || CLAIM_STATUS_PALETTE.SUBMITTED;
                        return (
                          <div key={claim.id} className="flex items-center justify-between p-3 rounded-xl" style={{ backgroundColor: '#F8F9FA', border: '1px solid #E5E7EB' }}>
                            <div className="min-w-0 mr-4">
                              <p className="text-sm font-bold truncate" style={{ color: '#2C3E50' }}>{claim.claim_number}</p>
                              <p className="text-xs mt-0.5 truncate" style={{ color: '#9CA3AF' }}>{claim.claim_type} · {fmtDate(claim.incident_date)}</p>
                            </div>
                            <div className="text-right flex-shrink-0">
                              <p className="text-sm font-semibold" style={{ color: '#2C3E50' }}>{fmtMoney(claim.claimed_amount, currency)}</p>
                              <span className="px-2 py-0.5 rounded-full text-xs font-bold" style={{ backgroundColor: csp.bg, color: csp.color }}>{claim.claim_status}</span>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </SectionCard>
                ) : (
                  <div className="bg-white rounded-2xl shadow-sm p-8 text-center" style={{ border: '1.5px dashed #E5E7EB' }}>
                    <FileText className="w-8 h-8 mx-auto mb-2" style={{ color: '#E5E7EB' }} />
                    <p className="text-sm font-semibold" style={{ color: '#9CA3AF' }}>No claims on this policy</p>
                  </div>
                )}
              </div>

              {/* Right sidebar */}
              <div className="space-y-6 min-w-0">

                {/* Policyholder snapshot — no credit bar, no button */}
                {policyholder && (
                  <SectionCard icon={<User className="w-4 h-4" />} title="Policyholder" accent="#3B82F6">
                    <div className="text-center mb-4">
                      <div className="w-14 h-14 rounded-full flex items-center justify-center mx-auto mb-2.5 text-xl font-bold text-white" style={{ backgroundColor: '#FF6B4A' }}>
                        {(policyholder.first_name?.[0] || '') + (policyholder.last_name?.[0] || '')}
                      </div>
                      <p className="font-bold text-sm" style={{ color: '#2C3E50' }}>
                        {policyholder.full_name || `${policyholder.first_name} ${policyholder.last_name}`}
                      </p>
                      <p className="text-xs mt-0.5" style={{ color: '#9CA3AF' }}>{policyholder.policy_holder_id}</p>
                    </div>
                    <InfoRow icon={<Mail className="w-3.5 h-3.5" />}     label="Email"      value={policyholder.email} />
                    <InfoRow icon={<Phone className="w-3.5 h-3.5" />}    label="Phone"      value={policyholder.phone_number} />
                    <InfoRow icon={<MapPin className="w-3.5 h-3.5" />}   label="City"       value={policyholder.city} />
                    <InfoRow icon={<Activity className="w-3.5 h-3.5" />} label="Occupation" value={policyholder.occupation} />
                  </SectionCard>
                )}

                {/* Vehicle snapshot — no button */}
                {vehicle && (
                  <SectionCard icon={<Car className="w-4 h-4" />} title="Insured Vehicle" accent="#10B981">
                    <div className="rounded-xl p-3 mb-4 text-center" style={{ background: 'linear-gradient(135deg,#F0FDF4,#ECFDF5)', border: '1.5px solid #A7F3D0' }}>
                      <Car className="w-7 h-7 mx-auto mb-1.5" style={{ color: '#10B981' }} />
                      <p className="font-bold text-sm" style={{ color: '#065F46' }}>{vehicle.manufacture_year} {vehicle.make} {vehicle.model}</p>
                      <p className="text-xs mt-0.5" style={{ color: '#6EE7B7' }}>{vehicle.registration_number}</p>
                    </div>
                    <InfoRow icon={<DollarSign className="w-3.5 h-3.5" />} label="Market Value" value={fmtMoney(vehicle.market_value, currency)} highlight />
                    <InfoRow icon={<Gauge className="w-3.5 h-3.5" />}      label="Odometer"     value={`${vehicle.odometer_reading?.toLocaleString()} mi`} />
                    <InfoRow icon={<Zap className="w-3.5 h-3.5" />}        label="Fuel Type"    value={vehicle.fuel_type} />
                    <InfoRow icon={<Lock className="w-3.5 h-3.5" />}       label="Anti-Theft"   value={<BoolBadge value={vehicle.has_anti_theft} />} />
                  </SectionCard>
                )}
              </div>
            </div>
          )}

          {/* ══ POLICYHOLDER TAB ══ */}
          {activeTab === 'policyholder' && policyholder && (
            <div className="grid grid-cols-2 gap-6 min-w-0">

              <SectionCard icon={<User className="w-4 h-4" />} title="Personal Information" accent="#3B82F6">
                <div className="flex items-center gap-4 mb-5 p-3 rounded-xl" style={{ backgroundColor: '#F8F9FA' }}>
                  <div className="w-12 h-12 rounded-full flex items-center justify-center text-lg font-bold text-white flex-shrink-0" style={{ backgroundColor: '#FF6B4A' }}>
                    {(policyholder.first_name?.[0] || '') + (policyholder.last_name?.[0] || '')}
                  </div>
                  <div className="min-w-0">
                    <p className="font-bold text-sm truncate" style={{ color: '#2C3E50' }}>{policyholder.full_name || `${policyholder.first_name} ${policyholder.last_name}`}</p>
                    <p className="text-xs truncate" style={{ color: '#9CA3AF' }}>{policyholder.policy_holder_id}</p>
                    <span className="mt-1 inline-block px-2 py-0.5 rounded-full text-xs font-bold" style={{ backgroundColor: policyholder.is_active ? '#D1FAE5' : '#FEE2E2', color: policyholder.is_active ? '#065F46' : '#991B1B' }}>
                      {policyholder.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </div>
                </div>
                <InfoRow icon={<Hash className="w-3.5 h-3.5" />}       label="ID"               value={policyholder.policy_holder_id} mono />
                <InfoRow icon={<Calendar className="w-3.5 h-3.5" />}   label="Date of Birth"    value={fmtDate(policyholder.date_of_birth)} />
                <InfoRow icon={<User className="w-3.5 h-3.5" />}       label="Gender"           value={policyholder.gender === 'M' ? 'Male' : policyholder.gender === 'F' ? 'Female' : 'Other'} />
                <InfoRow icon={<Award className="w-3.5 h-3.5" />}      label="Age"              value={`${policyholder.age} years`} />
                <InfoRow icon={<Star className="w-3.5 h-3.5" />}       label="Marital Status"   value={policyholder.marital_status} />
                <InfoRow icon={<Activity className="w-3.5 h-3.5" />}   label="Occupation"       value={policyholder.occupation} />
                <InfoRow icon={<DollarSign className="w-3.5 h-3.5" />} label="Annual Income"    value={fmtMoney(policyholder.annual_income, currency)} />
                <InfoRow icon={<Clock className="w-3.5 h-3.5" />}      label="Years w/ Company" value={`${policyholder.years_with_company} years`} />
              </SectionCard>

              <div className="space-y-6 min-w-0">

                <SectionCard icon={<Mail className="w-4 h-4" />} title="Contact Information" accent="#8B5CF6">
                  <InfoRow icon={<Mail className="w-3.5 h-3.5" />}      label="Email"    value={policyholder.email} />
                  <InfoRow icon={<Phone className="w-3.5 h-3.5" />}     label="Phone"    value={policyholder.phone_number} />
                  <InfoRow icon={<MapPin className="w-3.5 h-3.5" />}    label="Address"  value={policyholder.address_line1} />
                  {policyholder.address_line2 && <InfoRow icon={<MapPin className="w-3.5 h-3.5" />} label="" value={policyholder.address_line2} />}
                  <InfoRow icon={<MapPin className="w-3.5 h-3.5" />}    label="City"     value={`${policyholder.city}, ${policyholder.state}`} />
                  <InfoRow icon={<Navigation className="w-3.5 h-3.5" />} label="Country" value={policyholder.country} />
                </SectionCard>

                {/* Credit & Risk — slim progress bar, no big header block */}
                <SectionCard icon={<CreditCard className="w-4 h-4" />} title="Credit &amp; Risk Profile" accent="#F59E0B">
                  {/* Slim credit score row — just label + score + thin bar */}
                  <div className="mb-4">
                    <div className="flex items-center justify-between mb-1.5">
                      <span className="text-xs font-medium" style={{ color: '#9CA3AF' }}>Credit Score</span>
                      <div className="flex items-center gap-2">
                        <span className="text-xs px-2 py-0.5 rounded-full font-bold" style={{ backgroundColor: creditColors.bg, color: creditColors.label }}>
                          {policyholder.credit_rating?.replace('_', ' ')}
                        </span>
                        <span className="text-sm font-bold" style={{ color: creditColors.label }}>{creditScore}</span>
                      </div>
                    </div>
                    <div className="w-full h-1.5 rounded-full" style={{ backgroundColor: '#E5E7EB' }}>
                      <div className="h-1.5 rounded-full transition-all duration-700" style={{ width: `${creditPct(creditScore)}%`, backgroundColor: creditColors.bar }} />
                    </div>
                  </div>

                  <InfoRow icon={<CheckCircle className="w-3.5 h-3.5" />} label="Driving License"  value={<BoolBadge value={policyholder.has_driving_license} />} />
                  <InfoRow icon={<CheckCircle className="w-3.5 h-3.5" />} label="Defensive License" value={<BoolBadge value={policyholder.has_defensive_license} />} />
                  <InfoRow icon={<CheckCircle className="w-3.5 h-3.5" />} label="Medical License"   value={<BoolBadge value={policyholder.is_medical_license_valid} trueLabel="Valid" falseLabel="Invalid" />} />
                </SectionCard>
              </div>
            </div>
          )}

          {/* ══ VEHICLE TAB ══ */}
          {activeTab === 'vehicle' && vehicle && (
            <div className="grid grid-cols-2 gap-6 min-w-0">

              <SectionCard icon={<Car className="w-4 h-4" />} title="Vehicle Identity" accent="#10B981">
                <div className="rounded-xl p-4 mb-5 text-center" style={{ background: 'linear-gradient(135deg,#F0FDF4,#ECFDF5)', border: '1.5px solid #A7F3D0' }}>
                  <Car className="w-9 h-9 mx-auto mb-2" style={{ color: '#10B981' }} />
                  <p className="text-lg font-bold" style={{ color: '#065F46' }}>{vehicle.manufacture_year} {vehicle.make} {vehicle.model}</p>
                  <p className="text-sm mt-0.5" style={{ color: '#6EE7B7' }}>{vehicle.vehicle_type}</p>
                </div>
                <InfoRow icon={<Hash className="w-3.5 h-3.5" />}       label="VIN"          value={vehicle.vin} mono />
                <InfoRow icon={<Hash className="w-3.5 h-3.5" />}       label="Registration" value={vehicle.registration_number} mono />
                <InfoRow icon={<Calendar className="w-3.5 h-3.5" />}   label="Year"         value={vehicle.manufacture_year} />
                <InfoRow icon={<Activity className="w-3.5 h-3.5" />}   label="Vehicle Age"  value={`${vehicle.vehicle_age} years`} />
                <InfoRow icon={<DollarSign className="w-3.5 h-3.5" />} label="Market Value" value={fmtMoney(vehicle.market_value, currency)} highlight />
              </SectionCard>

              <div className="space-y-6 min-w-0">
                <SectionCard icon={<Wrench className="w-4 h-4" />} title="Technical Specifications" accent="#6366F1">
                  <InfoRow icon={<Gauge className="w-3.5 h-3.5" />}    label="Engine"    value={`${vehicle.engine_capacity} CC`} />
                  <InfoRow icon={<Zap className="w-3.5 h-3.5" />}      label="Fuel Type" value={vehicle.fuel_type} />
                  <InfoRow icon={<User className="w-3.5 h-3.5" />}     label="Seats"     value={vehicle.seating_capacity} />
                  <InfoRow icon={<Activity className="w-3.5 h-3.5" />} label="Odometer"  value={`${vehicle.odometer_reading?.toLocaleString()} mi`} />
                </SectionCard>

                <SectionCard icon={<Lock className="w-4 h-4" />} title="Safety &amp; Condition" accent="#EF4444">
                  <div className="grid grid-cols-2 gap-3">
                    {[
                      { key: 'has_anti_theft', label: 'Anti-Theft', icon: <Lock className="w-4 h-4" />,     invert: false },
                      { key: 'has_airbags',    label: 'Airbags',    icon: <Shield className="w-4 h-4" />,   invert: false },
                      { key: 'has_abs',        label: 'ABS Brakes', icon: <Activity className="w-4 h-4" />, invert: false },
                      { key: 'is_modified',    label: 'Modified',   icon: <Wrench className="w-4 h-4" />,   invert: true  },
                    ].map(({ key, label, icon, invert }) => {
                      const val = vehicle[key];
                      const positive = invert ? !val : val;
                      return (
                        <div key={key} className="rounded-xl p-3 flex items-center gap-2.5" style={{ backgroundColor: positive ? '#F0FDF4' : '#F8F9FA', border: `1px solid ${positive ? '#A7F3D0' : '#E5E7EB'}` }}>
                          <div className="w-7 h-7 rounded-lg flex items-center justify-center flex-shrink-0" style={{ backgroundColor: positive ? '#D1FAE5' : '#E5E7EB', color: positive ? '#10B981' : '#9CA3AF' }}>{icon}</div>
                          <div className="min-w-0">
                            <p className="text-xs font-semibold truncate" style={{ color: '#2C3E50' }}>{label}</p>
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

          {/* ══ CLAIMS TAB ══ */}
          {activeTab === 'claims' && (
            <div className="min-w-0">
              {claims.length === 0 ? (
                <div className="bg-white rounded-2xl shadow-sm p-16 text-center">
                  <FileText className="w-12 h-12 mx-auto mb-3" style={{ color: '#E5E7EB' }} />
                  <p className="text-lg font-bold" style={{ color: '#2C3E50' }}>No claims on this policy</p>
                  <p className="text-sm mt-1" style={{ color: '#9CA3AF' }}>Claims submitted against this policy will appear here.</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {claims.map((claim) => {
                    const csp = CLAIM_STATUS_PALETTE[claim.claim_status] || CLAIM_STATUS_PALETTE.SUBMITTED;
                    const fraudRisk = claim.fraud_score >= 0.7 ? 'HIGH' : claim.fraud_score >= 0.4 ? 'MEDIUM' : 'LOW';
                    const fc = { HIGH: { bg: '#FEE2E2', color: '#991B1B' }, MEDIUM: { bg: '#FEF3C7', color: '#92400E' }, LOW: { bg: '#D1FAE5', color: '#065F46' } }[fraudRisk];
                    return (
                      <div key={claim.id} className="bg-white rounded-2xl shadow-sm overflow-hidden min-w-0">
                        <div className="px-6 py-4 flex items-center justify-between border-b" style={{ borderColor: '#F3F4F6' }}>
                          <div className="flex items-center gap-4 min-w-0 mr-4">
                            <div className="w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0" style={{ backgroundColor: '#FFF5F3' }}>
                              <FileText className="w-5 h-5" style={{ color: '#FF6B4A' }} />
                            </div>
                            <div className="min-w-0">
                              <p className="font-bold text-sm truncate" style={{ color: '#2C3E50' }}>{claim.claim_number}</p>
                              <p className="text-xs truncate" style={{ color: '#9CA3AF' }}>{claim.claim_type} · Incident {fmtDate(claim.incident_date)}</p>
                            </div>
                          </div>
                          <div className="flex items-center gap-3 flex-shrink-0">
                            <span className="px-3 py-1 rounded-full text-xs font-bold" style={{ backgroundColor: fc.bg, color: fc.color }}>Fraud: {fraudRisk} ({(claim.fraud_score * 100).toFixed(0)}%)</span>
                            <span className="px-3 py-1 rounded-full text-xs font-bold" style={{ backgroundColor: csp.bg, color: csp.color }}>{claim.claim_status?.replace('_', ' ')}</span>
                          </div>
                        </div>
                        <div className="p-6 grid grid-cols-4 gap-3">
                          {[
                            { label: 'Claimed',  value: fmtMoney(claim.claimed_amount, currency) },
                            { label: 'Approved', value: fmtMoney(claim.approved_amount, currency) },
                            { label: 'Paid',     value: fmtMoney(claim.paid_amount, currency) },
                            { label: 'Severity', value: claim.severity },
                          ].map(({ label, value }) => (
                            <div key={label} className="rounded-xl p-3" style={{ backgroundColor: '#F8F9FA' }}>
                              <p className="text-xs font-medium mb-1" style={{ color: '#9CA3AF' }}>{label}</p>
                              <p className="text-sm font-bold" style={{ color: '#2C3E50' }}>{value || '—'}</p>
                            </div>
                          ))}
                        </div>
                        {claim.incident_location && (
                          <div className="px-6 pb-4 flex items-center gap-2 text-xs" style={{ color: '#9CA3AF' }}>
                            <MapPin className="w-3.5 h-3.5 flex-shrink-0" /><span className="truncate">{claim.incident_location}</span>
                          </div>
                        )}
                        {claim.fraud_reason && (
                          <div className="mx-6 mb-4 p-3 rounded-xl flex items-start gap-2 text-xs" style={{ backgroundColor: '#FEF3C7', color: '#92400E' }}>
                            <AlertTriangle className="w-3.5 h-3.5 flex-shrink-0 mt-0.5" /><span>{claim.fraud_reason}</span>
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          )}

        </div>
      </div>
    </div>
  );
}