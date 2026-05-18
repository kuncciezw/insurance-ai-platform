import { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useNotification } from './notifications/useNotification';
import { Shield, Eye, EyeOff } from 'lucide-react';
import { api } from '../services/api';

export default function Login() {
  const navigate = useNavigate();
  const { login } = useAuth();
  const { showNotification, NotificationContainer } = useNotification();
  const [formData, setFormData] = useState({
    username: '',
    password: '',
  });
  const [isLoading, setIsLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  // New state for branding and carousel
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
    // Image carousel interval
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

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);

    try {
      await login(formData.username, formData.password);
      showNotification('Login successful!', 'success');
      navigate('/dashboard');
    } catch (err) {
      if (err.status === 403) {
        if (err.data?.status === 'pending_approval' || err.message.includes('pending approval')) {
          showNotification(
            'Your account is pending approval. An administrator will review your application shortly.',
            'warning'
          );
        } else {
          showNotification(err.message || 'Account is disabled. Please contact support.', 'error');
        }
      } else if (err.status === 401) {
        showNotification('Invalid username or password', 'error');
      } else if (err.status === 0 || err.message.includes('fetch')) {
        showNotification('Unable to connect to server. Please check your connection.', 'error');
      } else if (err.status === 500) {
        showNotification('Server error. Please try again later.', 'error');
      } else {
        showNotification(err.message || 'Login failed. Please try again.', 'error');
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
      <div className="w-full md:w-[40%] h-full flex flex-col justify-center p-8 lg:p-12 xl:p-16 relative overflow-y-auto shadow-2xl z-10 bg-white">
        <div className="w-full max-w-md mx-auto space-y-8">
          {/* Header */}
          <div className="text-center md:text-left">
            <div className="flex justify-center md:justify-start mb-6">
              <div
                className="w-14 h-14 rounded-2xl flex items-center justify-center shadow-lg transition-all"
                style={{ backgroundColor: secondaryColor }}
              >
                <Shield className="w-7 h-7 text-white" />
              </div>
            </div>
            <h2 className="text-3xl lg:text-4xl font-extrabold tracking-tight" style={{ color: secondaryColor }}>
              {companyProfile ? companyProfile.company_name : 'Loading...'}
            </h2>
            <p className="mt-2 text-base font-medium" style={{ color: '#7F8C8D' }}>
              {companyProfile ? companyProfile.company_tagline : ''}
            </p>
          </div>

          {/* Form */}
          <div className="bg-[#F8F9FA] rounded-3xl shadow-sm p-6 lg:p-10 border border-slate-100">
            <form onSubmit={handleSubmit} className="space-y-6">
              <div>
                <label
                  htmlFor="username"
                  className="block text-xs font-bold tracking-wider uppercase mb-2"
                  style={{ color: secondaryColor }}
                >
                  Username
                </label>
                <input
                  id="username"
                  name="username"
                  type="text"
                  autoComplete="username"
                  required
                  value={formData.username}
                  onChange={handleChange}
                  className="w-full px-5 py-4 rounded-2xl border-2 transition-colors focus:outline-none focus:ring-0 focus:bg-white text-base font-medium"
                  style={{
                    borderColor: '#E5E7EB',
                    backgroundColor: '#F8F9FA',
                  }}
                  onFocus={(e) => {
                    e.target.style.borderColor = primaryColor;
                    e.target.style.backgroundColor = 'white';
                  }}
                  onBlur={(e) => {
                    e.target.style.borderColor = '#E5E7EB';
                    e.target.style.backgroundColor = '#F8F9FA';
                  }}
                />
              </div>

              <div>
                <label
                  htmlFor="password"
                  className="block text-xs font-bold tracking-wider uppercase mb-2"
                  style={{ color: secondaryColor }}
                >
                  Password
                </label>
                <div className="relative">
                  <input
                    id="password"
                    name="password"
                    type={showPassword ? "text" : "password"}
                    autoComplete="current-password"
                    required
                    value={formData.password}
                    onChange={handleChange}
                    className="w-full px-5 py-4 rounded-2xl border-2 transition-colors focus:outline-none focus:ring-0 focus:bg-white text-base font-medium pr-12"
                    style={{
                      borderColor: '#E5E7EB',
                      backgroundColor: '#F8F9FA',
                    }}
                    onFocus={(e) => {
                      e.target.style.borderColor = primaryColor;
                      e.target.style.backgroundColor = 'white';
                    }}
                    onBlur={(e) => {
                      e.target.style.borderColor = '#E5E7EB';
                      e.target.style.backgroundColor = '#F8F9FA';
                    }}
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 transform -translate-y-1/2 p-2 rounded-xl hover:bg-slate-200 transition-colors"
                    style={{ color: '#7F8C8D' }}
                  >
                    {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                  </button>
                </div>
              </div>

              <div className="pt-2">
                <button
                  type="submit"
                  disabled={isLoading}
                  className="w-full py-4 px-4 rounded-2xl text-white font-bold text-lg transition-transform hover:-translate-y-0.5 active:translate-y-0 disabled:opacity-70 disabled:cursor-not-allowed disabled:transform-none"
                  style={{ 
                    backgroundColor: primaryColor,
                    boxShadow: `0 8px 20px -4px ${primaryColor}80` // Dynamic shadow based on primary color
                  }}
                >
                  {isLoading ? 'Signing in...' : 'Sign in'}
                </button>
              </div>
            </form>

            <div className="mt-8 text-center">
              <p className="text-sm font-medium" style={{ color: '#7F8C8D' }}>
                Don't have an account?{' '}
                <Link
                  to="/register"
                  className="font-bold hover:underline transition-all"
                  style={{ color: primaryColor }}
                >
                  Register Here
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
            {/* Dark Gradient Overlay for text readability */}
            <div className="absolute inset-0 bg-gradient-to-t from-slate-900/95 via-slate-900/40 to-transparent" />
          </div>
        ))}

        {/* Carousel Content */}
        <div className="relative z-20 w-full h-full flex flex-col justify-end p-12 lg:p-24 pb-20">
          <div 
            key={currentImageIndex} 
            className="animate-in fade-in slide-in-from-bottom-8 duration-1000"
          >
            <div 
              className="inline-block px-4 py-1.5 mb-6 rounded-full text-xs font-bold tracking-wider text-white uppercase backdrop-blur-md bg-white/20 border border-white/30 shadow-lg"
            >
              Enterprise Solution
            </div>
            <h1 className="text-4xl lg:text-6xl xl:text-7xl font-extrabold text-white mb-6 drop-shadow-xl leading-tight">
              {overlayTexts[currentImageIndex]}
            </h1>
            <p className="text-lg lg:text-xl text-slate-200 max-w-xl drop-shadow-lg font-medium leading-relaxed">
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