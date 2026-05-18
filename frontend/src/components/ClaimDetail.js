import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { api } from '../services/api';
import Sidebar from './Sidebar';
import EmbeddedLossAssessor from './EmbeddedLossAssessor';
import { useNotification } from './notifications/useNotification';
import { useCurrencyFormatter } from '../utils/currencyFormatter';
import {
  ArrowLeft, AlertTriangle, CheckCircle, XCircle, FileText, Shield,
  User, Car, DollarSign, Calendar, MapPin, Clock, Activity,
  ChevronRight, Loader2, CreditCard, Phone, Mail, Hash,
  TrendingUp, ShieldCheck, Star, Award, Navigation, Lock, Gauge,
  Zap, Wrench, Download, ExternalLink, X,
  ArrowUp, ArrowDown, Minus, Calculator, BookOpen, Fingerprint
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

const creditPct   = (score) => Math.round(((score - 300) / (850 - 300)) * 100);

// ── Deterministic RNG & Plain English Engine ─────────────────────────────────

// Seeded random number generator
function createSeededRNG(seedStr) {
  let hash = 0;
  for (let i = 0; i < seedStr.length; i++) {
    hash = Math.imul(31, hash) + seedStr.charCodeAt(i) | 0;
  }
  return function() {
    hash = Math.imul(hash ^ (hash >>> 15), 1358650055);
    return ((hash ^ (hash >>> 15)) >>> 0) / 4294967296;
  };
}

// Select a random item from an array using the seeded RNG
function pick(array, rng) {
  return array[Math.floor(rng() * array.length)];
}

// Derive real-world values from claim data
function buildActualValues(claim, policyholder, vehicle, policy) {
  const incidentDate   = claim?.incident_date  ? new Date(claim.incident_date)  : null;
  const submittedDate  = claim?.submitted_date ? new Date(claim.submitted_date) : null;
  const policyStart    = policy?.start_date    ? new Date(policy.start_date)    : null;
  const currentYear    = new Date().getFullYear();

  const daysSinceStart = incidentDate && policyStart
    ? Math.round((incidentDate - policyStart) / 86400000)
    : null;

  const delayHours = incidentDate && submittedDate
    ? Math.round((submittedDate - incidentDate) / 3600000)
    : null;

  const claimed  = parseFloat(claim?.claimed_amount  || 0);
  const coverage = parseFloat(policy?.coverage_amount || 1);

  return {
    days_since_policy_start:    daysSinceStart,
    submission_delay_hours:     delayHours,
    claimed_amount:             claimed,
    claim_to_coverage_ratio:    coverage > 0 ? claimed / coverage : 0,
    vehicle_age:                vehicle?.manufacture_year ? currentYear - vehicle.manufacture_year : null,
    vehicle_value:              parseFloat(vehicle?.market_value || 0),
    has_anti_theft:             vehicle?.has_anti_theft,
    is_modified:                vehicle?.is_modified,
    number_of_vehicles_involved: parseInt(claim?.number_of_vehicles_involved || 1),
    policyholder_age:           policyholder?.age,
    credit_score:               policyholder?.credit_score,
    years_with_company:         policyholder?.years_with_company,
    incident_hour:              incidentDate ? incidentDate.getHours()    : null,
    incident_day_of_week:       incidentDate ? incidentDate.getDay()      : null,
    incident_month:             incidentDate ? incidentDate.getMonth() + 1 : null,
    severity:                   claim?.severity,
    claim_type:                 claim?.claim_type,
  };
}

// Map feature + direction + real value → dynamic plain English
function getNarrative(featureName, raises, v, rng, currency, fmtMoney) {
  const fmt = (n) => fmtMoney ? fmtMoney(n, currency) : `$${parseFloat(n || 0).toLocaleString('en-US', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}`;

  const DAYS  = ['Sunday','Monday','Tuesday','Wednesday','Thursday','Friday','Saturday'];
  const MONTHS = ['January','February','March','April','May','June','July','August','September','October','November','December'];
  const SEVERITY_LABELS = { MINOR:'minor', MODERATE:'moderate', MAJOR:'major', TOTAL_LOSS:'total loss' };
  const TYPE_LABELS = { ACCIDENT:'Accident', THEFT:'Theft', VANDALISM:'Vandalism', NATURAL_DISASTER:'Natural Disaster', FIRE:'Fire', OTHER:'Other' };

  const map = {
    days_since_policy_start: () => {
      const d = v.days_since_policy_start;
      if (d === null) return null;
      if (raises) {
        if (d < 14) return {
          explanation: `${pick([
            `This policy was just ${d} days old when the incident occurred.`,
            `A mere ${d} days passed between the policy start date and this incident.`,
            `The incident happened only ${d} days into the policy's lifespan.`
          ], rng)} ${pick([
            `Taking out coverage and making a claim almost immediately is a classic warning sign that requires review.`,
            `Claims filed this quickly automatically trigger closer scrutiny to ensure the policy wasn't purchased specifically for this incident.`,
            `Such a tight timeline between inception and claiming is a statistical indicator that warrants a closer look.`
          ], rng)}`,
        };
        if (d < 60) return {
          explanation: `The policy had been active for only ${d} days when the incident happened. Claims in the first two months of a policy receive additional scrutiny because this is a higher-risk period.`,
        };
        return {
          explanation: `The policy was ${d} days old at the time of the incident. The timing contributed a small amount to the overall risk score.`,
        };
      }
      const months = Math.round(d / 30);
      return {
        explanation: `${pick([
          `This policyholder held their policy for ${months} months before making a claim.`,
          `The account has been active and claim-free for ${months} months.`,
        ], rng)} Waiting this long before claiming is a strong indicator of legitimacy — fraud is far more common with brand-new policies.`,
      };
    },

    claimed_amount: () => {
      const amt = v.claimed_amount;
      if (raises) return {
        explanation: `${pick([
          `The total claim is requesting ${fmt(amt)}.`,
          `This claim is seeking a payout of ${fmt(amt)}.`,
        ], rng)} Larger claim amounts receive more scrutiny because they represent a greater potential financial impact. This doesn't mean the claim is false — just that the figure warrants careful review.`,
      };
      return {
        explanation: `The claimed amount of ${fmt(amt)} is within a normal, expected range for this type and severity of incident. The figure did not raise any red flags.`,
      };
    },

    severity_encoded: () => {
      const sev = SEVERITY_LABELS[v.severity] || v.severity;
      if (raises) return {
        explanation: `The reported damage level (${sev}) shows some inconsistency when compared to other details of the claim, such as the amount being claimed or the type of incident. Overstating damage severity is a common way to inflate a claim.`,
      };
      return {
        explanation: `The reported level of damage (${sev}) is historically consistent with the type of incident and the amount being claimed. Everything lines up as you would expect.`,
      };
    },

    claim_to_coverage_ratio: () => {
      const pct = Math.round(v.claim_to_coverage_ratio * 100);
      if (raises) {
        if (pct > 90) return {
          explanation: `The claimed amount is ${pct}% of the total policy coverage — very close to the maximum payout. Claims that push right up to the coverage ceiling are sometimes a sign that the claimant knows the exact policy limit and has inflated the claim to match it.`,
        };
        return {
          explanation: `This claim represents ${pct}% of the total policy coverage. The higher this ratio, the more carefully the claim is examined, since it gets closer to the maximum payout the insurer would have to pay.`,
        };
      }
      return {
        explanation: `The claimed amount (${pct}% of the coverage limit) is proportionate and leaves a reasonable buffer below the policy maximum. This is what a genuine claim typically looks like.`,
      };
    },

    submission_delay_hours: () => {
      const h = v.submission_delay_hours;
      if (h === null) return null;
      if (raises) {
        if (h < 2) return {
          explanation: `The claim was submitted within ${h} hour${h !== 1 ? 's' : ''} of the incident being reported. While prompt reporting is encouraged, filing a claim within hours — before damage can typically be assessed — can sometimes indicate the claimant was already prepared to file.`,
        };
        if (h > 168) return {
          explanation: `The claim wasn't submitted until ${Math.round(h / 24)} days after the incident. Significant delays in reporting raise questions — genuine claimants typically file as soon as possible, especially for high-value incidents.`,
        };
      }
      return {
        explanation: `The claim was reported ${h < 48 ? `within ${h} hours` : `${Math.round(h / 24)} days`} after the incident — a completely normal timeframe. Prompt, but not suspiciously immediate, reporting is a reassuring sign.`,
      };
    },

    vehicle_value: () => {
      const val = v.vehicle_value;
      if (raises) return {
        explanation: `The insured vehicle is valued at ${fmt(val)}. Higher-value vehicles mean larger potential payouts, so related claims naturally receive a slightly higher level of review.`,
      };
      return {
        explanation: `The vehicle's market value of ${fmt(val)} is within a normal range. No concern was raised by the vehicle's value alone.`,
      };
    },

    has_anti_theft: () => {
      if (raises) {
        if (!v.has_anti_theft && v.claim_type === 'THEFT') return {
          explanation: `A theft is being claimed, but the vehicle had no registered anti-theft system. While many vehicles without protection do get stolen, this combination — especially for high-value vehicles — is a known risk pattern.`,
        };
        return {
          explanation: `The vehicle was not fitted with an anti-theft device. On its own this is minor, but combined with other signals it contributes to the overall risk picture.`,
        };
      }
      return {
        explanation: `The vehicle was fitted with an anti-theft system. Owners who invest in vehicle security are statistically less likely to be involved in fraudulent theft claims — this is a positive indicator.`,
      };
    },

    is_modified: () => {
      if (raises && v.is_modified) return {
        explanation: `The vehicle has modifications beyond its original factory specification. Modified vehicles can be harder to accurately value and are sometimes associated with higher-risk driving. The modifications are a contributing factor to the risk score.`,
      };
      return {
        explanation: `The vehicle has no modifications and is in its original factory configuration. This is a neutral to positive factor — standard vehicles are straightforward to value and assess.`,
      };
    },

    number_of_vehicles_involved: () => {
      const n = v.number_of_vehicles_involved;
      if (raises && n > 1) return {
        explanation: `${n} vehicles were involved in this incident. Multi-vehicle incidents can be more difficult to independently verify, and are occasionally used to create more complex, harder-to-disprove claims.`,
      };
      return {
        explanation: `Only one vehicle was involved in this incident. Single-vehicle incidents are straightforward to assess and verify, which is a minor positive signal.`,
      };
    },

    policyholder_age: () => {
      const age = v.policyholder_age;
      if (!age) return null;
      if (raises && age < 25) return {
        explanation: `The policyholder is ${age} years old. Statistically, younger drivers have higher rates of accidents and claims — this is a well-established actuarial factor. This is not an accusation; it simply reflects general population patterns in the data the model was trained on.`,
      };
      if (raises && age > 70) return {
        explanation: `At ${age} years old, the policyholder falls into a demographic that statistically files slightly more claims. Like the young driver factor, this is a pattern-based signal, not an individual judgment.`,
      };
      return {
        explanation: `The policyholder's age of ${age} falls within the lower-risk demographic for insurance claims. Their age profile did not raise any concern.`,
      };
    },

    credit_score: () => {
      const score = v.credit_score;
      if (!score) return null;
      if (raises && score < 600) return {
        explanation: `The policyholder has a credit score of ${score}, which is below average. Research has found a statistical link between financial difficulty and insurance fraud — not because people in financial difficulty are dishonest, but because financial stress is a known contributing factor. This does not mean this claim is fraudulent.`,
      };
      if (!raises && score >= 700) return {
        explanation: `The policyholder has a credit score of ${score}, indicating good financial standing. People with strong financial histories are statistically less likely to commit insurance fraud. This is a meaningful positive signal.`,
      };
      return {
        explanation: `The policyholder's credit score of ${score} is within a normal range and did not raise or lower the risk score significantly.`,
      };
    },

    years_with_company: () => {
      const yrs = v.years_with_company;
      if (yrs === null || yrs === undefined) return null;
      if (raises && yrs < 1) return {
        explanation: `This policyholder joined the company less than a year ago. New customers have limited claim history on file, which introduces a small degree of uncertainty. This is a very minor factor.`,
      };
      if (!raises && yrs >= 3) return {
        explanation: `This policyholder has been a customer for ${yrs} year${yrs !== 1 ? 's' : ''}. Long-term customers are significantly less likely to file fraudulent claims — customer loyalty is one of the strongest indicators of trustworthiness in insurance data.`,
      };
      return {
        explanation: `The policyholder has held their policy for a reasonable amount of time, which is a positive signal.`,
      };
    },

    policyholder_claim_count: () => {
      if (raises) return {
        explanation: `This policyholder has submitted claims in the past. While making multiple claims is not inherently suspicious, frequent claimants do attract closer review — particularly if the claims follow a pattern or increase in value over time.`,
      };
      return {
        explanation: `This policyholder has rarely or never filed a claim before. First-time claimants with clean histories are statistically far less likely to be involved in fraud. This is one of the strongest positive indicators available.`,
      };
    },

    incident_hour: () => {
      const h = v.incident_hour;
      if (h === null) return null;
      if (raises && (h >= 23 || h <= 4)) return {
        explanation: `The incident occurred in the early hours of the morning (${h}:00). Late-night incidents are harder to verify — there are typically fewer witnesses, less CCTV coverage, and reduced traffic. This makes the claim more difficult to independently corroborate.`,
      };
      return {
        explanation: `The incident took place during daytime or early evening hours. This makes it easier to verify through witnesses, traffic cameras, and other sources — a reassuring detail.`,
      };
    },

    incident_day_of_week: () => {
      const d = v.incident_day_of_week;
      if (d === null) return null;
      if (raises) return {
        explanation: `Incidents occurring on ${DAYS[d] || 'this day of the week'} are statistically slightly more likely to be associated with fraudulent claims, based on historical patterns. This is a very minor factor and should not be read as significant on its own.`,
      };
      return {
        explanation: `The day of the week when this incident occurred did not raise any flags in the model.`,
      };
    },

    incident_month: () => {
      const m = v.incident_month;
      if (!m) return null;
      const month = MONTHS[(m - 1)] || 'this month';
      if (raises) return {
        explanation: `${month} shows a slightly elevated claims rate in historical data. This is a very minor pattern-based factor and carries little weight on its own.`,
      };
      return {
        explanation: `The time of year when this incident occurred does not fall within any elevated-risk seasonal pattern.`,
      };
    },

    vehicle_age: () => {
      const age = v.vehicle_age;
      if (age === null) return null;
      if (raises && age > 10) return {
        explanation: `The vehicle is ${age} years old, yet the claim amount is substantial. Repair costs for older vehicles can sometimes exceed the vehicle's actual market value — a situation that can indicate an inflated claim, or in some cases, that the claimant is hoping to use the insurance money towards a newer vehicle.`,
      };
      return {
        explanation: `The vehicle's age is reasonable relative to the claim amount. There are no signs of the claim being disproportionate to the vehicle's actual worth.`,
      };
    },

    claim_type_encoded: () => {
      const t = TYPE_LABELS[v.claim_type] || v.claim_type;
      if (raises) return {
        explanation: `Historically, ${t} claims have a slightly higher rate of fraud compared to other claim types. This is a pattern picked up from training data and is a minor contributing factor — it reflects the type of claim, not anything specific about this claimant.`,
      };
      return {
        explanation: `This type of claim (${t}) has a below-average rate of fraud in historical data. The claim type itself was a reassuring signal.`,
      };
    },
  };

  const fn = map[featureName];
  if (!fn) {
    const cleanName = featureName.replace(/_/g, ' ');
    return {
      explanation: raises ? `The system flagged ${cleanName} as a potential risk factor based on historical data patterns.` : `The system identified ${cleanName} as a reassuring factor consistent with legitimate claims.`
    };
  }
  try { return fn(); } catch { return null; }
}

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

