import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useNotification } from './notifications/useNotification';
import { Shield, Check, X, Eye, EyeOff } from 'lucide-react';

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

  // Password validation rules
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

    // Validate password strength
    if (!isPasswordValid) {
      showNotification('Password does not meet security requirements', 'error');
      return;
    }

    // Validate password match
    if (formData.password !== formData.confirmPassword) {
      showNotification('Passwords do not match', 'error');
      return;
    }

    // Validate username length
    if (formData.username.length < 3) {
      showNotification('Username must be at least 3 characters long', 'error');
      return;
    }

    setIsLoading(true);

    try {
      const { confirmPassword, ...registerData } = formData;
      await register(registerData);
      
      // Show pending approval message
      showNotification('Application submitted successfully! Please save your login details and check back later for approval.', 'success');
      
      // Redirect to login after a delay
      setTimeout(() => {
        navigate('/login');
      }, 4000);
    } catch (err) {
      // Handle specific error types
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

  return (
    <div className="min-h-screen flex items-center justify-center px-4 py-12" style={{ backgroundColor: '#F8F9FA' }}>
      <NotificationContainer />
      <div className="max-w-md w-full space-y-8">
        <div className="text-center">
          <div className="flex justify-center mb-4">
            <div
              className="w-16 h-16 rounded-full flex items-center justify-center"
              style={{ backgroundColor: '#2C3E50' }}
            >
              <Shield className="w-8 h-8 text-white" />
            </div>
          </div>
          <h2 className="text-3xl font-bold" style={{ color: '#2C3E50' }}>
            Insurance AI Platform
          </h2>
          <p className="mt-2" style={{ color: '#7F8C8D' }}>
            Submit your registration application
          </p>
        </div>

        <div
          className="rounded-lg shadow-lg p-8"
          style={{ backgroundColor: 'white' }}
        >
          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label
                  htmlFor="first_name"
                  className="block text-sm font-medium mb-2"
                  style={{ color: '#2C3E50' }}
                >
                  First Name
                </label>
                <input
                  id="first_name"
                  name="first_name"
                  type="text"
                  value={formData.first_name}
                  onChange={handleChange}
                  className="w-full px-4 py-3 rounded-lg border focus:outline-none focus:ring-2"
                  style={{
                    borderColor: '#E5E7EB',
                    backgroundColor: '#F8F9FA',
                  }}
                  onFocus={(e) => {
                    e.target.style.borderColor = '#FF6B4A';
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
                  htmlFor="last_name"
                  className="block text-sm font-medium mb-2"
                  style={{ color: '#2C3E50' }}
                >
                  Last Name
                </label>
                <input
                  id="last_name"
                  name="last_name"
                  type="text"
                  value={formData.last_name}
                  onChange={handleChange}
                  className="w-full px-4 py-3 rounded-lg border focus:outline-none focus:ring-2"
                  style={{
                    borderColor: '#E5E7EB',
                    backgroundColor: '#F8F9FA',
                  }}
                  onFocus={(e) => {
                    e.target.style.borderColor = '#FF6B4A';
                    e.target.style.backgroundColor = 'white';
                  }}
                  onBlur={(e) => {
                    e.target.style.borderColor = '#E5E7EB';
                    e.target.style.backgroundColor = '#F8F9FA';
                  }}
                />
              </div>
            </div>

            <div>
              <label
                htmlFor="username"
                className="block text-sm font-medium mb-2"
                style={{ color: '#2C3E50' }}
              >
                Username
              </label>
              <input
                id="username"
                name="username"
                type="text"
                required
                value={formData.username}
                onChange={handleChange}
                className="w-full px-4 py-3 rounded-lg border focus:outline-none focus:ring-2"
                style={{
                  borderColor: '#E5E7EB',
                  backgroundColor: '#F8F9FA',
                }}
                onFocus={(e) => {
                  e.target.style.borderColor = '#FF6B4A';
                  e.target.style.backgroundColor = 'white';
                }}
                onBlur={(e) => {
                  e.target.style.borderColor = '#E5E7EB';
                  e.target.style.backgroundColor = '#F8F9FA';
                }}
              />
              {formData.username && formData.username.length < 3 && (
                <p className="mt-1 text-xs" style={{ color: '#DC2626' }}>
                  Username must be at least 3 characters
                </p>
              )}
            </div>

            <div>
              <label
                htmlFor="email"
                className="block text-sm font-medium mb-2"
                style={{ color: '#2C3E50' }}
              >
                Email
              </label>
              <input
                id="email"
                name="email"
                type="email"
                required
                value={formData.email}
                onChange={handleChange}
                className="w-full px-4 py-3 rounded-lg border focus:outline-none focus:ring-2"
                style={{
                  borderColor: '#E5E7EB',
                  backgroundColor: '#F8F9FA',
                }}
                onFocus={(e) => {
                  e.target.style.borderColor = '#FF6B4A';
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
                className="block text-sm font-medium mb-2"
                style={{ color: '#2C3E50' }}
              >
                Password
              </label>
              <div className="relative">
                <input
                  id="password"
                  name="password"
                  type={showPassword ? "text" : "password"}
                  required
                  value={formData.password}
                  onChange={handleChange}
                  onFocus={() => setPasswordFocused(true)}
                  onBlur={() => setPasswordFocused(false)}
                  className="w-full px-4 py-3 rounded-lg border focus:outline-none focus:ring-2 pr-12"
                  style={{
                    borderColor: '#E5E7EB',
                    backgroundColor: '#F8F9FA',
                  }}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 transform -translate-y-1/2 p-1 rounded hover:bg-gray-100"
                  style={{ color: '#7F8C8D' }}
                >
                  {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                </button>
              </div>
              
              {/* Password strength indicator */}
              {(passwordFocused || formData.password) && (
                <div className="mt-3 p-3 rounded-lg" style={{ backgroundColor: '#F8F9FA' }}>
                  <p className="text-xs font-medium mb-2" style={{ color: '#7F8C8D' }}>
                    Password must contain:
                  </p>
                  <div className="space-y-1">
                    <PasswordRequirement met={passwordValidation.minLength} text="At least 8 characters" />
                    <PasswordRequirement met={passwordValidation.hasUpper} text="One uppercase letter" />
                    <PasswordRequirement met={passwordValidation.hasLower} text="One lowercase letter" />
                    <PasswordRequirement met={passwordValidation.hasNumber} text="One number" />
                    <PasswordRequirement met={passwordValidation.hasSpecial} text="One special character (!@#$%^&*)" />
                  </div>
                </div>
              )}
            </div>

            <div>
              <label
                htmlFor="confirmPassword"
                className="block text-sm font-medium mb-2"
                style={{ color: '#2C3E50' }}
              >
                Confirm Password
              </label>
              <div className="relative">
                <input
                  id="confirmPassword"
                  name="confirmPassword"
                  type={showConfirmPassword ? "text" : "password"}
                  required
                  value={formData.confirmPassword}
                  onChange={handleChange}
                  className="w-full px-4 py-3 rounded-lg border focus:outline-none focus:ring-2 pr-12"
                  style={{
                    borderColor: '#E5E7EB',
                    backgroundColor: '#F8F9FA',
                  }}
                  onFocus={(e) => {
                    e.target.style.borderColor = '#FF6B4A';
                    e.target.style.backgroundColor = 'white';
                  }}
                  onBlur={(e) => {
                    e.target.style.borderColor = '#E5E7EB';
                    e.target.style.backgroundColor = '#F8F9FA';
                  }}
                />
                <button
                  type="button"
                  onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                  className="absolute right-3 top-1/2 transform -translate-y-1/2 p-1 rounded hover:bg-gray-100"
                  style={{ color: '#7F8C8D' }}
                >
                  {showConfirmPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                </button>
              </div>
              {formData.confirmPassword && (
                <div className="mt-2 flex items-center">
                  {passwordsMatch ? (
                    <>
                      <Check className="w-4 h-4 mr-1" style={{ color: '#10B981' }} />
                      <span className="text-xs" style={{ color: '#10B981' }}>Passwords match</span>
                    </>
                  ) : (
                    <>
                      <X className="w-4 h-4 mr-1" style={{ color: '#DC2626' }} />
                      <span className="text-xs" style={{ color: '#DC2626' }}>Passwords do not match</span>
                    </>
                  )}
                </div>
              )}
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="w-full py-3 px-4 rounded-lg text-white font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              style={{ backgroundColor: '#FF6B4A' }}
              onMouseEnter={(e) => {
                if (!isLoading) e.target.style.backgroundColor = '#E55A3A';
              }}
              onMouseLeave={(e) => {
                if (!isLoading) e.target.style.backgroundColor = '#FF6B4A';
              }}
            >
              {isLoading ? 'Submitting application...' : 'Submit Application'}
            </button>
          </form>

          <div className="mt-6 text-center">
            <p style={{ color: '#7F8C8D' }}>
              Already have an account?{' '}
              <Link
                to="/login"
                className="font-medium"
                style={{ color: '#FF6B4A' }}
              >
                Sign in
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

// Helper component for password requirements
function PasswordRequirement({ met, text }) {
  return (
    <div className="flex items-center text-xs">
      {met ? (
        <Check className="w-4 h-4 mr-2" style={{ color: '#10B981' }} />
      ) : (
        <X className="w-4 h-4 mr-2" style={{ color: '#DC2626' }} />
      )}
      <span style={{ color: met ? '#10B981' : '#7F8C8D' }}>{text}</span>
    </div>
  );
}