import { useState, useEffect } from 'react';
import { api } from '../services/api';
import { usePricingSettings } from '../contexts/PricingSettingsContext';
import {
  TrendingUp, Calculator, AlertCircle, Loader2,
  ArrowLeftRight, Car, Wrench, Lock, ChevronDown,
} from 'lucide-react';


export default function EmbeddedLossAssessor({ claim, vehicle }) {
  const [currency,  setCurrency]  = useState('USD');
  const [isLoading, setIsLoading] = useState(false);
  const { settings } = usePricingSettings();
  const exchangeRate = settings?.zwg_usd_exchange_rate;
  const [result,    setResult]    = useState(null);
  const [error,     setError]     = useState('');

  // Auto-populated read-only fields (raw USD)
  const [autoFields, setAutoFields] = useState({
    vehicle_age_years:  '',
    vehicle_value:      '',
    incident_type:      '',
    incident_severity:  '',
    claimed_amount:     '',
  });

  // Adjuster-editable fields
  const [adjusterFields, setAdjusterFields] = useState({
    repair_complexity:    'Medium',
    parts_availability:   'Available',
    labor_hours_estimate: 20,
  });



  // Populate from props whenever they change
  useEffect(() => {
    const currentYear    = new Date().getFullYear();
    const manufactureYear = vehicle?.manufacture_year ?? currentYear;

    setAutoFields({
      vehicle_age_years: currentYear - manufactureYear,
      vehicle_value:     vehicle?.market_value  ?? claim?.vehicle_value   ?? '',
      incident_type:     claim?.claim_type      ?? '',
      incident_severity: claim?.severity        ?? '',
      claimed_amount:    claim?.claimed_amount  ?? '',
    });

    // Reset results whenever the claim changes
    setResult(null);
    setError('');
  }, [claim?.id, vehicle?.id]);

  // ── Currency helpers ──────────────────────────────────────────────────────
  const sym = currency === 'USD' ? '$' : 'ZWG ';

  const fmtUSD = (usdVal) => {
    if (usdVal === '' || usdVal == null) return '—';
    const n = Number(usdVal);
    if (isNaN(n)) return '—';
    const displayed = currency === 'ZWG' ? n * exchangeRate : n;
    return `${sym}${displayed.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  };

  const getAccuracy = (claimedUSD, estimatedUSD) => {
    const c = Number(claimedUSD);
    const e = Number(estimatedUSD);
    if (!c) return { level: 'N/A', color: '#7F8C8D', bg: '#F3F4F6' };
    const pct = (Math.abs(c - e) / c) * 100;
    if (pct <= 10) return { level: 'High Accuracy',    color: '#10B981', bg: '#D1FAE5' };
    if (pct <= 25) return { level: 'Medium Accuracy',  color: '#F59E0B', bg: '#FEF3C7' };
    return               { level: 'Low Accuracy',      color: '#EF4444', bg: '#FEE2E2' };
  };

  const claimedUSD   = Number(autoFields.claimed_amount) || 0;
  const estimatedUSD = result ? Number(result.estimated_amount) : 0;
  const accuracy     = getAccuracy(claimedUSD, estimatedUSD);
  const diffUSD      = Math.abs(claimedUSD - estimatedUSD);
  const varianceThreshold = settings?.threshold_variance_warning;
  const isLargeDiff = diffUSD > claimedUSD * varianceThreshold;

  // ── Submit ────────────────────────────────────────────────────────────────
  const handleSubmit = async () => {
    setIsLoading(true);
    setError('');
    setResult(null);

    const formData = {
      vehicle_age_years:    autoFields.vehicle_age_years !== '' ? Number(autoFields.vehicle_age_years) : 0,
      vehicle_value:        autoFields.vehicle_value     !== '' ? Number(autoFields.vehicle_value)     : 0,
      incident_type:        autoFields.incident_type,
      incident_severity:    autoFields.incident_severity,
      claimed_amount:       autoFields.claimed_amount    !== '' ? Number(autoFields.claimed_amount)    : 0,
      repair_complexity:    adjusterFields.repair_complexity,
      parts_availability:   adjusterFields.parts_availability,
      labor_hours_estimate: Number(adjusterFields.labor_hours_estimate),
    };

    try {
      const data = await api.estimateClaimDirect(formData);
      setResult(data);
    } catch (err) {
      console.error('Claim estimation failed:', err);
      setError('Failed to run estimate: ' + (err.message || 'Unknown error'));
    } finally {
      setIsLoading(false);
    }
  };

  const readOnlyClass =
    'w-full px-3 py-2 rounded-lg border text-sm font-medium bg-gray-50 text-gray-500 cursor-not-allowed select-none';
  const editableClass =
    'w-full px-3 py-2 rounded-lg border text-sm focus:outline-none focus:ring-2 focus:ring-orange-300 transition-shadow';

  return (
    <div className="space-y-5">

      {/* ── Currency Toggle ─────────────────────────────────────────────── */}
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-bold" style={{ color: '#2C3E50' }}>AI-powered loss estimation</p>
          <p className="text-xs mt-0.5" style={{ color: '#7F8C8D' }}>
            Claim details are pre-loaded from this record — adjust assessor fields below and run.
          </p>
        </div>
        <div className="flex items-center gap-1 rounded-xl p-1 shadow-inner"
             style={{ backgroundColor: '#E9ECEF', border: '1px solid #DEE2E6' }}>
          <ArrowLeftRight className="w-3.5 h-3.5 mx-1.5" style={{ color: '#7F8C8D' }} />
          {['USD', 'ZWG'].map((c) => (
            <button
              key={c}
              onClick={() => setCurrency(c)}
              className="px-4 py-1.5 rounded-lg text-sm font-semibold transition-all duration-200"
              style={
                currency === c
                  ? { backgroundColor: '#FF6B4A', color: '#fff', boxShadow: '0 1px 4px rgba(255,107,74,0.35)' }
                  : { color: '#7F8C8D', backgroundColor: 'transparent' }
              }
            >
              {c}
            </button>
          ))}
        </div>
      </div>

      {/* ── Error Banner ─────────────────────────────────────────────────── */}
      {error && (
        <div className="flex items-start gap-3 p-4 rounded-xl"
             style={{ backgroundColor: '#FEE2E2', color: '#DC2626', border: '1px solid #FECACA' }}>
          <AlertCircle className="w-4 h-4 mt-0.5 flex-shrink-0" />
          <span className="text-sm">{error}</span>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">

        {/* ── Left 2/3: Form ───────────────────────────────────────────── */}
        <div className="lg:col-span-2 space-y-5">

          {/* Claim Details — read-only */}
          <div className="bg-white rounded-2xl shadow-sm p-5" style={{ border: '1px solid #E9ECEF' }}>
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 rounded-xl flex items-center justify-center"
                   style={{ backgroundColor: '#EBF5FF' }}>
                <Car className="w-5 h-5" style={{ color: '#3B82F6' }} />
              </div>
              <div className="flex-1">
                <h3 className="font-bold text-base" style={{ color: '#2C3E50' }}>Claim Details</h3>
                <p className="text-xs" style={{ color: '#7F8C8D' }}>Auto-populated from {claim?.claim_number}</p>
              </div>
              <div className="flex items-center gap-1 px-2 py-1 rounded-full text-xs"
                   style={{ backgroundColor: '#F3F4F6', color: '#7F8C8D' }}>
                <Lock className="w-3 h-3" /> Locked
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold mb-1.5 uppercase tracking-wide" style={{ color: '#7F8C8D' }}>
                  Vehicle Age (years)
                </label>
                <div className="relative">
                  <input type="text" readOnly
                         value={autoFields.vehicle_age_years !== '' ? autoFields.vehicle_age_years : '—'}
                         className={readOnlyClass} style={{ borderColor: '#E9ECEF' }} />
                  <Lock className="absolute right-3 top-1/2 -translate-y-1/2 w-3 h-3" style={{ color: '#CBD5E1' }} />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold mb-1.5 uppercase tracking-wide" style={{ color: '#7F8C8D' }}>
                  Vehicle Value ({currency})
                </label>
                <div className="relative">
                  <input type="text" readOnly value={fmtUSD(autoFields.vehicle_value)}
                         className={readOnlyClass} style={{ borderColor: '#E9ECEF' }} />
                  <Lock className="absolute right-3 top-1/2 -translate-y-1/2 w-3 h-3" style={{ color: '#CBD5E1' }} />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold mb-1.5 uppercase tracking-wide" style={{ color: '#7F8C8D' }}>
                  Incident Type
                </label>
                <div className="relative">
                  <input type="text" readOnly value={autoFields.incident_type || '—'}
                         className={readOnlyClass} style={{ borderColor: '#E9ECEF' }} />
                  <Lock className="absolute right-3 top-1/2 -translate-y-1/2 w-3 h-3" style={{ color: '#CBD5E1' }} />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold mb-1.5 uppercase tracking-wide" style={{ color: '#7F8C8D' }}>
                  Incident Severity
                </label>
                <div className="relative">
                  <input type="text" readOnly value={autoFields.incident_severity || '—'}
                         className={readOnlyClass} style={{ borderColor: '#E9ECEF' }} />
                  <Lock className="absolute right-3 top-1/2 -translate-y-1/2 w-3 h-3" style={{ color: '#CBD5E1' }} />
                </div>
              </div>

              <div className="col-span-2">
                <label className="block text-xs font-semibold mb-1.5 uppercase tracking-wide" style={{ color: '#7F8C8D' }}>
                  Claimed Amount ({currency})
                </label>
                <div className="relative">
                  <input type="text" readOnly value={fmtUSD(autoFields.claimed_amount)}
                         className={readOnlyClass + ' text-base font-bold'}
                         style={{ borderColor: '#E9ECEF', color: '#2C3E50' }} />
                  <Lock className="absolute right-3 top-1/2 -translate-y-1/2 w-3 h-3" style={{ color: '#CBD5E1' }} />
                </div>
              </div>
            </div>
          </div>

          {/* Adjuster Inputs */}
          <div className="bg-white rounded-2xl shadow-sm p-5" style={{ border: '1px solid #E9ECEF' }}>
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 rounded-xl flex items-center justify-center"
                   style={{ backgroundColor: '#F0FDF4' }}>
                <Wrench className="w-5 h-5" style={{ color: '#10B981' }} />
              </div>
              <div>
                <h3 className="font-bold text-base" style={{ color: '#2C3E50' }}>Adjuster Assessment</h3>
                <p className="text-xs" style={{ color: '#7F8C8D' }}>Editable — filled in by the loss assessor</p>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold mb-1.5 uppercase tracking-wide" style={{ color: '#2C3E50' }}>
                  Repair Complexity
                </label>
                <div className="relative">
                  <select
                    value={adjusterFields.repair_complexity}
                    onChange={(e) => setAdjusterFields({ ...adjusterFields, repair_complexity: e.target.value })}
                    className={editableClass + ' appearance-none pr-8'}
                    style={{ borderColor: '#DEE2E6', color: '#2C3E50' }}>
                    <option value="Low">Low</option>
                    <option value="Medium">Medium</option>
                    <option value="High">High</option>
                  </select>
                  <ChevronDown className="absolute right-2.5 top-1/2 -translate-y-1/2 w-4 h-4 pointer-events-none"
                               style={{ color: '#7F8C8D' }} />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold mb-1.5 uppercase tracking-wide" style={{ color: '#2C3E50' }}>
                  Parts Availability
                </label>
                <div className="relative">
                  <select
                    value={adjusterFields.parts_availability}
                    onChange={(e) => setAdjusterFields({ ...adjusterFields, parts_availability: e.target.value })}
                    className={editableClass + ' appearance-none pr-8'}
                    style={{ borderColor: '#DEE2E6', color: '#2C3E50' }}>
                    <option value="Available">Available</option>
                    <option value="Limited">Limited</option>
                    <option value="Rare">Rare</option>
                  </select>
                  <ChevronDown className="absolute right-2.5 top-1/2 -translate-y-1/2 w-4 h-4 pointer-events-none"
                               style={{ color: '#7F8C8D' }} />
                </div>
              </div>

              <div className="col-span-2">
                <label className="block text-xs font-semibold mb-1.5 uppercase tracking-wide" style={{ color: '#2C3E50' }}>
                  Labor Hours Estimate
                </label>
                <input
                  type="number"
                  min="0"
                  value={adjusterFields.labor_hours_estimate}
                  onChange={(e) => setAdjusterFields({ ...adjusterFields, labor_hours_estimate: parseInt(e.target.value) || 0 })}
                  className={editableClass}
                  style={{ borderColor: '#DEE2E6', color: '#2C3E50' }}
                  placeholder="e.g. 20"
                />
                <p className="text-xs mt-1" style={{ color: '#7F8C8D' }}>
                  Estimated @ ${settings?.labor_rate_per_hour} / hr · affects final cost
                </p>
              </div>
            </div>

            <button
              onClick={handleSubmit}
              disabled={isLoading}
              className="mt-5 w-full py-3 px-4 rounded-xl text-white font-bold text-sm transition-all duration-200 flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
              style={{ backgroundColor: '#FF6B4A', boxShadow: '0 4px 14px rgba(255,107,74,0.35)' }}
              onMouseEnter={(e) => { if (!isLoading) e.currentTarget.style.backgroundColor = '#E55A3A'; }}
              onMouseLeave={(e) => { e.currentTarget.style.backgroundColor = '#FF6B4A'; }}>
              {isLoading
                ? <><Loader2 className="w-4 h-4 animate-spin" /> Running ML Estimate…</>
                : <><Calculator className="w-4 h-4" /> Run Loss Assessment</>}
            </button>
          </div>
        </div>

        {/* ── Right 1/3: Results ────────────────────────────────────────── */}
        <div className="lg:col-span-1">
          <div className="bg-white rounded-2xl shadow-sm p-5 sticky top-6"
               style={{ border: '1px solid #E9ECEF' }}>
            <div className="flex items-center gap-3 mb-5">
              <div className="w-10 h-10 rounded-xl flex items-center justify-center"
                   style={{ backgroundColor: '#D1FAE5' }}>
                <TrendingUp className="w-5 h-5" style={{ color: '#10B981' }} />
              </div>
              <div>
                <h3 className="font-bold text-base" style={{ color: '#2C3E50' }}>ML Estimate</h3>
                <p className="text-xs" style={{ color: '#7F8C8D' }}>AI-generated loss assessment</p>
              </div>
            </div>

            {!result ? (
              <div className="text-center py-12">
                <div className="w-16 h-16 rounded-2xl mx-auto mb-4 flex items-center justify-center"
                     style={{ backgroundColor: '#F8F9FA', border: '2px dashed #DEE2E6' }}>
                  <Calculator className="w-8 h-8" style={{ color: '#DEE2E6' }} />
                </div>
                <p className="text-sm font-medium" style={{ color: '#7F8C8D' }}>
                  Adjust assessor details and click "Run Loss Assessment"
                </p>
              </div>
            ) : (
              <div className="space-y-4">

                {/* Estimated Amount */}
                <div className="p-5 rounded-xl text-center"
                     style={{ backgroundColor: '#F8F9FA', border: '1px solid #E9ECEF' }}>
                  <p className="text-xs font-semibold uppercase tracking-widest mb-1" style={{ color: '#7F8C8D' }}>
                    Estimated Loss
                  </p>
                  <p className="text-4xl font-extrabold mb-3 tracking-tight" style={{ color: '#2C3E50' }}>
                    {fmtUSD(result.estimated_amount)}
                  </p>
                  <span className="inline-block px-3 py-1 rounded-full text-xs font-bold"
                        style={{ backgroundColor: accuracy.bg, color: accuracy.color }}>
                    {accuracy.level}
                  </span>
                </div>

                {/* Confidence Bar */}
                {result.confidence_score !== undefined && (
                  <div>
                    <div className="flex justify-between text-xs mb-1.5" style={{ color: '#7F8C8D' }}>
                      <span className="font-semibold uppercase tracking-wide">Model Confidence</span>
                      <span className="font-bold" style={{ color: '#2C3E50' }}>
                        {Math.round(result.confidence_score * 100)}%
                      </span>
                    </div>
                    <div className="h-2 rounded-full overflow-hidden" style={{ backgroundColor: '#E9ECEF' }}>
                      <div className="h-full rounded-full transition-all duration-700"
                           style={{
                             width: `${Math.round(result.confidence_score * 100)}%`,
                             backgroundColor: result.confidence_score >= 0.8 ? '#10B981'
                               : result.confidence_score >= 0.6 ? '#F59E0B' : '#EF4444',
                           }} />
                    </div>
                  </div>
                )}

                {/* Comparison */}
                <div>
                  <p className="text-xs font-semibold uppercase tracking-wide mb-2" style={{ color: '#7F8C8D' }}>
                    Comparison
                  </p>
                  <div className="space-y-2">
                    {[
                      { label: 'Claimed Amount', value: fmtUSD(claimedUSD) },
                      { label: 'ML Estimate',    value: fmtUSD(estimatedUSD) },
                      { label: 'Variance',        value: fmtUSD(diffUSD), valueColor: isLargeDiff ? '#EF4444' : '#10B981' },
                    ].map(({ label, value, valueColor }) => (
                      <div key={label} className="flex items-center justify-between px-3 py-2 rounded-lg"
                           style={{ backgroundColor: '#F8F9FA' }}>
                        <span className="text-xs" style={{ color: '#7F8C8D' }}>{label}</span>
                        <span className="text-sm font-bold" style={{ color: valueColor || '#2C3E50' }}>{value}</span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Cost Breakdown */}
                {result.cost_breakdown && (
                  <div>
                    <p className="text-xs font-semibold uppercase tracking-wide mb-2" style={{ color: '#7F8C8D' }}>
                      Cost Breakdown
                    </p>
                    <div className="space-y-1.5">
                      {Object.entries(result.cost_breakdown).map(([key, val]) => (
                        <div key={key} className="flex items-center justify-between px-3 py-2 rounded-lg"
                             style={{ backgroundColor: '#F8F9FA' }}>
                          <span className="text-xs capitalize" style={{ color: '#7F8C8D' }}>
                            {key.replace(/_/g, ' ')}
                          </span>
                          <span className="text-xs font-semibold" style={{ color: '#2C3E50' }}>
                            {fmtUSD(val)}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Recommendation */}
                <div className="p-4 rounded-xl"
                     style={{
                       backgroundColor: isLargeDiff ? '#FEF3C7' : '#EBF5FF',
                       border: `1px solid ${isLargeDiff ? '#FDE68A' : '#BFDBFE'}`,
                     }}>
                  <p className="text-xs font-bold mb-1 uppercase tracking-wide"
                     style={{ color: isLargeDiff ? '#92400E' : '#1E3A8A' }}>
                    {result.recommendation ? result.recommendation.replace(/_/g, ' ') : 'Recommendation'}
                  </p>
                  <p className="text-xs leading-relaxed" style={{ color: isLargeDiff ? '#78350F' : '#1E40AF' }}>
                    {isLargeDiff
                      ? 'Significant variance detected. Recommend further investigation and senior adjuster review before approval.'
                      : 'Claimed amount is within acceptable range of AI estimate. Proceed with standard approval workflow.'}
                  </p>
                </div>

                {/* Priority Badge */}
                {result.priority && (
                  <div className="flex items-center justify-between">
                    <span className="text-xs" style={{ color: '#7F8C8D' }}>Processing Priority</span>
                    <span className="text-xs font-bold px-3 py-1 rounded-full"
                          style={{
                            backgroundColor: result.priority === 'URGENT' ? '#FEE2E2'
                              : result.priority === 'HIGH'   ? '#FEF3C7'
                              : result.priority === 'MEDIUM' ? '#EBF5FF' : '#D1FAE5',
                            color: result.priority === 'URGENT' ? '#DC2626'
                              : result.priority === 'HIGH'   ? '#D97706'
                              : result.priority === 'MEDIUM' ? '#2563EB' : '#059669',
                          }}>
                      {result.priority}
                    </span>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}