function PlainEnglishFraudExplanation({ claim, policyholder, vehicle, policy, fraudAnalysis, currency, fmtMoney }) {
  const rng = createSeededRNG(claim?.claim_number || 'default_seed');

  const explanation    = fraudAnalysis?.model_explanation ?? {};
  const riskIncreasers = explanation.risk_increasers ?? [];
  const riskDecreasers = explanation.risk_decreasers ?? [];

  const actual = buildActualValues(claim, policyholder, vehicle, policy);

  const concerns = riskIncreasers
    .map(f => ({ key: f.feature, card: getNarrative(f.feature, true,  actual, rng, currency, fmtMoney) }))
    .filter(x => x.card);

  const positives = riskDecreasers
    .map(f => ({ key: f.feature, card: getNarrative(f.feature, false, actual, rng, currency, fmtMoney) }))
    .filter(x => x.card);

  const isApproved = ['APPROVED','PAID'].includes(claim?.claim_status);
  const isRejected = claim?.claim_status === 'REJECTED';

  const summary = isApproved
    ? `After checking ${concerns.length + positives.length} factors, the system found this claim to be within acceptable risk levels and approved it automatically. The positive signals outweighed the concerns.`
    : isRejected
    ? `After checking ${concerns.length + positives.length} factors, the system found enough risk signals to flag this claim as suspicious and reject it automatically. An adjuster can review and override this decision if needed.`
    : `The system has reviewed this claim. There are both concerns and positive signals present — human judgment is needed to make a final decision.`;

  return (
    <div className="space-y-4">
      <p className="text-sm text-gray-800 leading-relaxed">
        {summary}
      </p>

      {concerns.length > 0 && (
        <div className="space-y-2 mt-4">
          {concerns.map(({ key, card }) => (
            <p key={key} className="text-sm text-gray-700 leading-relaxed">
              {card.explanation}
            </p>
          ))}
        </div>
      )}

      {positives.length > 0 && (
        <div className="space-y-2 mt-4">
          {positives.map(({ key, card }) => (
            <p key={key} className="text-sm text-gray-700 leading-relaxed">
              {card.explanation}
            </p>
          ))}
        </div>
      )}

      {concerns.length === 0 && positives.length === 0 && (
        <p className="text-sm text-gray-500">
          No detailed explanation available for this claim yet.
        </p>
      )}
    </div>
  );
}

