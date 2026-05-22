import { useState, useEffect, useRef } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { usePricingSettings } from '../contexts/PricingSettingsContext';
import { api } from '../services/api';
import Sidebar from './Sidebar';
import { useNotification } from './notifications/useNotification';
import { useCurrencyFormatter } from '../utils/currencyFormatter';
import { useConfirm } from './notifications/useConfirm';
import {
  Search,
  Plus,
  Edit,
  Trash2,
  X,
  Sparkles,
  Loader2,
  CheckCircle2,
  ChevronDown,
  Info,
  ShieldCheck,
  TrendingUp,
  ChevronRight,
  Calculator,
  ArrowRight,
  ArrowLeft,
} from 'lucide-react';

const todayISO = () => new Date().toISOString().split('T')[0];
const nextYearISO = () => {
  const d = new Date();
  d.setFullYear(d.getFullYear() + 1);
  return d.toISOString().split('T')[0];
};

const mkPolicyNum = () =>
  `POL-${Math.random().toString(36).substr(2, 12).toUpperCase().padEnd(12, '0')}`;

const POLICY_TYPES = {
  COMPREHENSIVE: 'Comprehensive',
  THIRD_PARTY: 'Third Party',
  COLLISION: 'Collision',
  LIABILITY: 'Liability',
};

const STATUS_MAP = {
  ACTIVE: 'Active',
  EXPIRED: 'Expired',
  CANCELLED: 'Cancelled',
  SUSPENDED: 'Suspended',
  PENDING: 'Pending',
};

const STATUS_PALETTE = {
  ACTIVE:    { bg: '#D1FAE5', color: '#065F46' },
  EXPIRED:   { bg: '#FEE2E2', color: '#991B1B' },
  CANCELLED: { bg: '#FEE2E2', color: '#991B1B' },
  SUSPENDED: { bg: '#FEF3C7', color: '#92400E' },
  PENDING:   { bg: '#DBEAFE', color: '#1E40AF' },
};

const COVERAGE_HINTS = {
  BASIC:    { pct: '80%',  ded: '15%' },
  STANDARD: { pct: '100%', ded: '10%' },
  PREMIUM:  { pct: '120%', ded: '5%'  },
};

const blankForm = () => ({
  policy_number: '',
  policyholder: '',
  vehicle: '',
  policy_type: 'COMPREHENSIVE',
  coverage_level: 'STANDARD',
  start_date: todayISO(),
  end_date: nextYearISO(),
  status: 'ACTIVE',
  has_roadside_assistance: false,
  has_rental_coverage: false,
  has_glass_coverage: false,
});

function StepIndicator({ step }) {
  const steps = [
    { n: 1, label: 'Policy Details' },
    { n: 2, label: 'Review & Price' },
  ];
  return (
    <div className="flex items-center gap-0">
      {steps.map((s, i) => {
        const done    = step > s.n;
        const current = step === s.n;
        return (
          <div key={s.n} className="flex items-center">
            <div className="flex items-center gap-2">
              <div
                className="w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold transition-all duration-300"
                style={{
                  backgroundColor: done ? '#10B981' : current ? '#FF6B4A' : '#E5E7EB',
                  color: done || current ? '#fff' : '#9CA3AF',
                }}
              >
                {done ? <CheckCircle2 className="w-4 h-4" /> : s.n}
              </div>
              <span
                className="text-xs font-semibold hidden sm:block transition-colors duration-300"
                style={{ color: current ? '#2C3E50' : done ? '#10B981' : '#9CA3AF' }}
              >
                {s.label}
              </span>
            </div>
            {i < steps.length - 1 && (
              <div
                className="w-12 h-0.5 mx-3 rounded-full transition-all duration-500"
                style={{ backgroundColor: step > s.n ? '#10B981' : '#E5E7EB' }}
              />
            )}
          </div>
        );
      })}
    </div>
  );
}

