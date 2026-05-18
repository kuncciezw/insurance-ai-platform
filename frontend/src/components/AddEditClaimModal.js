import { useState, useEffect, useRef, useCallback } from 'react';
import { X, Search, Loader2, CheckCircle2, ChevronDown, Upload, FileText, AlertTriangle } from 'lucide-react';
import { api } from '../services/api';

const CLAIM_TYPES = [
  { value: 'ACCIDENT',         label: 'Accident' },
  { value: 'THEFT',            label: 'Theft' },
  { value: 'VANDALISM',        label: 'Vandalism' },
  { value: 'NATURAL_DISASTER', label: 'Natural Disaster' },
  { value: 'FIRE',             label: 'Fire' },
  { value: 'OTHER',            label: 'Other' },
];

const SEVERITIES = [
  { value: 'MINOR',      label: 'Minor' },
  { value: 'MODERATE',   label: 'Moderate' },
  { value: 'MAJOR',      label: 'Major' },
  { value: 'TOTAL_LOSS', label: 'Total Loss' },
];

const PAYMENT_METHODS = [
  { value: 'BANK_TRANSFER', label: 'Bank Transfer' },
  { value: 'SWIPE',         label: 'Swipe Card' },
  { value: 'ECOCASH',       label: 'EcoCash' },
  { value: 'CASH',          label: 'Cash' },
];

const todayISO = () => new Date().toISOString().slice(0, 16);

const blankForm = () => ({
  policy:           '',
  claim_type:       'ACCIDENT',
  severity:         'MINOR',
  incident_date:    '',
  incident_location:'',
  payment_method:   'BANK_TRANSFER',
});