// ── Override Panel ───────────────────────────────────────────────────────────
function OverridePanel({ claim, onOverride, onClose, isOverriding }) {
  const options = claim.claim_status === 'APPROVED'
    ? [{ status: 'REJECTED', label: 'Reject', color: '#EF4444', bg: '#FEE2E2' }]
    : claim.claim_status === 'REJECTED'
    ? [{ status: 'APPROVED', label: 'Approve', color: '#10B981', bg: '#D1FAE5' }]
    : [
        { status: 'APPROVED', label: 'Approve', color: '#10B981', bg: '#D1FAE5' },
        { status: 'REJECTED', label: 'Reject',  color: '#EF4444', bg: '#FEE2E2' },
      ];

  return (
    <div className="mt-4 p-4 rounded-xl border-2" style={{ borderColor: '#E5E7EB', backgroundColor: '#FAFAFA' }}>
      <div className="flex items-center justify-between mb-3">
        <p className="text-xs font-bold uppercase tracking-wider" style={{ color: '#7F8C8D' }}>
          Adjuster Override
        </p>
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

  // Toggle for Technical vs Plain English
  const [showTechnical, setShowTechnical] = useState(false);

  // Override panel
  const [showOverridePanel, setShowOverridePanel] = useState(false);
  const [isOverriding,      setIsOverriding]      = useState(false);

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

      // Fraud / SHAP analysis
      try {
        const fa = await api.detectFraud({ claim_id: id });
        setFraudAnalysis(fa);
      } catch { /* non-fatal */ }

    } catch {
      showNotification('Failed to load claim details', 'error');
    } finally {
      setIsLoading(false);
    }
  };

  // ── Override handler ────────────────────────────────────────────────────
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

  // ── Guards ──────────────────────────────────────────────────────────────
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

  // ── Derived values ──────────────────────────────────────────────────────
  const sp         = STATUS_PALETTE[claim.claim_status] || STATUS_PALETTE.SUBMITTED;
  const sevColor   = SEVERITY_COLOR[claim.severity] || '#7F8C8D';
  const creditC    = CREDIT_COLORS[policyholder?.credit_rating] || CREDIT_COLORS.FAIR;
  const creditSc   = policyholder?.credit_score || 650;
  const fraudScore = claim.fraud_score ?? 0;
  const isApproved = claim.claim_status === 'APPROVED' || claim.claim_status === 'PAID';
  const isRejected = claim.claim_status === 'REJECTED';

  const explanation    = fraudAnalysis?.model_explanation ?? {};
  const riskIncreasers = explanation.risk_increasers ?? [];
  const riskDecreasers = explanation.risk_decreasers ?? [];
  const topFeatures    = explanation.top_features    ?? [];

  // ── Tabs ───────────────────────────────────────────────────────────────
  const tabs = [
    { id: 'overview',   label: 'Overview',      icon: <Activity   className="w-3.5 h-3.5" /> },
    { id: 'policyholder', label: 'Policyholder',  icon: <User       className="w-3.5 h-3.5" /> },
    { id: 'vehicle',      label: 'Vehicle',       icon: <Car        className="w-3.5 h-3.5" /> },
    { id: 'fraud',        label: 'Fraud Analysis', icon: <Shield     className="w-3.5 h-3.5" /> },
    { id: 'assessment',   label: 'Loss Assessment',icon: <Calculator className="w-3.5 h-3.5" /> },
  ];

  const timeline = [
    { date: fmtDateTime(claim.incident_date),  event: 'Incident occurred',  icon: AlertTriangle, done: true },
    { date: fmtDateTime(claim.submitted_date), event: 'Claim submitted',    icon: FileText,      done: true },
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

        {/* ── Hero ──────────────────────────────────────────────────────── */}
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
            
            {/* Currency Toggle inside Hero block */}
            <div className="text-right flex-shrink-0">
              <div className="flex items-center gap-2 justify-end mb-1">
                <span className="text-xs font-medium" style={{ color: 'rgba(255,255,255,0.5)' }}>Claimed Amount</span>
                <div className="flex gap-0.5 p-0.5 rounded-lg" style={{ backgroundColor: 'rgba(255,255,255,0.1)' }}>
                  {['USD', 'ZWG'].map((c) => (
                    <button key={c} onClick={() => setCurrency(c)} className="px-2 py-0.5 rounded-md text-xs font-bold transition-all" style={{ backgroundColor: currency === c ? '#FF6B4A' : 'transparent', color: currency === c ? 'white' : 'rgba(255,255,255,0.5)' }}>{c}</button>
                  ))}
                </div>
              </div>
              <p className="text-3xl font-bold text-white">{fmtMoney(claim.claimed_amount, currency)}</p>
              <p className="text-xs mt-1" style={{ color: 'rgba(255,255,255,0.35)' }}>
                {fmtDate(claim.incident_date)}
              </p>
            </div>
          </div>

          {/* Quick stats */}
          <div className="grid grid-cols-4 gap-3 mt-6">
            {[
              { label: 'Approved', value: fmtMoney(claim.approved_amount, currency) },
              { label: 'Paid',     value: fmtMoney(claim.paid_amount, currency) },
              {
                label: 'Auto Decision',
                value: isApproved
                  ? '✓ Approved'
                  : isRejected
                  ? '✗ Rejected'
                  : 'Processing…',
              },
              { label: 'Policy', value: claim.policy_number || '—' },
            ].map(({ label, value }) => (
              <div key={label} className="rounded-xl px-4 py-3" style={{ backgroundColor: 'rgba(255,255,255,0.08)' }}>
                <p className="text-xs mb-1" style={{ color: 'rgba(255,255,255,0.45)' }}>{label}</p>
                <p className="text-base font-bold text-white truncate">{value}</p>
              </div>
            ))}
          </div>
        </div>

        {/* ── Tabs ──────────────────────────────────────────────────────── */}
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

        {/* ── Tab Content ───────────────────────────────────────────────── */}
        <div className="p-8">

          {/* ══ OVERVIEW ══════════════════════════════════════════════════ */}
          {activeTab === 'overview' && (
            <div className="grid grid-cols-3 gap-6">
              <div className="col-span-2 space-y-6">

                {/* Incident details */}
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
                        {/* New Tab Evidence Button */}
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

                {/* Timeline */}
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

              {/* Right column */}
              <div className="space-y-6">
                
                {/* Fraud / Risk snapshot */}
                <SectionCard icon={<Shield className="w-4 h-4" />} title="Risk Assessment" accent="#EF4444">
                  <div className="text-center py-4">
                    <p className="text-4xl font-bold" style={{ color: fraudScore > 0.5 ? '#EF4444' : '#10B981' }}>
                      {fmtPct(fraudScore)}
                    </p>
                    <p className="text-xs mt-1 font-medium" style={{ color: '#9CA3AF' }}>
                      {fraudScore > 0.8 ? 'Critical risk' : fraudScore > 0.5 ? 'High risk' : fraudScore > 0.3 ? 'Moderate risk' : 'Low risk'}
                    </p>
                    
                    {/* Integrated Auto Decision Banner */}
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

                {/* Policy snapshot */}
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

                {/* Quick-access to Loss Assessment */}
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

          {/* ══ FRAUD ANALYSIS ════════════════════════════════════════════ */}
          {activeTab === 'fraud' && (
            <div className="grid grid-cols-3 gap-6">
              
              {/* Left Column */}
              <div className="col-span-2 space-y-6">
                
                {/* ── MINIMAL AUTOMATED DECISION CARD ── */}
                <SectionCard icon={<Shield className="w-4 h-4" />} title="Automated Decision" accent="#9CA3AF">
                  
                  <div className="flex items-center justify-between mb-4">
                    <div>
                      <p className="text-sm font-bold text-gray-800">
                        {isApproved ? 'Approved' : isRejected ? 'Rejected' : 'Under Review'}
                      </p>
                      <p className="text-xs text-gray-500 mt-1">
                        Risk score: {fmtPct(fraudScore)}
                      </p>
                    </div>

                    <button
                      onClick={() => setShowOverridePanel((p) => !p)}
                      className="px-3 py-1.5 text-xs font-semibold border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors">
                      {showOverridePanel ? 'Cancel' : 'Override Decision'}
                    </button>
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

                {/* 3. What Drove This Decision */}
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
                    }
                  >
                    {showTechnical ? (
                      // Original numeric SHAP display — for IT staff
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
                      // Plain English — default view for non-technical users
                      <PlainEnglishFraudExplanation
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

              {/* ── RIGHT COLUMN ── */}
              <div className="space-y-6">
                
                {/* 1. Claim Reference */}
                <SectionCard icon={<FileText className="w-4 h-4" />} title="Claim Reference" accent="#9CA3AF">
                  <InfoRow icon={<Hash className="w-3.5 h-3.5" />}       label="Number"    value={claim.claim_number} mono />
                  <InfoRow icon={<Calendar className="w-3.5 h-3.5" />}   label="Submitted" value={fmtDate(claim.submitted_date)} />
                  <InfoRow icon={<Clock className="w-3.5 h-3.5" />}      label="Reviewed"  value={fmtDate(claim.reviewed_date)} />
                  <InfoRow icon={<DollarSign className="w-3.5 h-3.5" />} label="Approved"  value={fmtMoney(claim.approved_amount, currency)} />
                </SectionCard>

                {/* 2. Risk Signals */}
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

          {/* ══ VEHICLE ════════════════════════════════════════════════════ */}
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
                      { key: 'has_anti_theft', label: 'Anti-Theft', icon: <Lock    className="w-4 h-4" />, invert: false },
                      { key: 'has_airbags',    label: 'Airbags',    icon: <Shield  className="w-4 h-4" />, invert: false },
                      { key: 'has_abs',        label: 'ABS Brakes', icon: <Activity className="w-4 h-4" />, invert: false },
                      { key: 'is_modified',    label: 'Modified',   icon: <Wrench  className="w-4 h-4" />, invert: true  },
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

          {/* ══ LOSS ASSESSMENT ══════════════════════════════════════════════ */}
          {activeTab === 'assessment' && (
            <EmbeddedLossAssessor claim={claim} vehicle={vehicle} currency={currency} />
          )}

        </div>
      </div>
    </div>
  );
}