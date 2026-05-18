import { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useNotification } from './notifications/useNotification';
import { Shield, Check, X, Eye, EyeOff } from 'lucide-react';
import { api } from '../services/api';

export default function Register() {
  const navigate = useNavigate();
  const { register } = useAuth();
  const { showNotification, NotificationContainer } = useNotification();
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    confirmPassword: '',
    first_name: '',
    last_name: '',
  });
  const [isLoading, setIsLoading] = useState(false);
  const [passwordFocused, setPasswordFocused] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  // Branding and Carousel State
  const [companyProfile, setCompanyProfile] = useState(null);
  const [currentImageIndex, setCurrentImageIndex] = useState(0);

  const carImages = [
    '/assets/car_1.jpeg',
    '/assets/car_2.jpeg',
    '/assets/car_3.jpeg'
  ];

  const overlayTexts = [
    "AI-Powered Fraud Detection",
    "Smart Claims Processing",
    "Dynamic Premium Calculation"
  ];

  useEffect(() => {
    fetchCompanyProfile();
    const interval = setInterval(() => {
      setCurrentImageIndex((prev) => (prev + 1) % carImages.length);
    }, 5000);
    return () => clearInterval(interval);
  }, []);

  const fetchCompanyProfile = async () => {
    try {
      const data = await api.getCompanyProfile();
      setCompanyProfile(data);
    } catch (err) {
      setCompanyProfile({
        company_name: 'Insurance AI Platform',
        company_tagline: 'Intelligent Operations',
        primary_color: '#FF6B4A',
        secondary_color: '#2C3E50',
      });
    }
  };

  const passwordValidation = {
    minLength: formData.password.length >= 8,
    hasUpper: /[A-Z]/.test(formData.password),
    hasLower: /[a-z]/.test(formData.password),
    hasNumber: /[0-9]/.test(formData.password),
    hasSpecial: /[!@#$%^&*(),.?":{}|<>]/.test(formData.password),
  };

  const isPasswordValid = Object.values(passwordValidation).every(v => v);
  const passwordsMatch = formData.password === formData.confirmPassword && formData.confirmPassword !== '';

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!isPasswordValid) {
      showNotification('Password does not meet security requirements', 'error');
      return;
    }
    if (formData.password !== formData.confirmPassword) {
      showNotification('Passwords do not match', 'error');
      return;
    }
    if (formData.username.length < 3) {
      showNotification('Username must be at least 3 characters long', 'error');
      return;
    }

    setIsLoading(true);

    try {
      const { confirmPassword, ...registerData } = formData;
      await register(registerData);
      
      showNotification('Application submitted successfully! Please save your login details and check back later for approval.', 'success');
      
      setTimeout(() => {
        navigate('/login');
      }, 4000);
    } catch (err) {
      if (err.status === 400) {
        if (err.message.includes('username')) {
          showNotification('Username already exists. Please choose another.', 'error');
        } else if (err.message.includes('email')) {
          showNotification('Email already registered. Please use another email.', 'error');
        } else {
          showNotification(err.message || 'Invalid registration data. Please check your inputs.', 'error');
        }
      } else if (err.status === 0 || err.message.includes('fetch')) {
        showNotification('Unable to connect to server. Please check your connection.', 'error');
      } else if (err.status === 500) {
        showNotification('Server error. Please try again later.', 'error');
      } else {
        showNotification(err.message || 'Registration failed. Please try again.', 'error');
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };

  const primaryColor = companyProfile?.primary_color || '#FF6B4A';
  const secondaryColor = companyProfile?.secondary_color || '#2C3E50';

  return (
    <div className="h-screen overflow-hidden flex flex-col md:flex-row bg-white font-sans">
      <NotificationContainer />
      
      {/* Left Area - Form (40%) */}
      <div className="w-full md:w-[40%] h-full flex flex-col justify-center p-8 lg:p-10 xl:p-12 relative overflow-y-auto shadow-2xl z-10 bg-white">
        <div className="w-full max-w-md mx-auto space-y-6">
          <div className="text-center md:text-left mt-8">
            <div className="flex justify-center md:justify-start mb-5">
              <div
                className="w-12 h-12 rounded-2xl flex items-center justify-center shadow-lg transition-all"
                style={{ backgroundColor: secondaryColor }}
              >
                <Shield className="w-6 h-6 text-white" />
              </div>
            </div>
            <h2 className="text-3xl font-extrabold tracking-tight" style={{ color: secondaryColor }}>
              Join {companyProfile ? companyProfile.company_name : 'Insurance AI'}
            </h2>
            <p className="mt-1.5 text-sm font-medium" style={{ color: '#7F8C8D' }}>
              Submit your registration application
            </p>
          </div>

          <div className="bg-[#F8F9FA] rounded-3xl shadow-sm p-6 lg:p-10 border border-slate-100 mb-8">
            <form onSubmit={handleSubmit} className="space-y-5">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label htmlFor="first_name" className="block text-[11px] uppercase tracking-wider font-bold mb-2 md:block" style={{ color: secondaryColor }}>
                    First Name
                  </label>
                  <input
                    id="first_name" name="first_name" type="text" placeholder="First Name"
                    value={formData.first_name} onChange={handleChange}
                    className="w-full px-4 py-3.5 rounded-2xl border-2 transition-colors focus:outline-none focus:ring-0 focus:bg-white text-sm font-medium"
                    style={{ borderColor: '#E5E7EB', backgroundColor: '#F8F9FA' }}
                    onFocus={(e) => { e.target.style.borderColor = primaryColor; e.target.style.backgroundColor = 'white'; }}
                    onBlur={(e) => { e.target.style.borderColor = '#E5E7EB'; e.target.style.backgroundColor = '#F8F9FA'; }}
                  />
                </div>
                <div>
                  <label htmlFor="last_name" className="block text-[11px] uppercase tracking-wider font-bold mb-2 md:block" style={{ color: secondaryColor }}>
                    Last Name
                  </label>
                  <input
                    id="last_name" name="last_name" type="text" placeholder="Last Name"
                    value={formData.last_name} onChange={handleChange}
                    className="w-full px-4 py-3.5 rounded-2xl border-2 transition-colors focus:outline-none focus:ring-0 focus:bg-white text-sm font-medium"
                    style={{ borderColor: '#E5E7EB', backgroundColor: '#F8F9FA' }}
                    onFocus={(e) => { e.target.style.borderColor = primaryColor; e.target.style.backgroundColor = 'white'; }}
                    onBlur={(e) => { e.target.style.borderColor = '#E5E7EB'; e.target.style.backgroundColor = '#F8F9FA'; }}
                  />
                </div>
              </div>

              <div>
                <label htmlFor="username" className="block text-[11px] uppercase tracking-wider font-bold mb-2 md:block" style={{ color: secondaryColor }}>
                  Username
                </label>
                <input
                  id="username" name="username" type="text" required placeholder="Username"
                  value={formData.username} onChange={handleChange}
                  className="w-full px-4 py-3.5 rounded-2xl border-2 transition-colors focus:outline-none focus:ring-0 focus:bg-white text-sm font-medium"
                  style={{ borderColor: '#E5E7EB', backgroundColor: '#F8F9FA' }}
                  onFocus={(e) => { e.target.style.borderColor = primaryColor; e.target.style.backgroundColor = 'white'; }}
                  onBlur={(e) => { e.target.style.borderColor = '#E5E7EB'; e.target.style.backgroundColor = '#F8F9FA'; }}
                />
                {formData.username && formData.username.length < 3 && (
                  <p className="mt-1.5 text-xs font-semibold text-rose-500">
                    Username must be at least 3 characters
                  </p>
                )}
              </div>

              <div>
                <label htmlFor="email" className="block text-[11px] uppercase tracking-wider font-bold mb-2 md:block" style={{ color: secondaryColor }}>
                  Email Address
                </label>
                <input
                  id="email" name="email" type="email" required placeholder="Email Address"
                  value={formData.email} onChange={handleChange}
                  className="w-full px-4 py-3.5 rounded-2xl border-2 transition-colors focus:outline-none focus:ring-0 focus:bg-white text-sm font-medium"
                  style={{ borderColor: '#E5E7EB', backgroundColor: '#F8F9FA' }}
                  onFocus={(e) => { e.target.style.borderColor = primaryColor; e.target.style.backgroundColor = 'white'; }}
                  onBlur={(e) => { e.target.style.borderColor = '#E5E7EB'; e.target.style.backgroundColor = '#F8F9FA'; }}
                />
              </div>

              <div>
                <label htmlFor="password" className="block text-[11px] uppercase tracking-wider font-bold mb-2 md:block" style={{ color: secondaryColor }}>
                  Password
                </label>
                <div className="relative">
                  <input
                    id="password" name="password" placeholder="Password"
                    type={showPassword ? "text" : "password"}
                    required
                    value={formData.password} onChange={handleChange}
                    onFocus={(e) => { setPasswordFocused(true); e.target.style.borderColor = primaryColor; e.target.style.backgroundColor = 'white'; }}
                    onBlur={(e) => { setPasswordFocused(false); e.target.style.borderColor = '#E5E7EB'; e.target.style.backgroundColor = '#F8F9FA'; }}
                    className="w-full px-4 py-3.5 rounded-2xl border-2 transition-colors focus:outline-none focus:ring-0 focus:bg-white text-sm font-medium pr-12"
                    style={{ borderColor: '#E5E7EB', backgroundColor: '#F8F9FA' }}
                  />
                  <button
                    type="button" onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 transform -translate-y-1/2 p-1.5 rounded-xl hover:bg-slate-200 transition-colors"
                    style={{ color: '#7F8C8D' }}
                  >
                    {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                  </button>
                </div>
                
                {(passwordFocused || formData.password.length > 0) && (
                  <div className="mt-3 p-4 rounded-2xl border border-slate-200 bg-white">
                    <p className="text-[11px] uppercase tracking-wider font-bold mb-2" style={{ color: secondaryColor }}>
                      Password requirements:
                    </p>
                    <div className="space-y-2">
                      <PasswordRequirement met={passwordValidation.minLength} text="At least 8 characters" />
                      <PasswordRequirement met={passwordValidation.hasUpper} text="Uppercase letter" />
                      <PasswordRequirement met={passwordValidation.hasLower} text="Lowercase letter" />
                      <PasswordRequirement met={passwordValidation.hasNumber} text="Number" />
                      <PasswordRequirement met={passwordValidation.hasSpecial} text="Special character" />
                    </div>
                  </div>
                )}
              </div>

              <div>
                <label htmlFor="confirmPassword" className="block text-[11px] uppercase tracking-wider font-bold mb-2 md:block" style={{ color: secondaryColor }}>
                  Confirm Password
                </label>
                <div className="relative">
                  <input
                    id="confirmPassword" name="confirmPassword" placeholder="Confirm Password"
                    type={showConfirmPassword ? "text" : "password"}
                    required
                    value={formData.confirmPassword} onChange={handleChange}
                    className="w-full px-4 py-3.5 rounded-2xl border-2 transition-colors focus:outline-none focus:ring-0 focus:bg-white text-sm font-medium pr-12"
                    style={{ borderColor: '#E5E7EB', backgroundColor: '#F8F9FA' }}
                    onFocus={(e) => { e.target.style.borderColor = primaryColor; e.target.style.backgroundColor = 'white'; }}
                    onBlur={(e) => { e.target.style.borderColor = '#E5E7EB'; e.target.style.backgroundColor = '#F8F9FA'; }}
                  />
                  <button
                    type="button" onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                    className="absolute right-3 top-1/2 transform -translate-y-1/2 p-1.5 rounded-xl hover:bg-slate-200 transition-colors"
                    style={{ color: '#7F8C8D' }}
                  >
                    {showConfirmPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                  </button>
                </div>
                {formData.confirmPassword && (
                  <div className="mt-2.5 flex items-center">
                    {passwordsMatch ? (
                      <>
                        <Check className="w-4 h-4 mr-1.5 text-emerald-500" />
                        <span className="text-xs font-bold text-emerald-500">Passwords match</span>
                      </>
                    ) : (
                      <>
                        <X className="w-4 h-4 mr-1.5 text-rose-500" />
                        <span className="text-xs font-bold text-rose-500">Passwords do not match</span>
                      </>
                    )}
                  </div>
                )}
              </div>

              <div className="pt-3">
                <button
                  type="submit" disabled={isLoading}
                  className="w-full py-4 px-4 rounded-2xl text-white font-bold text-base transition-transform hover:-translate-y-0.5 active:translate-y-0 disabled:opacity-70 disabled:cursor-not-allowed disabled:transform-none"
                  style={{ 
                    backgroundColor: primaryColor,
                    boxShadow: `0 8px 20px -4px ${primaryColor}80` 
                  }}
                >
                  {isLoading ? 'Submitting...' : 'Register Account'}
                </button>
              </div>
            </form>

            <div className="mt-8 text-center">
              <p className="text-sm font-medium" style={{ color: '#7F8C8D' }}>
                Already have an account?{' '}
                <Link
                  to="/login"
                  className="font-bold hover:underline transition-all"
                  style={{ color: primaryColor }}
                >
                  Sign in Here
                </Link>
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Right Area - Image Display (60%) */}
      <div className="hidden md:flex w-full md:w-[60%] h-full relative bg-slate-900 overflow-hidden">
        {carImages.map((src, idx) => (
          <div
            key={src}
            className={`absolute inset-0 transition-opacity duration-1000 ease-in-out ${
              idx === currentImageIndex ? 'opacity-100 z-10' : 'opacity-0 z-0'
            }`}
            style={{
              backgroundImage: `url(${src})`,
              backgroundSize: 'cover',
              backgroundPosition: 'center',
            }}
          >
            <div className="absolute inset-0 bg-gradient-to-t from-slate-900/95 via-slate-900/40 to-transparent" />
          </div>
        ))}

        {/* Carousel Content */}
        <div className="relative z-20 w-full h-full flex flex-col justify-end p-12 lg:p-24 pb-20">
          <div key={currentImageIndex} className="animate-in fade-in slide-in-from-bottom-8 duration-1000">
            <div className="inline-block px-4 py-1.5 mb-6 rounded-full text-xs font-bold tracking-wider text-white uppercase backdrop-blur-md bg-white/20 border border-white/30 shadow-lg">
              Enterprise Solution
            </div>
            <h1 className="text-4xl lg:text-6xl xl:text-7xl font-extrabold text-white mb-6 drop-shadow-xl leading-tight">
              {overlayTexts[currentImageIndex]}
            </h1>
            <p className="text-lg lg:text-xl text-slate-200 justify-end max-w-xl drop-shadow-lg font-medium leading-relaxed">
              Empowering the future of insurance with advanced analytics, seamless onboarding, and intelligent workflow automation.
            </p>
          </div>

          {/* Dots Indicator */}
          <div className="flex gap-3 mt-12">
            {carImages.map((_, idx) => (
              <button
                key={idx}
                onClick={() => setCurrentImageIndex(idx)}
                className={`h-1.5 rounded-full transition-all duration-500 shadow-md ${
                  idx === currentImageIndex ? 'w-12 bg-white' : 'w-4 bg-white/40 hover:bg-white/70'
                }`}
                aria-label={`Go to slide ${idx + 1}`}
              />
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

function PasswordRequirement({ met, text }) {
  return (
    <div className="flex items-center text-xs font-semibold">
      {met ? (
        <Check className="w-4 h-4 mr-2 text-emerald-500" />
      ) : (
        <X className="w-4 h-4 mr-2 text-rose-500" />
      )}
      <span className={met ? "text-emerald-500" : "text-slate-400"}>{text}</span>
    </div>
  );
}