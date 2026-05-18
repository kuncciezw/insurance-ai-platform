import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../services/api';
import Sidebar from './Sidebar';
import { useNotification } from './notifications/useNotification';
import {
  User,
  Car,
  ShieldCheck,
  ChevronRight,
  ChevronLeft,
  Check,
  TrendingUp,
  MapPin,
  Briefcase,
  Settings,
} from 'lucide-react';

// ─── Helpers ────────────────────────────────────────────────────────────────

const generatePolicyHolderId = () => {
  const randomDigits = Math.floor(1000000000 + Math.random() * 9000000000);
  return `ZW-PH-${randomDigits}`;
};

const STEPS = [
  { id: 1, label: 'Personal Info',     Icon: User      },
  { id: 2, label: 'Contact',           Icon: MapPin    },
  { id: 3, label: 'Financial',         Icon: Briefcase },
  { id: 4, label: 'Vehicle',           Icon: Car       },
  { id: 5, label: 'Safety & Review',   Icon: ShieldCheck },
];

const getCreditScoreInfo = (score) => {
  if (score >= 750) return { color: '#065F46', bg: '#D1FAE5', label: 'Excellent' };
  if (score >= 700) return { color: '#1E40AF', bg: '#DBEAFE', label: 'Good'      };
  if (score >= 650) return { color: '#92400E', bg: '#FEF3C7', label: 'Fair'      };
  if (score >= 600) return { color: '#9A3412', bg: '#FED7AA', label: 'Poor'      };
  return               { color: '#991B1B', bg: '#FEE2E2', label: 'Very Poor'  };
};

const inputCls = 'w-full px-4 py-2.5 rounded-lg border focus:outline-none focus:ring-2 transition-all';
const inputSty = { borderColor: '#E5E7EB' };
const labelCls = 'block text-sm font-semibold mb-2';
const labelSty = { color: '#2C3E50' };

// ─── Component ───────────────────────────────────────────────────────────────