export default function AddEditClaimModal({ isOpen, onClose, onSuccess, editingClaim = null }) {
  const [formData,        setFormData]        = useState(blankForm());
  const [evidenceFile,    setEvidenceFile]     = useState(null);
  const [existingEvidence,setExistingEvidence] = useState(null);
  const [isSaving,        setIsSaving]         = useState(false);
  const [errors,          setErrors]           = useState({});

  // Policy searchable select
  const [policySearch,    setPolicySearch]     = useState('');
  const [policyOptions,   setPolicyOptions]    = useState([]);
  const [showPolicyDrop,  setShowPolicyDrop]   = useState(false);
  const [policySearching, setPolicySearching]  = useState(false);
  const [selectedPolicy,  setSelectedPolicy]   = useState(null);

  const policyRef    = useRef(null);
  const fileInputRef = useRef(null);
  const debounceRef  = useRef(null);

  // ── Close dropdown on outside click ──────────────────────────────────────
  useEffect(() => {
    const handler = (e) => {
      if (policyRef.current && !policyRef.current.contains(e.target))
        setShowPolicyDrop(false);
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  // ── Reset / Load on open ─────────────────────────────────────────────────
  useEffect(() => {
    if (!isOpen) return;
    if (editingClaim) {
      loadClaimData(editingClaim);
    } else {
      resetForm();
    }
  }, [isOpen, editingClaim]);

  const loadClaimData = async (claim) => {
    setFormData({
      policy:            claim.policy         || '',
      claim_type:        claim.claim_type     || 'ACCIDENT',
      severity:          claim.severity       || 'MINOR',
      incident_date:     claim.incident_date
                           ? claim.incident_date.slice(0, 16)
                           : '',
      incident_location: claim.incident_location || '',
      payment_method:    claim.payment_method    || 'BANK_TRANSFER',
    });
    setExistingEvidence(claim.incident_evidence || null);

    if (claim.policy) {
      try {
        const pol = await api.getPolicy(claim.policy);
        setSelectedPolicy(pol);
        setPolicySearch(pol.policy_number || '');
      } catch {
        setSelectedPolicy({
          id:               claim.policy,
          policy_number:    claim.policy_number    || 'Policy',
          policyholder_name: claim.policyholder_name || '',
          vehicle_display:  claim.vehicle_display  || '',
        });
        setPolicySearch(claim.policy_number || '');
      }
    }
  };

  const resetForm = () => {
    setFormData(blankForm());
    setEvidenceFile(null);
    setExistingEvidence(null);
    setSelectedPolicy(null);
    setPolicySearch('');
    setPolicyOptions([]);
    setErrors({});
  };

  // ── Debounced policy search ───────────────────────────────────────────────
  useEffect(() => {
    if (selectedPolicy) return;
    clearTimeout(debounceRef.current);

    debounceRef.current = setTimeout(async () => {
      setPolicySearching(true);
      try {
        const params = policySearch.length > 0
          ? { search: policySearch, page_size: 20 }
          : { page_size: 30 };
        const data = await api.getPolicies(params);
        setPolicyOptions(data.results || data);
      } catch {
        setPolicyOptions([]);
      } finally {
        setPolicySearching(false);
      }
    }, policySearch.length > 0 ? 350 : 100);

    return () => clearTimeout(debounceRef.current);
  }, [policySearch, selectedPolicy]);

  const applyPolicy = (pol) => {
    setSelectedPolicy(pol);
    setPolicySearch(pol.policy_number || '');
    setFormData((prev) => ({ ...prev, policy: String(pol.id) }));
    setShowPolicyDrop(false);
    setErrors((prev) => ({ ...prev, policy: undefined }));
  };

  const clearPolicy = () => {
    setSelectedPolicy(null);
    setPolicySearch('');
    setPolicyOptions([]);
    setFormData((prev) => ({ ...prev, policy: '' }));
  };

  // ── File handling ─────────────────────────────────────────────────────────
  const handleFileChange = (e) => {
    const file = e.target.files?.[0] || null;
    setEvidenceFile(file);
    if (file) setErrors((prev) => ({ ...prev, incident_evidence: undefined }));
  };

  // ── Validation ────────────────────────────────────────────────────────────
  const validate = () => {
    const errs = {};
    if (!formData.policy)                   errs.policy            = 'Please select a policy.';
    if (!formData.incident_date)            errs.incident_date     = 'Incident date is required.';
    if (!formData.incident_location.trim()) errs.incident_location = 'Location is required.';
    return errs;
  };

  // ── Submit via FormData ───────────────────────────────────────────────────
  const handleSubmit = async (e) => {
    e.preventDefault();
    const errs = validate();
    if (Object.keys(errs).length) { setErrors(errs); return; }

    setIsSaving(true);
    try {
      const fd = new FormData();

      fd.append('policy',            formData.policy);
      fd.append('claim_type',        formData.claim_type);
      fd.append('severity',          formData.severity);
      fd.append('incident_date',     formData.incident_date);
      fd.append('incident_location', formData.incident_location);
      fd.append('payment_method',    formData.payment_method);

      if (evidenceFile) {
        fd.append('incident_evidence', evidenceFile);
      }

      if (!editingClaim) {
        fd.append('claim_number', `CLM-${Date.now().toString().slice(-10)}`);
      }

      // ── KEY CHANGE: pass the new claim back so parent can navigate to it ──
      if (editingClaim) {
        await api.updateClaim(editingClaim.id, fd);
        onSuccess(null);   // edit — just refresh the list
        onClose();
      } else {
        const newClaim = await api.createClaim(fd);
        onSuccess(newClaim);  // create — hand the new claim object up
        onClose();
      }
    } catch (err) {
      console.error('Failed to save claim:', err);
      const msg = err?.data
        ? Object.entries(err.data).map(([f, m]) => `${f}: ${Array.isArray(m) ? m.join(', ') : m}`).join('\n')
        : (err.message || 'Unknown error');
      setErrors({ _form: msg });
    } finally {
      setIsSaving(false);
    }
  };

  if (!isOpen) return null;

  const inputBase = 'w-full px-4 py-2.5 rounded-xl border text-sm focus:outline-none focus:ring-2 focus:ring-orange-300 transition-all bg-white';
  const labelBase = 'block text-xs font-bold uppercase tracking-wider mb-1.5';

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4"
         style={{ backgroundColor: 'rgba(0,0,0,0.55)', backdropFilter: 'blur(2px)' }}>
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-2xl flex flex-col overflow-hidden"
           style={{ maxHeight: '92vh' }}>

        {/* ── Header ──────────────────────────────────────────────────────── */}
        <div className="flex items-center justify-between px-7 py-5 border-b flex-shrink-0"
             style={{ borderColor: '#E5E7EB' }}>
          <div>
            <h3 className="text-xl font-bold flex items-center gap-2" style={{ color: '#2C3E50' }}>
              <FileText className="w-5 h-5" style={{ color: '#FF6B4A' }} />
              {editingClaim ? 'Edit Claim' : 'First Notice of Loss'}
            </h3>
            <p className="text-xs mt-0.5" style={{ color: '#9CA3AF' }}>
              {editingClaim
                ? 'Update claim details'
                : 'Submit a new insurance claim'}
            </p>
          </div>
          <button onClick={() => { onClose(); resetForm(); }}
                  className="p-2 rounded-lg hover:bg-gray-100 transition-colors"
                  style={{ color: '#7F8C8D' }}>
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* ── Body ────────────────────────────────────────────────────────── */}
        <form onSubmit={handleSubmit} className="flex-1 overflow-y-auto px-7 py-6 space-y-6">

          {errors._form && (
            <div className="p-3 rounded-xl flex items-start gap-2 text-xs"
                 style={{ backgroundColor: '#FEE2E2', color: '#991B1B' }}>
              <AlertTriangle className="w-4 h-4 flex-shrink-0 mt-0.5" />
              <pre className="whitespace-pre-wrap font-sans">{errors._form}</pre>
            </div>
          )}

          {/* ── Section 1: Policy ─────────────────────────────────────────── */}
          <div>
            <p className="text-xs font-bold uppercase tracking-widest mb-4" style={{ color: '#7F8C8D' }}>
              Policy Selection
            </p>

            <div>
              <label className={labelBase} style={{ color: '#2C3E50' }}>Policy *</label>
              <div ref={policyRef} className="relative">
                <div className="relative">
                  <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 pointer-events-none"
                          style={{ color: '#9CA3AF' }} />
                  <input
                    type="text"
                    value={policySearch}
                    onChange={(e) => { setPolicySearch(e.target.value); setShowPolicyDrop(true); }}
                    onFocus={() => setShowPolicyDrop(true)}
                    placeholder="Type policy number to search…"
                    className={`${inputBase} pl-10 pr-10`}
                    style={{
                      borderColor:     errors.policy ? '#EF4444' : selectedPolicy ? '#10B981' : '#E5E7EB',
                      backgroundColor: selectedPolicy ? '#F0FDF4' : 'white',
                    }}
                  />
                  {policySearching ? (
                    <Loader2 className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 animate-spin"
                             style={{ color: '#9CA3AF' }} />
                  ) : selectedPolicy ? (
                    <button type="button" onClick={clearPolicy}
                            className="absolute right-3 top-1/2 -translate-y-1/2 p-1 rounded-md hover:bg-gray-100">
                      <X className="w-3.5 h-3.5" style={{ color: '#9CA3AF' }} />
                    </button>
                  ) : (
                    <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 pointer-events-none"
                                 style={{ color: '#9CA3AF' }} />
                  )}
                </div>

                {showPolicyDrop && !selectedPolicy && (
                  <div className="absolute z-50 w-full mt-1 bg-white rounded-xl shadow-xl overflow-hidden"
                       style={{ border: '1px solid #E5E7EB', maxHeight: 220, overflowY: 'auto' }}>
                    {policySearching ? (
                      <div className="px-4 py-3 text-sm flex items-center gap-2 justify-center"
                           style={{ color: '#9CA3AF' }}>
                        <Loader2 className="w-4 h-4 animate-spin" />
                        <span>Searching policies…</span>
                      </div>
                    ) : policyOptions.length > 0 ? (
                      policyOptions.map((pol) => (
                        <button key={pol.id} type="button" onClick={() => applyPolicy(pol)}
                                className="w-full text-left px-4 py-3 border-b last:border-0 transition-colors"
                                style={{ borderColor: '#F3F4F6' }}
                                onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = '#FFF5F3')}
                                onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = 'transparent')}>
                          <div className="font-semibold text-sm" style={{ color: '#2C3E50' }}>
                            {pol.policy_number}
                          </div>
                          <div className="text-xs mt-0.5 flex items-center gap-2" style={{ color: '#9CA3AF' }}>
                            <span>{pol.policyholder_name || '—'}</span>
                            <span>·</span>
                            <span>{pol.vehicle_display || pol.policy_type}</span>
                            <span>·</span>
                            <span className="font-medium" style={{
                              color: pol.status === 'ACTIVE' ? '#10B981' : '#EF4444'
                            }}>{pol.status}</span>
                          </div>
                        </button>
                      ))
                    ) : (
                      <div className="px-4 py-3 text-sm text-center" style={{ color: '#9CA3AF' }}>
                        {policySearch.length > 0
                          ? `No policies match "${policySearch}"`
                          : 'Start typing to search policies'}
                      </div>
                    )}
                  </div>
                )}
              </div>
              {errors.policy && (
                <p className="mt-1 text-xs" style={{ color: '#EF4444' }}>{errors.policy}</p>
              )}
            </div>

            {selectedPolicy && (
              <div className="mt-3 p-4 rounded-xl border-2 flex items-start gap-4"
                   style={{ backgroundColor: '#F0FDF4', borderColor: '#A7F3D0' }}>
                <CheckCircle2 className="w-5 h-5 flex-shrink-0 mt-0.5" style={{ color: '#10B981' }} />
                <div className="min-w-0 flex-1">
                  <p className="text-xs font-bold uppercase tracking-wider mb-2" style={{ color: '#059669' }}>
                    Policy auto-populated
                  </p>
                  <div className="grid grid-cols-2 gap-x-6 gap-y-1 text-xs">
                    <div>
                      <span style={{ color: '#6EE7B7' }}>Policyholder</span>
                      <p className="font-semibold truncate" style={{ color: '#065F46' }}>
                        {selectedPolicy.policyholder_name || '—'}
                      </p>
                    </div>
                    <div>
                      <span style={{ color: '#6EE7B7' }}>Vehicle</span>
                      <p className="font-semibold truncate" style={{ color: '#065F46' }}>
                        {selectedPolicy.vehicle_display || '—'}
                      </p>
                    </div>
                    <div>
                      <span style={{ color: '#6EE7B7' }}>Type</span>
                      <p className="font-semibold" style={{ color: '#065F46' }}>
                        {selectedPolicy.policy_type || '—'}
                      </p>
                    </div>
                    <div>
                      <span style={{ color: '#6EE7B7' }}>Status</span>
                      <p className="font-semibold" style={{
                        color: selectedPolicy.status === 'ACTIVE' ? '#065F46' : '#991B1B'
                      }}>
                        {selectedPolicy.status || '—'}
                      </p>
                    </div>
                  </div>
                  {selectedPolicy.status !== 'ACTIVE' && (
                    <div className="mt-2 flex items-center gap-1.5 text-xs"
                         style={{ color: '#DC2626' }}>
                      <AlertTriangle className="w-3.5 h-3.5" />
                      <span>Warning: this policy is not active — the claim may be auto-rejected.</span>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>

          {/* ── Section 2: Incident Details ───────────────────────────────── */}
          <div>
            <p className="text-xs font-bold uppercase tracking-widest mb-4" style={{ color: '#7F8C8D' }}>
              Incident Details
            </p>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className={labelBase} style={{ color: '#2C3E50' }}>Claim Type *</label>
                <select
                  required
                  value={formData.claim_type}
                  onChange={(e) => setFormData((p) => ({ ...p, claim_type: e.target.value }))}
                  className={inputBase}
                  style={{ borderColor: '#E5E7EB' }}>
                  {CLAIM_TYPES.map(({ value, label }) => (
                    <option key={value} value={value}>{label}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className={labelBase} style={{ color: '#2C3E50' }}>Severity *</label>
                <select
                  required
                  value={formData.severity}
                  onChange={(e) => setFormData((p) => ({ ...p, severity: e.target.value }))}
                  className={inputBase}
                  style={{ borderColor: '#E5E7EB' }}>
                  {SEVERITIES.map(({ value, label }) => (
                    <option key={value} value={value}>{label}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className={labelBase} style={{ color: '#2C3E50' }}>Incident Date &amp; Time *</label>
                <input
                  type="datetime-local"
                  required
                  max={todayISO()}
                  value={formData.incident_date}
                  onChange={(e) => {
                    setFormData((p) => ({ ...p, incident_date: e.target.value }));
                    setErrors((prev) => ({ ...prev, incident_date: undefined }));
                  }}
                  className={inputBase}
                  style={{ borderColor: errors.incident_date ? '#EF4444' : '#E5E7EB' }}
                />
                {errors.incident_date && (
                  <p className="mt-1 text-xs" style={{ color: '#EF4444' }}>{errors.incident_date}</p>
                )}
              </div>

              <div>
                <label className={labelBase} style={{ color: '#2C3E50' }}>Incident Location *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g., Harare CBD, Corner 1st St"
                  value={formData.incident_location}
                  onChange={(e) => {
                    setFormData((p) => ({ ...p, incident_location: e.target.value }));
                    setErrors((prev) => ({ ...prev, incident_location: undefined }));
                  }}
                  className={inputBase}
                  style={{ borderColor: errors.incident_location ? '#EF4444' : '#E5E7EB' }}
                />
                {errors.incident_location && (
                  <p className="mt-1 text-xs" style={{ color: '#EF4444' }}>{errors.incident_location}</p>
                )}
              </div>
            </div>
          </div>

          {/* ── Section 3: Payment & Evidence ────────────────────────────── */}
          <div>
            <p className="text-xs font-bold uppercase tracking-widest mb-4" style={{ color: '#7F8C8D' }}>
              Payment &amp; Evidence
            </p>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className={labelBase} style={{ color: '#2C3E50' }}>Preferred Payment Method *</label>
                <select
                  required
                  value={formData.payment_method}
                  onChange={(e) => setFormData((p) => ({ ...p, payment_method: e.target.value }))}
                  className={inputBase}
                  style={{ borderColor: '#E5E7EB' }}>
                  {PAYMENT_METHODS.map(({ value, label }) => (
                    <option key={value} value={value}>{label}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className={labelBase} style={{ color: '#2C3E50' }}>Evidence Upload</label>
                <div
                  onClick={() => fileInputRef.current?.click()}
                  className="flex items-center gap-3 px-4 py-2.5 rounded-xl border cursor-pointer transition-all text-sm"
                  style={{
                    borderColor:     evidenceFile ? '#10B981' : '#E5E7EB',
                    borderStyle:     'dashed',
                    backgroundColor: evidenceFile ? '#F0FDF4' : '#F8F9FA',
                    color:           evidenceFile ? '#065F46' : '#9CA3AF',
                  }}
                  onMouseEnter={(e) => (e.currentTarget.style.borderColor = '#FF6B4A')}
                  onMouseLeave={(e) => (e.currentTarget.style.borderColor = evidenceFile ? '#10B981' : '#E5E7EB')}>
                  <Upload className="w-4 h-4 flex-shrink-0" />
                  <span className="truncate text-xs">
                    {evidenceFile
                      ? evidenceFile.name
                      : existingEvidence
                        ? 'Replace existing file…'
                        : 'Photo, PDF or doc'}
                  </span>
                </div>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="image/*,.pdf,.doc,.docx"
                  onChange={handleFileChange}
                  className="hidden"
                />
                {existingEvidence && !evidenceFile && (
                  <p className="mt-1 text-xs" style={{ color: '#6B7280' }}>
                    Existing evidence on file. Upload a new file to replace it.
                  </p>
                )}
              </div>
            </div>
          </div>

        </form>

        {/* ── Footer ──────────────────────────────────────────────────────── */}
        <div className="flex items-center justify-end gap-3 px-7 py-4 border-t flex-shrink-0"
             style={{ borderColor: '#E5E7EB', backgroundColor: '#F8F9FA' }}>
          <button
            type="button"
            onClick={() => { onClose(); resetForm(); }}
            className="px-5 py-2.5 rounded-xl text-sm font-semibold transition-colors"
            style={{ backgroundColor: 'white', color: '#7F8C8D', border: '1px solid #E5E7EB' }}>
            Cancel
          </button>
          <button
            type="submit"
            form="fnol-form"
            disabled={isSaving}
            onClick={handleSubmit}
            className="flex items-center gap-2 px-6 py-2.5 rounded-xl text-white text-sm font-bold transition-all disabled:opacity-60"
            style={{ backgroundColor: '#FF6B4A', boxShadow: '0 2px 8px rgba(255,107,74,0.35)' }}
            onMouseEnter={(e) => { if (!isSaving) e.currentTarget.style.backgroundColor = '#E55A3A'; }}
            onMouseLeave={(e) => { if (!isSaving) e.currentTarget.style.backgroundColor = '#FF6B4A'; }}>
            {isSaving
              ? <><Loader2 className="w-4 h-4 animate-spin" /> Saving…</>
              : editingClaim
                ? 'Update Claim'
                : 'Submit Claim'}
          </button>
        </div>
      </div>
    </div>
  );
}