export default function Policies() {
  const navigate = useNavigate();
  const location = useLocation();
  const { fmtMoney } = useCurrencyFormatter();
  const { user } = useAuth();
  const { settings: pricingSettings } = usePricingSettings();
  const { showNotification, NotificationContainer } = useNotification();
  const { showConfirm, ConfirmDialog } = useConfirm();

  const [policies, setPolicies]   = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [currency, setCurrency]   = useState('USD');

  const [showModal, setShowModal] = useState(false);
  const [modalStep, setModalStep] = useState(1);
  const [editingId, setEditingId] = useState(null);
  const [formData, setFormData]   = useState(blankForm());
  const [isSaving, setIsSaving]   = useState(false);

  const [phSearch, setPhSearch]     = useState('');
  const [vehSearch, setVehSearch]   = useState('');
  const [showPhDrop, setShowPhDrop] = useState(false);
  const [showVehDrop, setShowVehDrop] = useState(false);
  const [selectedPH, setSelectedPH] = useState(null);
  const [selectedVeh, setSelectedVeh] = useState(null);
  const [phOptions, setPhOptions]   = useState([]);
  const [vehOptions, setVehOptions] = useState([]);
  const [phSearching, setPhSearching]   = useState(false);
  const [vehSearching, setVehSearching] = useState(false);
  const phRef  = useRef(null);
  const vehRef = useRef(null);

  const [isCalcing, setIsCalcing]   = useState(false);
  const [premiumData, setPremiumData] = useState(null);
  const debounceRef    = useRef(null);
  const phDebounceRef  = useRef(null);
  const vehDebounceRef = useRef(null);

  const ADD_ONS = pricingSettings ? [
    {
      key: 'has_roadside_assistance',
      label: 'Roadside Assistance',
      price: `+${fmtMoney(pricingSettings.addon_roadside_assistance, currency)}/yr`,
    },
    {
      key: 'has_rental_coverage',
      label: 'Rental Coverage',
      price: `+${fmtMoney(pricingSettings.addon_rental_coverage, currency)}/yr`,
    },
    {
      key: 'has_glass_coverage',
      label: 'Glass Coverage',
      price: `+${fmtMoney(pricingSettings.addon_glass_coverage, currency)}/yr`,
    },
  ] : [];

  // ── Click-outside for dropdowns ────────────────────────────────────────────
  useEffect(() => {
    const handler = (e) => {
      if (phRef.current  && !phRef.current.contains(e.target))  setShowPhDrop(false);
      if (vehRef.current && !vehRef.current.contains(e.target)) setShowVehDrop(false);
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  // ── Open modal from router state ───────────────────────────────────────────
  useEffect(() => {
    if (location.state?.openModal) {
      openModal();
      if (location.state.policyholderId) {
        api.getPolicyholder(location.state.policyholderId)
          .then((ph) => {
            applyPH(ph);
            if (location.state.vehicleId) {
              api.getVehicle(location.state.vehicleId).then(applyVeh).catch(() => {});
            }
          }).catch(() => {});
      }
    }
  }, []); // eslint-disable-line

  // ── Policyholder search ────────────────────────────────────────────────────
  useEffect(() => {
    if (selectedPH) return;
    clearTimeout(phDebounceRef.current);
    if (phSearch.length < 1) {
      phDebounceRef.current = setTimeout(async () => {
        setPhSearching(true);
        try {
          const data = await api.getPolicyholders({ page_size: 30 });
          setPhOptions(data.results || data);
        } catch { setPhOptions([]); }
        finally { setPhSearching(false); }
      }, 100);
      return;
    }
    phDebounceRef.current = setTimeout(async () => {
      setPhSearching(true);
      try {
        const data = await api.getPolicyholders({ search: phSearch, page_size: 20 });
        setPhOptions(data.results || data);
      } catch { setPhOptions([]); }
      finally { setPhSearching(false); }
    }, 350);
    return () => clearTimeout(phDebounceRef.current);
  }, [phSearch, selectedPH]);

  // ── Vehicle search ─────────────────────────────────────────────────────────
  useEffect(() => {
    if (!selectedPH) { setVehOptions([]); return; }
    if (selectedVeh) return;
    clearTimeout(vehDebounceRef.current);
    vehDebounceRef.current = setTimeout(async () => {
      setVehSearching(true);
      try {
        const data = await api.request(`/fraud-detection/policyholders/${selectedPH.id}/vehicles/`);
        const all = data.results || data;
        const filtered = vehSearch
          ? all.filter((v) =>
              `${v.make} ${v.model} ${v.registration_number}`.toLowerCase().includes(vehSearch.toLowerCase())
            )
          : all;
        setVehOptions(filtered.slice(0, 10));
      } catch { setVehOptions([]); }
      finally { setVehSearching(false); }
    }, 200);
    return () => clearTimeout(vehDebounceRef.current);
  }, [selectedPH, vehSearch, selectedVeh]); // eslint-disable-line

  // ── Auto-advance end_date when start_date changes ─────────────────────────
  useEffect(() => {
    if (!editingId && formData.start_date) {
      const d = new Date(formData.start_date);
      d.setFullYear(d.getFullYear() + 1);
      setFormData((prev) => ({ ...prev, end_date: d.toISOString().split('T')[0] }));
    }
  }, [formData.start_date]); // eslint-disable-line

  // ── Premium recalculation on step 2 ───────────────────────────────────────
  useEffect(() => {
    if (!selectedPH || !selectedVeh) return;
    if (modalStep !== 2) return;
    clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(runPremiumCalc, 400);
    return () => clearTimeout(debounceRef.current);
  }, [ // eslint-disable-line
    selectedPH, selectedVeh, modalStep,
    formData.policy_type, formData.coverage_level,
    formData.has_roadside_assistance, formData.has_rental_coverage, formData.has_glass_coverage,
  ]);

  useEffect(() => { fetchAllData(); }, []);

  // ── Data ───────────────────────────────────────────────────────────────────
  const fetchAllData = async () => {
    setIsLoading(true);
    try {
      const data = await api.getPolicies().catch(() => []);
      setPolicies(data.results || data);
    } finally { setIsLoading(false); }
  };

  const refreshPolicies = async () => {
    try {
      const data = await api.getPolicies();
      setPolicies(data.results || data);
    } catch { showNotification('Failed to refresh policies', 'error'); }
  };

  // ── Premium calc ───────────────────────────────────────────────────────────
  const runPremiumCalc = async () => {
    if (!selectedPH || !selectedVeh || !pricingSettings) return;
    setIsCalcing(true);
    try {
      const vVal = parseFloat(selectedVeh.market_value || 0);
      const res = await api.calculatePremium({
        policy_type:               formData.policy_type,
        coverage_level:            formData.coverage_level,
        coverage_amount:           vVal * 1.0,
        deductible:                vVal * 0.1,
        customer_age:              selectedPH.age              ?? 30,
        customer_credit_score:     selectedPH.credit_score     ?? 650,
        customer_years_experience: selectedPH.years_with_company ?? 0,
        vehicle_manufacture_year:  selectedVeh.manufacture_year,
        vehicle_make:              selectedVeh.make,
        vehicle_model:             selectedVeh.model,
        vehicle_value:             vVal,
        vehicle_has_anti_theft:    selectedVeh.has_anti_theft  || false,
        vehicle_is_modified:       selectedVeh.is_modified     || false,
        has_roadside_assistance:   formData.has_roadside_assistance,
        has_rental_coverage:       formData.has_rental_coverage,
        has_glass_coverage:        formData.has_glass_coverage,
      });
      setPremiumData({
        premium_amount:  res.final_premium,
        coverage_amount: res.breakdown.coverage_amount,
        deductible:      res.breakdown.deductible,
        confidence:      res.confidence_score,
        ml_base:         res.ml_predicted_premium,
        risk_adj:        res.risk_adjustment,
        discounts:       res.discount_amount,
      });
    } catch {
      showNotification('Failed to calculate premium. Please try again.', 'error');
      setPremiumData(null);
    } finally {
      setIsCalcing(false);
    }
  };

  // ── Dropdown helpers ───────────────────────────────────────────────────────
  const applyPH = (ph) => {
    setSelectedPH(ph);
    setPhSearch(ph.full_name || `${ph.first_name} ${ph.last_name}`);
    setShowPhDrop(false);
    setSelectedVeh(null);
    setVehSearch('');
    setVehOptions([]);
    setPremiumData(null);
    setFormData((prev) => ({ ...prev, policyholder: String(ph.id), vehicle: '' }));
  };

  const applyVeh = (veh) => {
    setSelectedVeh(veh);
    setVehSearch(`${veh.make} ${veh.model} (${veh.registration_number})`);
    setFormData((prev) => ({ ...prev, vehicle: String(veh.id) }));
    setShowVehDrop(false);
  };

  const clearPH = () => {
    setSelectedPH(null); setPhSearch(''); setPhOptions([]);
    setSelectedVeh(null); setVehSearch(''); setVehOptions([]); setPremiumData(null);
    setFormData((prev) => ({ ...prev, policyholder: '', vehicle: '' }));
  };

  const clearVeh = () => {
    setSelectedVeh(null); setVehSearch(''); setPremiumData(null);
    setFormData((prev) => ({ ...prev, vehicle: '' }));
  };

  // ── Modal helpers ──────────────────────────────────────────────────────────
  const openModal = () => { resetForm(); setShowModal(true); setModalStep(1); };

  const handleNextStep = () => {
    if (!formData.policyholder || !formData.vehicle) {
      showNotification('Please select a policyholder and a vehicle first.', 'error');
      return;
    }
    setModalStep(2);
  };

  // ── CRUD ───────────────────────────────────────────────────────────────────
  const handleSubmit = async () => {
    if (!formData.policyholder || !formData.vehicle) {
      showNotification('Please select a policyholder and a vehicle.', 'error');
      return;
    }
    setIsSaving(true);
    try {
      const payload = {
        policy_number:           editingId ? formData.policy_number : mkPolicyNum(),
        policyholder:            formData.policyholder,
        vehicle:                 formData.vehicle,
        policy_type:             formData.policy_type,
        coverage_level:          formData.coverage_level,
        start_date:              formData.start_date,
        end_date:                formData.end_date,
        status:                  formData.status,
        currency,
        has_roadside_assistance: formData.has_roadside_assistance,
        has_rental_coverage:     formData.has_rental_coverage,
        has_glass_coverage:      formData.has_glass_coverage,
      };

      if (editingId) {
        await api.updatePolicy(editingId, payload);
        showNotification('Policy updated successfully!', 'success');
      } else {
        await api.createPolicy(payload);
        showNotification('Policy issued successfully!', 'success');
      }
      setShowModal(false);
      resetForm();
      refreshPolicies();
    } catch (err) {
      showNotification(err.data?.detail || err.message || 'Failed to save policy', 'error');
    } finally { setIsSaving(false); }
  };

  const handleEdit = async (e, policy) => {
    e.stopPropagation();
    setEditingId(policy.id);
    try {
      const fp = await api.getPolicy(policy.id);
      const [ph, veh] = await Promise.all([
        api.getPolicyholder(fp.policyholder),
        api.getVehicle(fp.vehicle),
      ]);

      setSelectedPH(ph);
      setSelectedVeh(veh);
      setPhSearch(ph.full_name || `${ph.first_name} ${ph.last_name}`);
      setVehSearch(`${veh.make} ${veh.model} (${veh.registration_number})`);
      if (fp.currency) setCurrency(fp.currency);

      if (fp.premium_amount) {
        setPremiumData({
          premium_amount:  fp.premium_amount,
          coverage_amount: fp.coverage_amount,
          deductible:      fp.deductible,
          confidence:      null,
          ml_base:         null,
        });
      }

      setFormData({
        policy_number:           fp.policy_number             || '',
        policyholder:            String(fp.policyholder       || ''),
        vehicle:                 String(fp.vehicle            || ''),
        policy_type:             fp.policy_type               || 'COMPREHENSIVE',
        coverage_level:          fp.coverage_level            || 'STANDARD',
        start_date:              fp.start_date                || todayISO(),
        end_date:                fp.end_date                  || nextYearISO(),
        status:                  fp.status                    || 'ACTIVE',
        has_roadside_assistance: fp.has_roadside_assistance   || false,
        has_rental_coverage:     fp.has_rental_coverage       || false,
        has_glass_coverage:      fp.has_glass_coverage        || false,
      });

      setModalStep(1);
      setShowModal(true);
    } catch {
      showNotification('Failed to load policy details', 'error');
    }
  };

  const handleDelete = async (e, id) => {
    e.stopPropagation();
    const confirmed = await showConfirm({
      title: 'Delete Policy',
      message: 'Are you sure? This cannot be undone.',
      confirmText: 'Delete',
      cancelText: 'Cancel',
      type: 'danger',
    });
    if (confirmed) {
      try {
        await api.deletePolicy(id);
        showNotification('Policy deleted successfully!', 'success');
        refreshPolicies();
      } catch (err) {
        showNotification(err.message || 'Failed to delete policy', 'error');
      }
    }
  };

  const resetForm = () => {
    setEditingId(null); setSelectedPH(null); setSelectedVeh(null);
    setPhSearch(''); setVehSearch(''); setPhOptions([]); setVehOptions([]);
    setPremiumData(null); setFormData(blankForm()); setModalStep(1);
  };

  const filteredPolicies = policies.filter((p) =>
    `${p.policy_number} ${p.policyholder_name || ''} ${p.vehicle_display || ''}`
      .toLowerCase().includes(searchTerm.toLowerCase())
  );

  const stepSubtitle =
    modalStep === 1
      ? editingId
        ? 'Update the details below — pricing recalculates on the next step'
        : 'Fill in the details below, then continue to review pricing'
      : editingId
        ? 'Premium recalculated — confirm to update the policy'
        : 'Review the AI-calculated premium before issuing';

  // ── Render ─────────────────────────────────────────────────────────────────
  return (
    <div className="flex h-screen overflow-hidden" style={{ backgroundColor: '#F8F9FA' }}>
      <Sidebar />
      <NotificationContainer />
      <ConfirmDialog />

      <div className="flex-1 overflow-y-auto">
        <div className="p-8">

          {/* Header */}
          <div className="flex items-start justify-between mb-8">
            <div>
              <h2 className="text-3xl font-bold" style={{ color: '#2C3E50' }}>Policies</h2>
              <p className="mt-1.5 text-sm" style={{ color: '#7F8C8D' }}>
                Manage and intelligently issue insurance policies · Click any row to view full details
              </p>
            </div>
            <div className="flex items-center gap-3 mt-1">
              <span className="text-xs font-semibold uppercase tracking-wider" style={{ color: '#7F8C8D' }}>Display</span>
              <div className="flex gap-1 p-1 rounded-xl" style={{ backgroundColor: '#E5E7EB' }}>
                {['USD', 'ZWG'].map((c) => (
                  <button key={c} onClick={() => setCurrency(c)}
                    className="px-4 py-1.5 rounded-lg text-sm font-bold transition-all duration-200"
                    style={{
                      backgroundColor: currency === c ? '#FF6B4A' : 'transparent',
                      color: currency === c ? '#FFFFFF' : '#7F8C8D',
                      boxShadow: currency === c ? '0 2px 6px rgba(255,107,74,0.35)' : 'none',
                    }}>
                    {c}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Search & Add */}
          <div className="bg-white rounded-xl shadow-sm px-5 py-4 mb-6 flex items-center gap-4">
            <div className="flex-1 relative">
              <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4" style={{ color: '#7F8C8D' }} />
              <input type="text" placeholder="Search by policy number, holder, or vehicle…"
                value={searchTerm} onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-2.5 rounded-lg border text-sm focus:outline-none focus:ring-2"
                style={{ borderColor: '#E5E7EB', backgroundColor: '#F8F9FA' }} />
            </div>
            <button onClick={openModal}
              className="flex items-center px-5 py-2.5 rounded-xl text-white font-semibold text-sm transition-all duration-200"
              style={{ backgroundColor: '#FF6B4A', boxShadow: '0 2px 8px rgba(255,107,74,0.3)' }}
              onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = '#E55A3A')}
              onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = '#FF6B4A')}>
              <Plus className="w-4 h-4 mr-2" /> Add Policy
            </button>
          </div>

          {/* Table */}
          {isLoading ? (
            <div className="text-center py-20">
              <Loader2 className="inline-block w-10 h-10 animate-spin mb-3" style={{ color: '#FF6B4A' }} />
              <p className="text-sm" style={{ color: '#7F8C8D' }}>Loading policies…</p>
            </div>
          ) : (
            <div className="bg-white rounded-xl shadow-sm overflow-hidden">
              <table className="w-full">
                <thead style={{ backgroundColor: '#F8F9FA', borderBottom: '2px solid #E5E7EB' }}>
                  <tr>
                    {['Policy Number', 'Policyholder', 'Vehicle', 'Type', `Premium (${currency})`, 'Status', 'Actions'].map((h) => (
                      <th key={h} className="px-6 py-4 text-left text-xs font-bold uppercase tracking-wider" style={{ color: '#2C3E50' }}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {filteredPolicies.length === 0 ? (
                    <tr>
                      <td colSpan="7" className="px-6 py-16 text-center text-sm" style={{ color: '#7F8C8D' }}>
                        {searchTerm ? 'No policies match your search.' : 'No policies yet. Issue the first one!'}
                      </td>
                    </tr>
                  ) : filteredPolicies.map((policy) => {
                    const sp = STATUS_PALETTE[policy.status] || STATUS_PALETTE.PENDING;
                    return (
                      <tr key={policy.id} onClick={() => navigate(`/policies/${policy.id}`)}
                        className="border-t transition-colors cursor-pointer group"
                        style={{ borderColor: '#F3F4F6' }}
                        onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = '#FFF5F3')}
                        onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = 'transparent')}>
                        <td className="px-6 py-4">
                          <div className="flex items-center gap-2">
                            <span className="font-mono text-xs font-bold px-2.5 py-1 rounded-lg" style={{ backgroundColor: '#F3F4F6', color: '#2C3E50' }}>{policy.policy_number}</span>
                            <ChevronRight className="w-3.5 h-3.5 opacity-0 group-hover:opacity-100 transition-opacity" style={{ color: '#FF6B4A' }} />
                          </div>
                        </td>
                        <td className="px-6 py-4 text-sm font-medium" style={{ color: '#2C3E50' }}>{policy.policyholder_name || '—'}</td>
                        <td className="px-6 py-4 text-sm" style={{ color: '#7F8C8D' }}>{policy.vehicle_display || '—'}</td>
                        <td className="px-6 py-4 text-sm" style={{ color: '#7F8C8D' }}>{POLICY_TYPES[policy.policy_type] || policy.policy_type}</td>
                        <td className="px-6 py-4 text-sm font-semibold" style={{ color: '#2C3E50' }}>{fmtMoney(policy.premium_amount, currency)}</td>
                        <td className="px-6 py-4">
                          <span className="px-3 py-1 rounded-full text-xs font-bold" style={{ backgroundColor: sp.bg, color: sp.color }}>
                            {STATUS_MAP[policy.status] || policy.status}
                          </span>
                        </td>
                        <td className="px-6 py-4">
                          <div className="flex items-center gap-2">
                            <button onClick={(e) => handleEdit(e, policy)} className="p-2 rounded-lg transition-colors" style={{ backgroundColor: '#EBF5FF', color: '#3B82F6' }} title="Edit">
                              <Edit className="w-3.5 h-3.5" />
                            </button>
                            <button onClick={(e) => handleDelete(e, policy.id)} className="p-2 rounded-lg transition-colors" style={{ backgroundColor: '#FEE2E2', color: '#EF4444' }} title="Delete">
                              <Trash2 className="w-3.5 h-3.5" />
                            </button>
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      {/* ══════════════════════════════════════════════════════════════════════
          MODAL
      ══════════════════════════════════════════════════════════════════════ */}
      {showModal && (
        <div className="fixed inset-0 flex items-center justify-center p-4 z-50"
          style={{ backgroundColor: 'rgba(0,0,0,0.55)', backdropFilter: 'blur(2px)' }}>
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-3xl flex flex-col overflow-hidden"
            style={{ maxHeight: '92vh' }}>

            {/* Modal Header */}
            <div className="flex items-center justify-between px-8 py-5 border-b flex-shrink-0" style={{ borderColor: '#E5E7EB' }}>
              <div>
                <h3 className="text-xl font-bold flex items-center gap-2" style={{ color: '#2C3E50' }}>
                  {editingId
                    ? <><Edit className="w-5 h-5" style={{ color: '#FF6B4A' }} /> Edit Policy</>
                    : <><Sparkles className="w-5 h-5" style={{ color: '#FF6B4A' }} /> Intelligent Policy Issuance</>}
                </h3>
                <p className="text-xs mt-0.5" style={{ color: '#7F8C8D' }}>{stepSubtitle}</p>
              </div>
              <div className="flex items-center gap-4">
                <StepIndicator step={modalStep} />
                <div className="flex gap-1 p-1 rounded-lg" style={{ backgroundColor: '#F3F4F6' }}>
                  {['USD', 'ZWG'].map((c) => (
                    <button key={c} type="button" onClick={() => setCurrency(c)}
                      className="px-3 py-1 rounded-md text-xs font-bold transition-all duration-200"
                      style={{
                        backgroundColor: currency === c ? '#FF6B4A' : 'transparent',
                        color: currency === c ? '#FFFFFF' : '#7F8C8D',
                      }}>
                      {c}
                    </button>
                  ))}
                </div>
                <button type="button" onClick={() => { setShowModal(false); resetForm(); }}
                  className="p-2 rounded-lg hover:bg-gray-100 transition-colors" style={{ color: '#7F8C8D' }}>
                  <X className="w-5 h-5" />
                </button>
              </div>
            </div>

            {/* Modal Body */}
            <div className="flex-1 overflow-y-auto">

              {/* ════ STEP 1 ════ */}
              {modalStep === 1 && (
                <div className="px-8 py-6 space-y-7">

                  {/* Customer & Vehicle */}
                  <div>
                    <p className="text-xs font-bold uppercase tracking-widest mb-4" style={{ color: '#7F8C8D' }}>Customer &amp; Vehicle</p>
                    <div className="grid grid-cols-2 gap-5">

                      {/* Policyholder */}
                      <div>
                        <label className="block text-sm font-semibold mb-1.5" style={{ color: '#2C3E50' }}>Policyholder *</label>
                        <div ref={phRef} className="relative">
                          <div className="relative">
                            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 pointer-events-none" style={{ color: '#9CA3AF' }} />
                            <input type="text" value={phSearch}
                              onChange={(e) => { setPhSearch(e.target.value); setShowPhDrop(true); }}
                              onFocus={() => setShowPhDrop(true)}
                              placeholder="Search by name or ID…"
                              className="w-full pl-9 pr-9 py-2.5 rounded-xl border text-sm focus:outline-none focus:ring-2 transition-all"
                              style={{ borderColor: selectedPH ? '#10B981' : '#E5E7EB', backgroundColor: selectedPH ? '#F0FDF4' : 'white' }} />
                            {phSearching
                              ? <Loader2 className="absolute right-2.5 top-1/2 -translate-y-1/2 w-4 h-4 animate-spin" style={{ color: '#9CA3AF' }} />
                              : selectedPH
                                ? <button type="button" onClick={clearPH} className="absolute right-2.5 top-1/2 -translate-y-1/2 p-1 rounded-md hover:bg-gray-100"><X className="w-3.5 h-3.5" style={{ color: '#9CA3AF' }} /></button>
                                : <ChevronDown className="absolute right-2.5 top-1/2 -translate-y-1/2 w-4 h-4 pointer-events-none" style={{ color: '#9CA3AF' }} />}
                          </div>
                          {selectedPH && (
                            <div className="mt-1.5 px-3 py-1.5 rounded-lg text-xs flex items-center gap-2 flex-wrap" style={{ backgroundColor: '#D1FAE5', color: '#065F46' }}>
                              <CheckCircle2 className="w-3.5 h-3.5 flex-shrink-0" />
                              <span>Credit: <strong>{selectedPH.credit_score}</strong></span>
                              <span style={{ color: '#6EE7B7' }}>·</span>
                              <span>Rating: <strong>{selectedPH.credit_rating}</strong></span>
                              <span style={{ color: '#6EE7B7' }}>·</span>
                              <span>Age: <strong>{selectedPH.age}</strong></span>
                            </div>
                          )}
                          {showPhDrop && !selectedPH && (
                            <div className="absolute z-50 w-full mt-1 bg-white rounded-xl shadow-xl overflow-hidden" style={{ border: '1px solid #E5E7EB' }}>
                              {phSearching
                                ? <div className="px-4 py-3 text-sm text-center flex items-center justify-center gap-2" style={{ color: '#9CA3AF' }}><Loader2 className="w-4 h-4 animate-spin" /><span>Searching…</span></div>
                                : phOptions.length > 0
                                  ? phOptions.map((ph) => (
                                    <button key={ph.id} type="button" onClick={() => applyPH(ph)}
                                      className="w-full text-left px-4 py-3 transition-colors border-b last:border-0" style={{ borderColor: '#F3F4F6' }}
                                      onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = '#FFF5F3')}
                                      onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = 'transparent')}>
                                      <div className="font-semibold text-sm" style={{ color: '#2C3E50' }}>{ph.full_name || `${ph.first_name} ${ph.last_name}`}</div>
                                      <div className="text-xs mt-0.5 flex items-center gap-2" style={{ color: '#9CA3AF' }}>
                                        <span>{ph.policy_holder_id}</span><span>·</span><span>{ph.email}</span>
                                      </div>
                                    </button>
                                  ))
                                  : <div className="px-4 py-3 text-sm text-center" style={{ color: '#9CA3AF' }}>{phSearch.length > 0 ? `No results for "${phSearch}"` : 'Start typing to search'}</div>}
                            </div>
                          )}
                        </div>
                      </div>

                      {/* Vehicle */}
                      <div>
                        <label className="block text-sm font-semibold mb-1.5" style={{ color: '#2C3E50' }}>
                          Vehicle *
                          {/* Only show "no vehicles registered" when PH is selected, no vehicle is selected, not searching, and options came back empty */}
                          {selectedPH && !selectedVeh && vehOptions.length === 0 && !vehSearching && (
                            <span className="ml-2 text-xs font-normal" style={{ color: '#EF4444' }}>(no vehicles registered)</span>
                          )}
                        </label>
                        <div ref={vehRef} className="relative">
                          <div className="relative">
                            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 pointer-events-none" style={{ color: '#9CA3AF' }} />
                            <input type="text" value={vehSearch}
                              onChange={(e) => { setVehSearch(e.target.value); setShowVehDrop(true); }}
                              onFocus={() => setShowVehDrop(true)}
                              disabled={!selectedPH}
                              placeholder={selectedPH ? 'Search vehicle…' : 'Select a policyholder first'}
                              className="w-full pl-9 pr-9 py-2.5 rounded-xl border text-sm focus:outline-none focus:ring-2 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                              style={{
                                borderColor: selectedVeh ? '#10B981' : '#E5E7EB',
                                backgroundColor: selectedVeh ? '#F0FDF4' : (selectedPH ? 'white' : '#F8F9FA'),
                              }} />
                            {vehSearching
                              ? <Loader2 className="absolute right-2.5 top-1/2 -translate-y-1/2 w-4 h-4 animate-spin" style={{ color: '#9CA3AF' }} />
                              : selectedVeh
                                ? <button type="button" onClick={clearVeh} className="absolute right-2.5 top-1/2 -translate-y-1/2 p-1 rounded-md hover:bg-gray-100"><X className="w-3.5 h-3.5" style={{ color: '#9CA3AF' }} /></button>
                                : <ChevronDown className="absolute right-2.5 top-1/2 -translate-y-1/2 w-4 h-4 pointer-events-none" style={{ color: '#9CA3AF' }} />}
                          </div>
                          {selectedVeh && (
                            <div className="mt-1.5 px-3 py-1.5 rounded-lg text-xs flex items-center gap-2 flex-wrap" style={{ backgroundColor: '#D1FAE5', color: '#065F46' }}>
                              <CheckCircle2 className="w-3.5 h-3.5 flex-shrink-0" />
                              <span>Value: <strong>{fmtMoney(selectedVeh.market_value, currency)}</strong></span>
                              <span style={{ color: '#6EE7B7' }}>·</span>
                              <span>Year: <strong>{selectedVeh.manufacture_year}</strong></span>
                              {selectedVeh.has_anti_theft && <><span style={{ color: '#6EE7B7' }}>·</span><span>🔒 Anti-theft</span></>}
                            </div>
                          )}
                          {showVehDrop && selectedPH && !selectedVeh && (
                            <div className="absolute z-50 w-full mt-1 bg-white rounded-xl shadow-xl overflow-hidden" style={{ border: '1px solid #E5E7EB' }}>
                              {vehSearching
                                ? <div className="px-4 py-3 text-sm text-center flex items-center justify-center gap-2" style={{ color: '#9CA3AF' }}><Loader2 className="w-4 h-4 animate-spin" /><span>Loading…</span></div>
                                : vehOptions.length > 0
                                  ? vehOptions.map((veh) => (
                                    <button key={veh.id} type="button" onClick={() => applyVeh(veh)}
                                      className="w-full text-left px-4 py-3 transition-colors border-b last:border-0" style={{ borderColor: '#F3F4F6' }}
                                      onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = '#FFF5F3')}
                                      onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = 'transparent')}>
                                      <div className="font-semibold text-sm" style={{ color: '#2C3E50' }}>{veh.make} {veh.model} ({veh.manufacture_year})</div>
                                      <div className="text-xs mt-0.5 flex items-center gap-2" style={{ color: '#9CA3AF' }}>
                                        <span>{veh.registration_number}</span><span>·</span><span>Value: {fmtMoney(veh.market_value, currency)}</span>
                                        {veh.vehicle_type && <><span>·</span><span>{veh.vehicle_type}</span></>}
                                      </div>
                                    </button>
                                  ))
                                  : <div className="px-4 py-3 text-sm text-center" style={{ color: '#9CA3AF' }}>No vehicles registered for this policyholder</div>}
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Policy Configuration */}
                  <div>
                    <p className="text-xs font-bold uppercase tracking-widest mb-4" style={{ color: '#7F8C8D' }}>Policy Configuration</p>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-semibold mb-1.5" style={{ color: '#2C3E50' }}>Policy Type *</label>
                        <select required value={formData.policy_type}
                          onChange={(e) => setFormData((p) => ({ ...p, policy_type: e.target.value }))}
                          className="w-full px-3 py-2.5 rounded-xl border text-sm focus:outline-none focus:ring-2 bg-white" style={{ borderColor: '#E5E7EB' }}>
                          {Object.entries(POLICY_TYPES).map(([v, l]) => <option key={v} value={v}>{l}</option>)}
                        </select>
                      </div>
                      <div>
                        <label className="block text-sm font-semibold mb-1.5" style={{ color: '#2C3E50' }}>Coverage Level *</label>
                        <select required value={formData.coverage_level}
                          onChange={(e) => setFormData((p) => ({ ...p, coverage_level: e.target.value }))}
                          className="w-full px-3 py-2.5 rounded-xl border text-sm focus:outline-none focus:ring-2 bg-white" style={{ borderColor: '#E5E7EB' }}>
                          <option value="BASIC">Basic (80% vehicle value)</option>
                          <option value="STANDARD">Standard (100% vehicle value)</option>
                          <option value="PREMIUM">Premium (120% vehicle value)</option>
                        </select>
                      </div>
                      <div>
                        <label className="block text-sm font-semibold mb-1.5" style={{ color: '#2C3E50' }}>Start Date *</label>
                        <input type="date" required value={formData.start_date}
                          onChange={(e) => setFormData((p) => ({ ...p, start_date: e.target.value }))}
                          className="w-full px-3 py-2.5 rounded-xl border text-sm focus:outline-none focus:ring-2" style={{ borderColor: '#E5E7EB' }} />
                      </div>
                      <div>
                        <label className="block text-sm font-semibold mb-1.5" style={{ color: '#2C3E50' }}>End Date *</label>
                        <input type="date" required value={formData.end_date} min={formData.start_date}
                          onChange={(e) => setFormData((p) => ({ ...p, end_date: e.target.value }))}
                          className="w-full px-3 py-2.5 rounded-xl border text-sm focus:outline-none focus:ring-2" style={{ borderColor: '#E5E7EB' }} />
                      </div>
                      <div className="col-span-2">
                        <label className="block text-sm font-semibold mb-1.5" style={{ color: '#2C3E50' }}>Status</label>
                        <select value={formData.status}
                          onChange={(e) => setFormData((p) => ({ ...p, status: e.target.value }))}
                          className="w-full px-3 py-2.5 rounded-xl border text-sm focus:outline-none focus:ring-2 bg-white" style={{ borderColor: '#E5E7EB' }}>
                          {Object.entries(STATUS_MAP).map(([v, l]) => <option key={v} value={v}>{l}</option>)}
                        </select>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* ════ STEP 2 ════ */}
              {modalStep === 2 && (
                <div className="px-8 py-6">

                  {/* Context summary bar */}
                  <div className="flex items-center gap-3 p-4 rounded-xl mb-6" style={{ backgroundColor: '#F8F9FA', border: '1px solid #E5E7EB' }}>
                    <div className="flex-1 min-w-0">
                      <p className="text-xs font-bold uppercase tracking-wider mb-1" style={{ color: '#9CA3AF' }}>Policy Summary</p>
                      <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
                        <span className="text-sm font-semibold" style={{ color: '#2C3E50' }}>
                          {selectedPH?.full_name || `${selectedPH?.first_name} ${selectedPH?.last_name}`}
                        </span>
                        <span style={{ color: '#E5E7EB' }}>·</span>
                        <span className="text-sm" style={{ color: '#7F8C8D' }}>
                          {selectedVeh?.make} {selectedVeh?.model} ({selectedVeh?.manufacture_year})
                        </span>
                        <span style={{ color: '#E5E7EB' }}>·</span>
                        <span className="text-xs font-medium px-2 py-0.5 rounded-full" style={{ backgroundColor: '#EBF5FF', color: '#3B82F6' }}>
                          {POLICY_TYPES[formData.policy_type]}
                        </span>
                        <span className="text-xs font-medium px-2 py-0.5 rounded-full" style={{ backgroundColor: '#F3F4F6', color: '#7F8C8D' }}>
                          {formData.coverage_level.charAt(0) + formData.coverage_level.slice(1).toLowerCase()}
                        </span>
                      </div>
                    </div>
                    <button type="button" onClick={() => setModalStep(1)}
                      className="text-xs font-semibold flex items-center gap-1 px-3 py-1.5 rounded-lg transition-colors"
                      style={{ color: '#FF6B4A', backgroundColor: '#FFF5F3' }}
                      onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = '#FFE8E3')}
                      onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = '#FFF5F3')}>
                      <ArrowLeft className="w-3 h-3" /> Edit details
                    </button>
                  </div>

                  {/* Premium Calculator */}
                  <div className="rounded-2xl border-2 overflow-hidden"
                    style={{
                      borderColor: premiumData ? '#A7F3D0' : '#E5E7EB',
                      background: premiumData ? 'linear-gradient(135deg,#F0FDF4 0%,#ECFDF5 100%)' : '#F8F9FA',
                      transition: 'all 0.4s ease',
                    }}>

                    {/* Card header */}
                    <div className="flex items-center justify-between px-6 py-5 border-b" style={{ borderColor: premiumData ? '#D1FAE5' : '#E5E7EB' }}>
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-xl flex items-center justify-center" style={{ backgroundColor: premiumData ? '#D1FAE5' : '#E5E7EB' }}>
                          <Calculator className="w-5 h-5" style={{ color: premiumData ? '#059669' : '#9CA3AF' }} />
                        </div>
                        <div>
                          <p className="text-base font-bold" style={{ color: premiumData ? '#065F46' : '#9CA3AF' }}>AI Premium Calculator</p>
                          <p className="text-xs" style={{ color: premiumData ? '#6EE7B7' : '#D1D5DB' }}>
                            {isCalcing ? 'Calculating your premium…' : premiumData ? 'Recalculates as you change add-ons or coverage' : 'Fetching price…'}
                          </p>
                        </div>
                      </div>
                      {isCalcing ? (
                        <div className="flex items-center gap-2 text-sm" style={{ color: '#059669' }}>
                          <Loader2 className="w-4 h-4 animate-spin" />
                          <span className="font-medium">Calculating…</span>
                        </div>
                      ) : premiumData?.confidence != null ? (
                        <div className="text-right">
                          <p className="text-xs font-semibold" style={{ color: '#059669' }}>AI Confidence</p>
                          <p className="text-3xl font-bold leading-tight" style={{ color: '#065F46' }}>
                            {(premiumData.confidence * 100).toFixed(0)}%
                          </p>
                        </div>
                      ) : null}
                    </div>

                    {/* Three metric cards */}
                    <div className="p-6 grid grid-cols-3 gap-4">
                      {[
                        { label: 'Annual Premium', key: 'premium_amount', hint: `Deductible: ${COVERAGE_HINTS[formData.coverage_level]?.ded ?? '—'}`, icon: <TrendingUp className="w-4 h-4" />, big: true },
                        { label: 'Coverage Amount', key: 'coverage_amount', hint: `${COVERAGE_HINTS[formData.coverage_level]?.pct ?? '—'} of vehicle value`, icon: <ShieldCheck className="w-4 h-4" /> },
                        { label: 'Deductible', key: 'deductible', hint: `${COVERAGE_HINTS[formData.coverage_level]?.ded ?? '—'} of coverage`, icon: <Info className="w-4 h-4" /> },
                      ].map(({ label, key, hint, icon, big }) => (
                        <div key={key} className="rounded-xl p-5"
                          style={{
                            backgroundColor: premiumData ? 'white' : '#F3F4F6',
                            border: premiumData ? '1px solid #A7F3D0' : '1px solid #E5E7EB',
                            transition: 'all 0.3s ease',
                          }}>
                          <div className="flex items-center gap-1.5 mb-3" style={{ color: premiumData ? '#059669' : '#9CA3AF' }}>
                            {icon}
                            <span className="text-xs font-semibold">{label}</span>
                          </div>
                          {isCalcing ? (
                            <div className="h-8 rounded-lg animate-pulse" style={{ backgroundColor: '#D1FAE5' }} />
                          ) : premiumData ? (
                            <>
                              <div className={`font-bold ${big ? 'text-2xl' : 'text-xl'}`} style={{ color: '#065F46' }}>
                                {fmtMoney(premiumData[key], currency)}
                              </div>
                              <div className="text-xs mt-1.5" style={{ color: '#6EE7B7' }}>{hint}</div>
                            </>
                          ) : (
                            <div className="text-xl font-bold" style={{ color: '#D1D5DB' }}>—</div>
                          )}
                        </div>
                      ))}
                    </div>

                    {/* Confidence bar */}
                    {premiumData?.confidence != null && !isCalcing && (
                      <div className="px-6 pb-5">
                        <div className="flex justify-between text-xs mb-1.5" style={{ color: '#6EE7B7' }}>
                          <span>Model confidence</span>
                          <span className="font-bold">{(premiumData.confidence * 100).toFixed(0)}%</span>
                        </div>
                        <div className="w-full h-2 rounded-full" style={{ backgroundColor: '#D1FAE5' }}>
                          <div className="h-2 rounded-full transition-all duration-700 ease-out"
                            style={{ width: `${premiumData.confidence * 100}%`, backgroundColor: '#10B981' }} />
                        </div>
                      </div>
                    )}

                    {/* Add-ons */}
                    <div className="px-6 pb-5 border-t pt-4" style={{ borderColor: '#D1FAE5' }}>
                      <p className="text-xs font-semibold uppercase tracking-wider mb-3" style={{ color: '#6EE7B7' }}>
                        Optional Add-ons
                      </p>
                      {!pricingSettings ? (
                        <div className="flex items-center gap-2 text-xs" style={{ color: '#9CA3AF' }}>
                          <Loader2 className="w-3.5 h-3.5 animate-spin" /> Loading prices…
                        </div>
                      ) : (
                        <div className="flex flex-wrap gap-2">
                          {ADD_ONS.map(({ key, label, price }) => {
                            const active = formData[key];
                            return (
                              <label key={key}
                                className="flex items-center gap-2 px-3 py-2 rounded-xl border-2 cursor-pointer transition-all duration-200 select-none"
                                style={{
                                  borderColor: active ? '#10B981' : '#D1FAE5',
                                  backgroundColor: active ? '#D1FAE5' : 'white',
                                }}>
                                <input
                                  type="checkbox"
                                  checked={active}
                                  onChange={(e) => setFormData((p) => ({ ...p, [key]: e.target.checked }))}
                                  className="w-3.5 h-3.5 rounded flex-shrink-0"
                                  style={{ accentColor: '#10B981' }}
                                />
                                <span className="text-xs font-semibold" style={{ color: active ? '#065F46' : '#6B7280' }}>
                                  {label}
                                </span>
                                <span className="text-xs" style={{ color: active ? '#10B981' : '#9CA3AF' }}>
                                  {price}
                                </span>
                              </label>
                            );
                          })}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Modal Footer */}
            <div className="flex items-center justify-between px-8 py-4 border-t flex-shrink-0"
              style={{ borderColor: '#E5E7EB', backgroundColor: '#F8F9FA' }}>
              {modalStep === 1 ? (
                <button type="button" onClick={() => { setShowModal(false); resetForm(); }}
                  className="px-5 py-2.5 rounded-xl text-sm font-semibold transition-colors"
                  style={{ backgroundColor: 'white', color: '#7F8C8D', border: '1px solid #E5E7EB' }}>
                  Cancel
                </button>
              ) : (
                <button type="button" onClick={() => setModalStep(1)}
                  className="flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-semibold transition-colors"
                  style={{ backgroundColor: 'white', color: '#7F8C8D', border: '1px solid #E5E7EB' }}>
                  <ArrowLeft className="w-4 h-4" /> Back
                </button>
              )}

              {modalStep === 1 ? (
                <button type="button" onClick={handleNextStep}
                  className="flex items-center gap-2 px-6 py-2.5 rounded-xl text-white text-sm font-bold transition-all duration-200"
                  style={{ backgroundColor: '#FF6B4A', boxShadow: '0 2px 8px rgba(255,107,74,0.35)' }}
                  onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = '#E55A3A')}
                  onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = '#FF6B4A')}>
                  Review Pricing <ArrowRight className="w-4 h-4" />
                </button>
              ) : (
                <button type="button" onClick={handleSubmit} disabled={isSaving}
                  className="flex items-center gap-2 px-6 py-2.5 rounded-xl text-white text-sm font-bold transition-all duration-200 disabled:opacity-60"
                  style={{ backgroundColor: '#FF6B4A', boxShadow: '0 2px 8px rgba(255,107,74,0.35)' }}
                  onMouseEnter={(e) => { if (!isSaving) e.currentTarget.style.backgroundColor = '#E55A3A'; }}
                  onMouseLeave={(e) => { if (!isSaving) e.currentTarget.style.backgroundColor = '#FF6B4A'; }}>
                  {isSaving
                    ? <><Loader2 className="w-4 h-4 animate-spin" /> Saving…</>
                    : editingId
                      ? <><Edit className="w-4 h-4" /> Update Policy</>
                      : <><Sparkles className="w-4 h-4" /> Issue Policy</>}
                </button>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}