export default function OnboardingWizard() {
  const navigate = useNavigate();
  const { showNotification, NotificationContainer } = useNotification();

  const [currentStep,           setCurrentStep]           = useState(1);
  const [isSubmitting,          setIsSubmitting]          = useState(false);
  const [calculatedCreditScore, setCalculatedCreditScore] = useState(650);

  // ── Step 1-3 state (Policyholder) ───────────────────────────────────────────
  const [ph, setPh] = useState({
    policy_holder_id:  generatePolicyHolderId(),
    first_name:        '',
    last_name:         '',
    date_of_birth:     '',
    gender:            'M',
    national_id:       '',
    email:             '',
    phone_number:      '',
    address_line1:     '',
    address_line2:     '',
    city:              'Bulawayo',
    state:             'Bulawayo',
    country:           'Zimbabwe',
    marital_status:    'SINGLE',
    occupation:        'EMPLOYED',
    monthly_income:    '',
    years_with_company: '',
  });

  // ── Step 4-5 state (Vehicle) ────────────────────────────────────────────────
  const [veh, setVeh] = useState({
    registration_number: '',
    make:                '',
    model:               '',
    manufacture_year:    new Date().getFullYear(),
    vehicle_type:        'SEDAN',
    vin:                 '',
    seating_capacity:    '',
    fuel_type:           'PETROL',
    engine_capacity:     '',
    market_value:        '',
    odometer_reading:    '',
  });

  // ── Step 5 state (Risk) ─────────────────────────────────────────────────────
  const [risk, setRisk] = useState({
    has_driving_license:    false,
    has_defensive_license:  false,
    is_medical_license_valid: true,
    has_anti_theft: false,
    has_airbags:    true,
    has_abs:        true,
    is_modified:    false,
  });

  // ── Real-time credit score ──────────────────────────────────────────────────
  useEffect(() => {
    let score = 650;

    const income = parseFloat(ph.monthly_income) || 0;
    if      (income >= 5000) score += 50;
    else if (income >= 3000) score += 30;
    else if (income >= 1500) score += 10;

    const years = parseInt(ph.years_with_company) || 0;
    score += Math.min(years * 5, 50);

    if (risk.has_driving_license)      score += 20;
    if (risk.has_defensive_license)    score += 15;
    if (!risk.is_medical_license_valid) score -= 30;

    setCalculatedCreditScore(Math.max(300, Math.min(850, score)));
  }, [
    ph.monthly_income,
    ph.years_with_company,
    risk.has_driving_license,
    risk.has_defensive_license,
    risk.is_medical_license_valid,
  ]);

  // ── Validation ──────────────────────────────────────────────────────────────
  const validateStep = (step) => {
    if (step === 1) {
      if (!ph.first_name || !ph.last_name || !ph.date_of_birth || !ph.gender) {
        showNotification('Please fill in all required fields.', 'error');
        return false;
      }
    }
    if (step === 2) {
      if (!ph.email || !ph.phone_number || !ph.address_line1 || !ph.city || !ph.state || !ph.country) {
        showNotification('Please fill in all required fields.', 'error');
        return false;
      }
    }
    if (step === 3) {
      if (ph.monthly_income === '' || ph.years_with_company === '') {
        showNotification('Please fill in all required fields.', 'error');
        return false;
      }
    }
    if (step === 4) {
      if (!veh.make || !veh.model || !veh.registration_number || !veh.vin) {
        showNotification('Please fill in all required fields.', 'error');
        return false;
      }
      if (veh.vin.length !== 17) {
        showNotification('VIN must be exactly 17 characters.', 'error');
        return false;
      }
    }
    if (step === 5) {
      if (veh.market_value === '' || veh.odometer_reading === '' || veh.engine_capacity === '' || veh.seating_capacity === '') {
        showNotification('Please fill in all required fields.', 'error');
        return false;
      }
    }
    return true;
  };

  const handleNext = () => {
    if (validateStep(currentStep)) setCurrentStep((s) => Math.min(s + 1, 5));
  };

  const handleBack = () => setCurrentStep((s) => Math.max(s - 1, 1));

  // ── Submit ──────────────────────────────────────────────────────────────────
  const handleSubmit = async () => {
    setIsSubmitting(true);
    try {
      const phPayload = {
        ...ph,
        monthly_income: parseFloat(ph.monthly_income) || 0,
        years_with_company: parseInt(ph.years_with_company) || 0,
        has_driving_license:      risk.has_driving_license,
        has_defensive_license:    risk.has_defensive_license,
        is_medical_license_valid: risk.is_medical_license_valid,
        is_active: true,
      };
      const phResponse = await api.createPolicyholder(phPayload);

      const vehPayload = {
        ...veh,
        manufacture_year: parseInt(veh.manufacture_year) || new Date().getFullYear(),
        seating_capacity: parseInt(veh.seating_capacity) || 5,
        engine_capacity: parseInt(veh.engine_capacity) || 1500,
        market_value: parseFloat(veh.market_value) || 0,
        odometer_reading: parseInt(veh.odometer_reading) || 0,
        policyholder:   phResponse.id,
        has_anti_theft: risk.has_anti_theft,
        has_airbags:    risk.has_airbags,
        has_abs:        risk.has_abs,
        is_modified:    risk.is_modified,
      };
      await api.createVehicle(vehPayload);

      showNotification('Registration completed successfully!', 'success');
      setTimeout(() => navigate('/policies'), 1200);
    } catch (err) {
      console.error('Onboarding failed:', err);
      showNotification(
        err.message || 'Registration failed. Please check all fields and try again.',
        'error'
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  const scoreInfo = getCreditScoreInfo(calculatedCreditScore);

  // ─── Render ─────────────────────────────────────────────────────────────────
  return (
    <div className="flex h-screen overflow-hidden" style={{ backgroundColor: '#F8F9FA' }}>
      <Sidebar />
      <NotificationContainer />

      <div className="flex-1 overflow-y-auto">
        
        {/* ── Header ──────────────────────────────────────────────────────── */}
        <div className="px-8 pt-8 pb-6" style={{ backgroundColor: 'white', borderBottom: '1px solid #E5E7EB' }}>
          <h2 className="text-3xl font-bold" style={{ color: '#2C3E50' }}>
            New Customer Onboarding
          </h2>
          <p className="mt-1 text-sm" style={{ color: '#7F8C8D' }}>
            Register a new policyholder and their vehicle
          </p>
        </div>

        {/* ── Progress Bar ────────────────────────────────────────────────── */}
        <div className="px-8 py-6" style={{ backgroundColor: 'white', borderBottom: '1px solid #E5E7EB' }}>
          <div className="flex items-center justify-between max-w-3xl">
            {STEPS.map(({ id, label, Icon }, index) => {
              const isCompleted = currentStep > id;
              const isActive    = currentStep === id;
              return (
                <div key={id} className="flex items-center flex-1">
                  <div className="flex flex-col items-center flex-shrink-0">
                    <div
                      className="w-10 h-10 rounded-full flex items-center justify-center transition-all duration-300 relative"
                      style={{
                        backgroundColor: isCompleted || isActive ? '#FF6B4A' : '#E5E7EB',
                        color:           isCompleted || isActive ? 'white'   : '#7F8C8D',
                      }}
                    >
                      {isCompleted
                        ? <Check className="w-5 h-5" />
                        : <Icon  className="w-5 h-5" />}
                    </div>
                    <span
                      className="mt-2 text-xs font-semibold"
                      style={{ color: isActive ? '#FF6B4A' : isCompleted ? '#2C3E50' : '#7F8C8D' }}
                    >
                      {label}
                    </span>
                  </div>

                  {index < STEPS.length - 1 && (
                    <div
                      className="flex-1 h-1 mx-3 rounded-full transition-all duration-300"
                      style={{ backgroundColor: currentStep > id ? '#FF6B4A' : '#E5E7EB' }}
                    />
                  )}
                </div>
              );
            })}
          </div>
        </div>

        {/* ── Form Content ────────────────────────────────────────────────── */}
        <div className="px-8 py-8">
          <div className="bg-white rounded-lg shadow-sm p-8" style={{ borderLeft: '4px solid #FF6B4A' }}>

            {/* ════════════════════════════════════════════════
                STEP 1 — Personal Information
            ════════════════════════════════════════════════ */}
            {currentStep === 1 && (
              <div>
                <h3 className="text-xl font-bold mb-6" style={{ color: '#2C3E50' }}>
                  Personal Information
                </h3>

                <div className="grid grid-cols-2 gap-6">
                  <div>
                    <label className={labelCls} style={labelSty}>First Name *</label>
                    <input
                      type="text"
                      required
                      value={ph.first_name}
                      onChange={(e) => setPh({ ...ph, first_name: e.target.value })}
                      className={inputCls}
                      style={{ ...inputSty, focusRingColor: '#FF6B4A' }}
                      placeholder="First name"
                    />
                  </div>
                  <div>
                    <label className={labelCls} style={labelSty}>Last Name *</label>
                    <input
                      type="text"
                      required
                      value={ph.last_name}
                      onChange={(e) => setPh({ ...ph, last_name: e.target.value })}
                      className={inputCls}
                      style={inputSty}
                      placeholder="Last name"
                    />
                  </div>

                  <div>
                    <label className={labelCls} style={labelSty}>Date of Birth *</label>
                    <input
                      type="date"
                      required
                      value={ph.date_of_birth}
                      onChange={(e) => setPh({ ...ph, date_of_birth: e.target.value })}
                      className={inputCls}
                      style={inputSty}
                      max={new Date().toISOString().split('T')[0]}
                    />
                  </div>
                  <div>
                    <label className={labelCls} style={labelSty}>Gender *</label>
                    <select
                      required
                      value={ph.gender}
                      onChange={(e) => setPh({ ...ph, gender: e.target.value })}
                      className={inputCls}
                      style={inputSty}
                    >
                      <option value="M">Male</option>
                      <option value="F">Female</option>
                      <option value="O">Other</option>
                    </select>
                  </div>

                  <div className="col-span-2">
                    <label className={labelCls} style={labelSty}>National ID</label>
                    <input
                      type="text"
                      value={ph.national_id}
                      onChange={(e) => setPh({ ...ph, national_id: e.target.value })}
                      className={inputCls}
                      style={inputSty}
                      placeholder="e.g., 63-123456A78"
                    />
                  </div>
                </div>
              </div>
            )}

            {/* ════════════════════════════════════════════════
                STEP 2 — Contact & Address
            ════════════════════════════════════════════════ */}
            {currentStep === 2 && (
              <div>
                <h3 className="text-xl font-bold mb-6" style={{ color: '#2C3E50' }}>
                  Contact & Address
                </h3>

                <div className="grid grid-cols-2 gap-6">
                  <div>
                    <label className={labelCls} style={labelSty}>Email *</label>
                    <input
                      type="email"
                      required
                      value={ph.email}
                      onChange={(e) => setPh({ ...ph, email: e.target.value })}
                      className={inputCls}
                      style={inputSty}
                      placeholder="email@example.com"
                    />
                  </div>
                  <div>
                    <label className={labelCls} style={labelSty}>Phone Number *</label>
                    <input
                      type="text"
                      required
                      value={ph.phone_number}
                      onChange={(e) => setPh({ ...ph, phone_number: e.target.value })}
                      className={inputCls}
                      style={inputSty}
                      placeholder="+263 123 456 789"
                    />
                  </div>

                  <div className="col-span-2">
                    <label className={labelCls} style={labelSty}>Address Line 1 *</label>
                    <input
                      type="text"
                      required
                      value={ph.address_line1}
                      onChange={(e) => setPh({ ...ph, address_line1: e.target.value })}
                      className={inputCls}
                      style={inputSty}
                      placeholder="Street address"
                    />
                  </div>

                  <div className="col-span-2">
                    <label className={labelCls} style={labelSty}>Address Line 2</label>
                    <input
                      type="text"
                      value={ph.address_line2}
                      onChange={(e) => setPh({ ...ph, address_line2: e.target.value })}
                      className={inputCls}
                      style={inputSty}
                      placeholder="Apartment, suite, etc. (optional)"
                    />
                  </div>

                  <div>
                    <label className={labelCls} style={labelSty}>City *</label>
                    <input
                      type="text"
                      required
                      value={ph.city}
                      onChange={(e) => setPh({ ...ph, city: e.target.value })}
                      className={inputCls}
                      style={inputSty}
                      placeholder="Bulawayo"
                    />
                  </div>
                  <div>
                    <label className={labelCls} style={labelSty}>State/Province *</label>
                    <input
                      type="text"
                      required
                      value={ph.state}
                      onChange={(e) => setPh({ ...ph, state: e.target.value })}
                      className={inputCls}
                      style={inputSty}
                      placeholder="Bulawayo"
                    />
                  </div>

                  <div className="col-span-2">
                    <label className={labelCls} style={labelSty}>Country *</label>
                    <input
                      type="text"
                      required
                      value={ph.country}
                      onChange={(e) => setPh({ ...ph, country: e.target.value })}
                      className={inputCls}
                      style={inputSty}
                    />
                  </div>
                </div>
              </div>
            )}

            {/* ════════════════════════════════════════════════
                STEP 3 — Financial Profile
            ════════════════════════════════════════════════ */}
            {currentStep === 3 && (
              <div>
                <h3 className="text-xl font-bold mb-6" style={{ color: '#2C3E50' }}>
                  Financial Profile
                </h3>

                {/* Credit Score Banner */}
                <div
                  className="mb-6 p-4 rounded-lg flex items-center justify-between"
                  style={{ backgroundColor: scoreInfo.bg }}
                >
                  <div className="flex items-center gap-3">
                    <TrendingUp className="w-6 h-6" style={{ color: scoreInfo.color }} />
                    <div>
                      <p className="text-sm font-semibold" style={{ color: scoreInfo.color }}>
                        Credit Score
                      </p>
                      <p className="text-xs" style={{ color: '#7F8C8D' }}>
                        Live calculation
                      </p>
                    </div>
                  </div>
                  <div className="text-right">
                    <span className="text-3xl font-bold" style={{ color: scoreInfo.color }}>
                      {calculatedCreditScore}
                    </span>
                    <p className="text-sm font-semibold" style={{ color: scoreInfo.color }}>
                      {scoreInfo.label}
                    </p>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-6">
                  <div>
                    <label className={labelCls} style={labelSty}>Marital Status *</label>
                    <select
                      required
                      value={ph.marital_status}
                      onChange={(e) => setPh({ ...ph, marital_status: e.target.value })}
                      className={inputCls}
                      style={inputSty}
                    >
                      <option value="SINGLE">Single</option>
                      <option value="MARRIED">Married</option>
                      <option value="DIVORCED">Divorced</option>
                      <option value="WIDOWED">Widowed</option>
                    </select>
                  </div>
                  <div>
                    <label className={labelCls} style={labelSty}>Occupation *</label>
                    <select
                      required
                      value={ph.occupation}
                      onChange={(e) => setPh({ ...ph, occupation: e.target.value })}
                      className={inputCls}
                      style={inputSty}
                    >
                      <option value="EMPLOYED">Employed</option>
                      <option value="SELF_EMPLOYED">Self-Employed</option>
                      <option value="UNEMPLOYED">Unemployed</option>
                      <option value="RETIRED">Retired</option>
                      <option value="STUDENT">Student</option>
                    </select>
                  </div>

                  <div>
                    <label className={labelCls} style={labelSty}>Monthly Income ($) *</label>
                    <input
                      type="number"
                      required
                      value={ph.monthly_income}
                      onChange={(e) => setPh({ ...ph, monthly_income: e.target.value })}
                      className={inputCls}
                      style={inputSty}
                      min="0"
                      step="100"
                      placeholder="2000"
                    />
                  </div>
                  <div>
                    <label className={labelCls} style={labelSty}>Years with Company *</label>
                    <input
                      type="number"
                      required
                      value={ph.years_with_company}
                      onChange={(e) => setPh({ ...ph, years_with_company: e.target.value })}
                      className={inputCls}
                      style={inputSty}
                      min="0"
                      max="100"
                      placeholder="3"
                    />
                  </div>
                </div>
              </div>
            )}

            {/* ════════════════════════════════════════════════
                STEP 4 — Vehicle Details
            ════════════════════════════════════════════════ */}
            {currentStep === 4 && (
              <div>
                <h3 className="text-xl font-bold mb-6" style={{ color: '#2C3E50' }}>
                  Vehicle Details
                </h3>

                <div className="grid grid-cols-2 gap-6">
                  <div>
                    <label className={labelCls} style={labelSty}>Make *</label>
                    <input
                      type="text"
                      required
                      value={veh.make}
                      onChange={(e) => setVeh({ ...veh, make: e.target.value })}
                      className={inputCls}
                      style={inputSty}
                      placeholder="e.g., Toyota"
                    />
                  </div>
                  <div>
                    <label className={labelCls} style={labelSty}>Model *</label>
                    <input
                      type="text"
                      required
                      value={veh.model}
                      onChange={(e) => setVeh({ ...veh, model: e.target.value })}
                      className={inputCls}
                      style={inputSty}
                      placeholder="e.g., Corolla"
                    />
                  </div>

                  <div>
                    <label className={labelCls} style={labelSty}>Manufacture Year *</label>
                    <input
                      type="number"
                      required
                      value={veh.manufacture_year}
                      onChange={(e) => setVeh({ ...veh, manufacture_year: e.target.value })}
                      className={inputCls}
                      style={inputSty}
                      min="1900"
                      max={new Date().getFullYear() + 1}
                    />
                  </div>
                  <div>
                    <label className={labelCls} style={labelSty}>Vehicle Type *</label>
                    <select
                      required
                      value={veh.vehicle_type}
                      onChange={(e) => setVeh({ ...veh, vehicle_type: e.target.value })}
                      className={inputCls}
                      style={inputSty}
                    >
                      <option value="SEDAN">Sedan</option>
                      <option value="SUV">SUV</option>
                      <option value="TRUCK">Truck</option>
                      <option value="HATCHBACK">Hatchback</option>
                      <option value="COUPE">Coupe</option>
                      <option value="VAN">Van</option>
                      <option value="SPORTS">Sports Car</option>
                    </select>
                  </div>

                  <div>
                    <label className={labelCls} style={labelSty}>Registration Number *</label>
                    <input
                      type="text"
                      required
                      value={veh.registration_number}
                      onChange={(e) => setVeh({ ...veh, registration_number: e.target.value })}
                      className={inputCls}
                      style={inputSty}
                      placeholder="e.g., ABZ-1234"
                    />
                  </div>
                  <div>
                    <label className={labelCls} style={labelSty}>VIN (Chassis Number) *</label>
                    <input
                      type="text"
                      required
                      value={veh.vin}
                      onChange={(e) => setVeh({ ...veh, vin: e.target.value.toUpperCase() })}
                      className={inputCls}
                      style={inputSty}
                      placeholder="17-character VIN"
                      maxLength="17"
                    />
                    <p className="mt-1 text-xs" style={{ color: '#7F8C8D' }}>
                      {veh.vin.length}/17 characters
                    </p>
                  </div>

                  <div className="col-span-2">
                    <label className={labelCls} style={labelSty}>Fuel Type *</label>
                    <select
                      required
                      value={veh.fuel_type}
                      onChange={(e) => setVeh({ ...veh, fuel_type: e.target.value })}
                      className={inputCls}
                      style={inputSty}
                    >
                      <option value="PETROL">Petrol</option>
                      <option value="DIESEL">Diesel</option>
                      <option value="ELECTRIC">Electric</option>
                      <option value="HYBRID">Hybrid</option>
                      <option value="CNG">CNG</option>
                    </select>
                  </div>
                </div>
              </div>
            )}

            {/* ════════════════════════════════════════════════
                STEP 5 — Technical Specs & Safety
            ════════════════════════════════════════════════ */}
            {currentStep === 5 && (
              <div>
                <h3 className="text-xl font-bold mb-6" style={{ color: '#2C3E50' }}>
                  Technical Specs & Safety
                </h3>

                <div className="grid grid-cols-2 gap-6 mb-6">
                  <div>
                    <label className={labelCls} style={labelSty}>Market Value ($) *</label>
                    <input
                      type="number"
                      required
                      value={veh.market_value}
                      onChange={(e) => setVeh({ ...veh, market_value: e.target.value })}
                      className={inputCls}
                      style={inputSty}
                      min="0"
                      step="100"
                      placeholder="25000"
                    />
                  </div>
                  <div>
                    <label className={labelCls} style={labelSty}>Odometer Reading (km) *</label>
                    <input
                      type="number"
                      required
                      value={veh.odometer_reading}
                      onChange={(e) => setVeh({ ...veh, odometer_reading: e.target.value })}
                      className={inputCls}
                      style={inputSty}
                      min="0"
                      placeholder="50000"
                    />
                  </div>

                  <div>
                    <label className={labelCls} style={labelSty}>Seating Capacity *</label>
                    <input
                      type="number"
                      required
                      value={veh.seating_capacity}
                      onChange={(e) => setVeh({ ...veh, seating_capacity: e.target.value })}
                      className={inputCls}
                      style={inputSty}
                      min="2"
                      max="50"
                      placeholder="5"
                    />
                  </div>
                  <div>
                    <label className={labelCls} style={labelSty}>Engine Capacity (cc) *</label>
                    <input
                      type="number"
                      required
                      value={veh.engine_capacity}
                      onChange={(e) => setVeh({ ...veh, engine_capacity: e.target.value })}
                      className={inputCls}
                      style={inputSty}
                      min="500"
                      max="10000"
                      placeholder="1500"
                    />
                  </div>
                </div>

                {/* Driver Verification */}
                <div className="mb-6">
                  <label className={labelCls} style={labelSty}>
                    Driver Verification
                  </label>
                  <div className="p-4 rounded-lg space-y-3" style={{ backgroundColor: '#F8F9FA' }}>
                    <label className="flex items-start gap-3 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={risk.has_driving_license}
                        onChange={(e) => setRisk({ ...risk, has_driving_license: e.target.checked })}
                        className="w-4 h-4 mt-0.5 rounded"
                        style={{ accentColor: '#FF6B4A' }}
                      />
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="font-medium text-sm" style={{ color: '#2C3E50' }}>
                            Valid Driving License
                          </span>
                          <span
                            className="text-xs px-2 py-0.5 rounded-full font-medium"
                            style={{ backgroundColor: '#D1FAE5', color: '#065F46' }}
                          >
                            +20 pts
                          </span>
                        </div>
                        <p className="text-xs mt-0.5" style={{ color: '#7F8C8D' }}>
                          Customer holds a current, valid driving license
                        </p>
                      </div>
                    </label>

                    <label className="flex items-start gap-3 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={risk.has_defensive_license}
                        onChange={(e) => setRisk({ ...risk, has_defensive_license: e.target.checked })}
                        className="w-4 h-4 mt-0.5 rounded"
                        style={{ accentColor: '#FF6B4A' }}
                      />
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="font-medium text-sm" style={{ color: '#2C3E50' }}>
                            Defensive Driving Certificate
                          </span>
                          <span
                            className="text-xs px-2 py-0.5 rounded-full font-medium"
                            style={{ backgroundColor: '#D1FAE5', color: '#065F46' }}
                          >
                            +15 pts
                          </span>
                        </div>
                        <p className="text-xs mt-0.5" style={{ color: '#7F8C8D' }}>
                          Completed a certified defensive driving course
                        </p>
                      </div>
                    </label>

                    <label className="flex items-start gap-3 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={risk.is_medical_license_valid}
                        onChange={(e) => setRisk({ ...risk, is_medical_license_valid: e.target.checked })}
                        className="w-4 h-4 mt-0.5 rounded"
                        style={{ accentColor: '#FF6B4A' }}
                      />
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="font-medium text-sm" style={{ color: '#2C3E50' }}>
                            Medical Fitness Certificate Valid
                          </span>
                          <span
                            className="text-xs px-2 py-0.5 rounded-full font-medium"
                            style={{ backgroundColor: '#FEE2E2', color: '#991B1B' }}
                          >
                            −30 pts if unchecked
                          </span>
                        </div>
                        <p className="text-xs mt-0.5" style={{ color: '#7F8C8D' }}>
                          Medical fitness certificate is current and valid
                        </p>
                      </div>
                    </label>
                  </div>
                </div>

                {/* Vehicle Safety Features */}
                <div className="mb-6">
                  <label className={labelCls} style={labelSty}>
                    Vehicle Safety Features
                  </label>
                  <div
                    className="p-4 rounded-lg grid grid-cols-2 gap-3"
                    style={{ backgroundColor: '#F8F9FA' }}
                  >
                    <label className="flex items-center gap-2 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={risk.has_anti_theft}
                        onChange={(e) => setRisk({ ...risk, has_anti_theft: e.target.checked })}
                        className="w-4 h-4 rounded"
                        style={{ accentColor: '#FF6B4A' }}
                      />
                      <span className="text-sm" style={{ color: '#7F8C8D' }}>Anti-theft System</span>
                    </label>

                    <label className="flex items-center gap-2 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={risk.has_airbags}
                        onChange={(e) => setRisk({ ...risk, has_airbags: e.target.checked })}
                        className="w-4 h-4 rounded"
                        style={{ accentColor: '#FF6B4A' }}
                      />
                      <span className="text-sm" style={{ color: '#7F8C8D' }}>Airbags</span>
                    </label>

                    <label className="flex items-center gap-2 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={risk.has_abs}
                        onChange={(e) => setRisk({ ...risk, has_abs: e.target.checked })}
                        className="w-4 h-4 rounded"
                        style={{ accentColor: '#FF6B4A' }}
                      />
                      <span className="text-sm" style={{ color: '#7F8C8D' }}>ABS Brakes</span>
                    </label>

                    <label className="flex items-center gap-2 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={risk.is_modified}
                        onChange={(e) => setRisk({ ...risk, is_modified: e.target.checked })}
                        className="w-4 h-4 rounded"
                        style={{ accentColor: '#FF6B4A' }}
                      />
                      <span className="text-sm" style={{ color: '#7F8C8D' }}>Modified Vehicle</span>
                    </label>
                  </div>
                </div>

                {/* Registration Summary */}
                <div
                  className="p-5 rounded-lg border"
                  style={{ borderColor: '#E5E7EB', backgroundColor: '#F8F9FA' }}
                >
                  <h4 className="font-semibold mb-4" style={{ color: '#2C3E50' }}>
                    Registration Summary
                  </h4>
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <p className="text-xs mb-1" style={{ color: '#7F8C8D' }}>Customer</p>
                      <p className="font-medium" style={{ color: '#2C3E50' }}>
                        {ph.first_name || '—'} {ph.last_name}
                      </p>
                    </div>
                    <div>
                      <p className="text-xs mb-1" style={{ color: '#7F8C8D' }}>Email</p>
                      <p className="font-medium" style={{ color: '#2C3E50' }}>
                        {ph.email || '—'}
                      </p>
                    </div>
                    <div>
                      <p className="text-xs mb-1" style={{ color: '#7F8C8D' }}>Vehicle</p>
                      <p className="font-medium" style={{ color: '#2C3E50' }}>
                        {veh.manufacture_year} {veh.make} {veh.model}
                      </p>
                    </div>
                    <div>
                      <p className="text-xs mb-1" style={{ color: '#7F8C8D' }}>Registration No.</p>
                      <p className="font-medium" style={{ color: '#2C3E50' }}>
                        {veh.registration_number || '—'}
                      </p>
                    </div>
                    <div>
                      <p className="text-xs mb-1" style={{ color: '#7F8C8D' }}>City</p>
                      <p className="font-medium" style={{ color: '#2C3E50' }}>
                        {ph.city}, {ph.country}
                      </p>
                    </div>
                    <div>
                      <p className="text-xs mb-1" style={{ color: '#7F8C8D' }}>Credit Score (Est.)</p>
                      <p className="font-medium" style={{ color: scoreInfo.color }}>
                        {calculatedCreditScore} — {scoreInfo.label}
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* ── Navigation Buttons ───────────────────────────────────────── */}
            <div
              className="flex justify-between mt-8 pt-6 border-t"
              style={{ borderColor: '#E5E7EB' }}
            >
              <button
                type="button"
                onClick={handleBack}
                disabled={currentStep === 1}
                className="flex items-center px-6 py-2.5 rounded-lg font-medium transition-colors disabled:opacity-40"
                style={{ backgroundColor: '#F8F9FA', color: '#7F8C8D' }}
              >
                <ChevronLeft className="w-5 h-5 mr-1" />
                Back
              </button>

              {currentStep < 5 ? (
                <button
                  type="button"
                  onClick={handleNext}
                  className="flex items-center px-6 py-2.5 rounded-lg text-white font-medium transition-colors"
                  style={{ backgroundColor: '#FF6B4A' }}
                  onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = '#E55A3A')}
                  onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = '#FF6B4A')}
                >
                  Next
                  <ChevronRight className="w-5 h-5 ml-1" />
                </button>
              ) : (
                <button
                  type="button"
                  onClick={handleSubmit}
                  disabled={isSubmitting}
                  className="flex items-center px-8 py-2.5 rounded-lg text-white font-medium transition-colors disabled:opacity-60"
                  style={{ backgroundColor: '#FF6B4A' }}
                  onMouseEnter={(e) =>
                    !isSubmitting && (e.currentTarget.style.backgroundColor = '#E55A3A')
                  }
                  onMouseLeave={(e) =>
                    !isSubmitting && (e.currentTarget.style.backgroundColor = '#FF6B4A')
                  }
                >
                  {isSubmitting ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2" />
                      Registering…
                    </>
                  ) : (
                    <>
                      <Check className="w-5 h-5 mr-2" />
                      Complete Registration
                    </>
                  )}
                </button>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}