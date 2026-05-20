import { useState, useEffect, useRef } from 'react';
import { Save, Loader2, Info } from 'lucide-react';
import { api } from '../../services/api';

const HINTS = {
  base_premium_percentage:   'Fraction of vehicle market value charged as the starting premium (e.g. 0.05 = 5%).',
  minimum_premium:           'Absolute floor premium — no policy can be priced below this amount regardless of discounts.',
  labor_rate_per_hour:       'Hourly repair labour cost used when estimating claims that include a repair component.',
  addon_roadside_assistance: 'Flat fee added to a premium when the policyholder opts in to roadside assistance cover.',
  addon_rental_coverage:     'Flat fee added to a premium for rental-car cover while the insured vehicle is being repaired.',
  addon_glass_coverage:      'Flat fee added for glass and windscreen replacement cover.',
  surcharge_young_driver:    'Extra premium multiplier for drivers under 25 years old (e.g. 0.15 = +15% on base).',
  surcharge_senior_driver:   'Extra premium multiplier for drivers over 65 years old (e.g. 0.10 = +10% on base).',
  surcharge_poor_credit:     "Extra premium multiplier when a policyholder's credit score is below 600.",
  discount_excellent_credit: 'Premium reduction fraction for policyholders with a credit score of 750+ (e.g. 0.10 = −10%).',
  discount_anti_theft:       'Premium reduction fraction when the insured vehicle has an anti-theft device installed.',
  threshold_auto_approve:    'Claims at or below this dollar amount are approved automatically without adjuster review.',
  threshold_manual_review:   'Claims above this amount are escalated to a human adjuster for manual review.',
  threshold_fraud_reject:    'ML fraud score (0–1) at which a claim is automatically rejected. Scores at or above this trigger rejection.',
  threshold_variance_warning:'ML fraud score (0–1) at which a claim is flagged as elevated risk and sent for closer review.',
  sev_trivial_mult:          'Fraction of vehicle value used as the starting claim estimate for trivial damage (e.g. 0.05 = 5% of value).',
  sev_minor_mult:            'Fraction of vehicle value for minor damage claims (e.g. 0.15 = 15%).',
  sev_moderate_mult:         'Fraction of vehicle value for moderate damage claims (e.g. 0.30 = 30%).',
  sev_major_mult:            'Fraction of vehicle value for major damage claims (e.g. 0.35 = 35%).',
  sev_total_mult:            'Fraction of vehicle value for total-loss claims — typically 1.0 (100% of value).',
  ratio_vehicle_damage:      'Portion of an estimated claim total attributed to vehicle repair. All four ratios must sum to 1.0.',
  ratio_medical_expenses:    'Portion attributed to medical expenses. Part of the four-way cost split.',
  ratio_legal_fees:          'Portion attributed to legal fees. Part of the four-way cost split.',
  ratio_other_costs:         'Portion attributed to miscellaneous costs. Together the four ratios must equal 1.0.',
  default_currency:          'Currency applied automatically when creating new policies and quotes.',
  zwg_usd_exchange_rate:     'Exchange rate used for on-screen currency conversion (e.g. 13.56 means 1 USD = 13.56 ZWG). Does not affect stored amounts.',
  allow_multi_currency:      'Allow users to select ZWG when creating policies. When off, USD is the only option.',
};

function Tooltip({ hint }) {
  const [visible, setVisible] = useState(false);
  return (
    <span
      className="relative inline-flex items-center"
      onMouseEnter={() => setVisible(true)}
      onMouseLeave={() => setVisible(false)}
    >
      <Info className="w-3 h-3 cursor-help flex-shrink-0" style={{ color: '#C4C9D4' }} />
      {visible && (
        <span
          className="absolute z-50 left-5 top-1/2 -translate-y-1/2 w-52 rounded-lg px-3 py-2 text-xs leading-relaxed shadow-xl pointer-events-none"
          style={{ backgroundColor: '#1E293B', color: '#F1F5F9', border: '1px solid #334155' }}
        >
          {hint}
          <span
            className="absolute -left-1.5 top-1/2 -translate-y-1/2 w-2.5 h-2.5 rotate-45"
            style={{ backgroundColor: '#1E293B', border: '1px solid #334155', borderRight: 'none', borderTop: 'none' }}
          />
        </span>
      )}
    </span>
  );
}

const Field = ({ label, fieldKey, children }) => (
  <div>
    <div className="flex items-center gap-1 mb-1">
      <label className="block text-xs font-medium" style={{ color: '#4B5563' }}>
        {label}
      </label>
      {HINTS[fieldKey] && <Tooltip hint={HINTS[fieldKey]} />}
    </div>
    {children}
  </div>
);

const NumInput = ({ value, onChange, step = '0.01', min = '0', max }) => (
  <input
    type="number"
    step={step}
    min={min}
    max={max}
    value={value || ''}
    onChange={(e) => onChange(e.target.value)}
    className="w-full px-2.5 py-1.5 rounded border text-sm focus:outline-none focus:ring-1"
    style={{ borderColor: '#E0E0E0' }}
  />
);

const SectionHeader = ({ title, color, badge }) => (
  <div className="col-span-4 flex items-center justify-between pt-4 pb-1 border-b" style={{ borderColor: '#F0F0F0' }}>
    <h3 className="text-sm font-semibold uppercase tracking-wide" style={{ color }}>
      {title}
    </h3>
    {badge}
  </div>
);

export default function GlobalPricingSettingsTab({ companyProfile }) {
  const [original, setOriginal] = useState(null);
  const [draft, setDraft] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    const fetchSettings = async () => {
      try {
        const data = await api.getGlobalPricingSettings();
        setOriginal(data);
        setDraft(data);
      } catch (err) {
        console.error('Could not load settings:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchSettings();
  }, []);

  const settingsChanged = original && draft
    ? JSON.stringify(original) !== JSON.stringify(draft)
    : false;

  const handleReset = () => setDraft({ ...original });

  const handleSave = async () => {
    setSaving(true);
    try {
      const data = await api.updateGlobalPricingSettings(draft);
      setOriginal(data);
      setDraft(data);
    } catch (err) {
      console.error('Failed to save settings:', err);
    } finally {
      setSaving(false);
    }
  };

  const handleChange = (field, value) => setDraft({ ...draft, [field]: value });

  const ratioSum = draft ? (
    (parseFloat(draft.ratio_vehicle_damage) || 0) +
    (parseFloat(draft.ratio_medical_expenses) || 0) +
    (parseFloat(draft.ratio_legal_fees) || 0) +
    (parseFloat(draft.ratio_other_costs) || 0)
  ) : 0;
  const ratioValid = Math.abs(ratioSum - 1) < 0.005;

  if (loading) {
    return (
      <div className="text-center py-12">
        <Loader2 className="w-6 h-6 animate-spin mx-auto" style={{ color: companyProfile.primary_color }} />
        <p className="mt-3 text-sm" style={{ color: '#7F8C8D' }}>Loading pricing settings...</p>
      </div>
    );
  }

  if (!draft) return null;

  const col = companyProfile.secondary_color;
  const f = (field) => ({
    value: draft[field],
    onChange: (v) => handleChange(field, v),
  });

  return (
    <div>
      {/* Header */}
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-base font-semibold" style={{ color: col }}>
          Global Pricing Settings
        </h2>
        <div className="flex space-x-2">
          {settingsChanged && (
            <button
              onClick={handleReset}
              className="px-3 py-1.5 rounded text-sm font-medium"
              style={{ backgroundColor: '#F3F4F6', color: '#6B7280' }}
            >
              Reset
            </button>
          )}
          <button
            onClick={handleSave}
            disabled={!settingsChanged || saving}
            className="px-4 py-1.5 rounded text-sm font-medium flex items-center"
            style={{
              backgroundColor: settingsChanged && !saving ? companyProfile.primary_color : '#E5E7EB',
              color: 'white',
              opacity: settingsChanged && !saving ? 1 : 0.6,
              cursor: settingsChanged && !saving ? 'pointer' : 'not-allowed',
            }}
          >
            {saving ? <Loader2 className="w-3.5 h-3.5 mr-1.5 animate-spin" /> : <Save className="w-3.5 h-3.5 mr-1.5" />}
            Save Changes
          </button>
        </div>
      </div>

      <div className="grid grid-cols-4 gap-x-4 gap-y-3">

        {/* Base Rates */}
        <SectionHeader title="Base Rates" color={col} />

        <Field label="Base Premium %" fieldKey="base_premium_percentage">
          <NumInput step="0.0001" {...f('base_premium_percentage')} />
        </Field>
        <Field label="Minimum Premium ($)" fieldKey="minimum_premium">
          <NumInput {...f('minimum_premium')} />
        </Field>
        <Field label="Labor Rate / Hour ($)" fieldKey="labor_rate_per_hour">
          <NumInput {...f('labor_rate_per_hour')} />
        </Field>
        <div /> {/* spacer */}

        {/* Add-on Coverage Fees */}
        <SectionHeader title="Add-on Coverage Fees" color={col} />

        <Field label="Roadside Assistance ($)" fieldKey="addon_roadside_assistance">
          <NumInput {...f('addon_roadside_assistance')} />
        </Field>
        <Field label="Rental Car Coverage ($)" fieldKey="addon_rental_coverage">
          <NumInput {...f('addon_rental_coverage')} />
        </Field>
        <Field label="Glass / Windscreen ($)" fieldKey="addon_glass_coverage">
          <NumInput {...f('addon_glass_coverage')} />
        </Field>
        <div />

        {/* Risk Surcharges */}
        <SectionHeader title="Risk Surcharges" color={col} />

        <Field label="Young Driver" fieldKey="surcharge_young_driver">
          <NumInput step="0.0001" {...f('surcharge_young_driver')} />
        </Field>
        <Field label="Senior Driver" fieldKey="surcharge_senior_driver">
          <NumInput step="0.0001" {...f('surcharge_senior_driver')} />
        </Field>
        <Field label="Poor Credit" fieldKey="surcharge_poor_credit">
          <NumInput step="0.0001" {...f('surcharge_poor_credit')} />
        </Field>
        <div />

        {/* Discounts */}
        <SectionHeader title="Discounts" color={col} />

        <Field label="Excellent Credit" fieldKey="discount_excellent_credit">
          <NumInput step="0.0001" {...f('discount_excellent_credit')} />
        </Field>
        <Field label="Anti-Theft Device" fieldKey="discount_anti_theft">
          <NumInput step="0.0001" {...f('discount_anti_theft')} />
        </Field>
        <div />
        <div />

        {/* Workflow Thresholds */}
        <SectionHeader title="Workflow Thresholds" color={col} />

        <Field label="Auto-Approve Limit ($)" fieldKey="threshold_auto_approve">
          <NumInput {...f('threshold_auto_approve')} />
        </Field>
        <Field label="Manual Review Limit ($)" fieldKey="threshold_manual_review">
          <NumInput {...f('threshold_manual_review')} />
        </Field>
        <Field label="Fraud Reject" fieldKey="threshold_fraud_reject">
          <NumInput step="0.01" min="0" max="1" {...f('threshold_fraud_reject')} />
        </Field>
        <Field label="Variance Warning" fieldKey="threshold_variance_warning">
          <NumInput step="0.01" min="0" max="1" {...f('threshold_variance_warning')} />
        </Field>

        {/* Severity Multipliers */}
        <SectionHeader title="Severity Multipliers" color={col} />

        <Field label="Trivial" fieldKey="sev_trivial_mult">
          <NumInput step="0.0001" {...f('sev_trivial_mult')} />
        </Field>
        <Field label="Minor" fieldKey="sev_minor_mult">
          <NumInput step="0.0001" {...f('sev_minor_mult')} />
        </Field>
        <Field label="Moderate" fieldKey="sev_moderate_mult">
          <NumInput step="0.0001" {...f('sev_moderate_mult')} />
        </Field>
        <Field label="Major" fieldKey="sev_major_mult">
          <NumInput step="0.0001" {...f('sev_major_mult')} />
        </Field>

        <Field label="Total Loss" fieldKey="sev_total_mult">
          <NumInput step="0.0001" {...f('sev_total_mult')} />
        </Field>
        <div /><div /><div />

        {/* Cost-Breakdown Ratios */}
        <SectionHeader
          title="Cost-Breakdown Ratios"
          color={col}
          badge={
            ratioValid
              ? <span className="text-xs px-2 py-0.5 rounded-full font-medium" style={{ backgroundColor: '#ECFDF5', color: '#10B981' }}>Valid ✓</span>
              : <span className="text-xs px-2 py-0.5 rounded-full font-medium" style={{ backgroundColor: '#FEF2F2', color: '#EF4444' }}>Must sum to 1.0 (now {ratioSum.toFixed(3)})</span>
          }
        />

        <Field label="Vehicle Damage" fieldKey="ratio_vehicle_damage">
          <NumInput step="0.0001" min="0" max="1" {...f('ratio_vehicle_damage')} />
        </Field>
        <Field label="Medical Expenses" fieldKey="ratio_medical_expenses">
          <NumInput step="0.0001" min="0" max="1" {...f('ratio_medical_expenses')} />
        </Field>
        <Field label="Legal Fees" fieldKey="ratio_legal_fees">
          <NumInput step="0.0001" min="0" max="1" {...f('ratio_legal_fees')} />
        </Field>
        <Field label="Other Costs" fieldKey="ratio_other_costs">
          <NumInput step="0.0001" min="0" max="1" {...f('ratio_other_costs')} />
        </Field>

        {/* Currency Settings */}
        <SectionHeader title="Currency Settings" color={col} />

        <Field label="Default Currency" fieldKey="default_currency">
          <select
            value={draft.default_currency || 'USD'}
            onChange={(e) => handleChange('default_currency', e.target.value)}
            className="w-full px-2.5 py-1.5 rounded border text-sm focus:outline-none focus:ring-1"
            style={{ borderColor: '#E0E0E0' }}
          >
            <option value="USD">USD — US Dollar</option>
            <option value="ZWG">ZWG — Zimbabwe Gold</option>
          </select>
        </Field>

        <Field label="ZWG per 1 USD" fieldKey="zwg_usd_exchange_rate">
          <NumInput step="0.01" {...f('zwg_usd_exchange_rate')} />
        </Field>

        <Field label="Allow Multi-Currency" fieldKey="allow_multi_currency">
          <div className="flex items-center h-[34px]">
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={draft.allow_multi_currency || false}
                onChange={(e) => handleChange('allow_multi_currency', e.target.checked)}
                className="sr-only peer"
              />
              <div className="w-9 h-5 bg-gray-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-blue-600" />
            </label>
          </div>
        </Field>
        <div />

      </div>
    </div>
  );
}