import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useNotification } from './notifications/useNotification';
import { Shield, Eye, EyeOff, Clock } from 'lucide-react';

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

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);

    try {
      await login(formData.username, formData.password);
      showNotification('Login successful!', 'success');
      navigate('/dashboard');
    } catch (err) {
      // Handle specific error types
      if (err.status === 403) {
        // Check if it's a pending approval status
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

  return (
    <div className="min-h-screen flex items-center justify-center px-4" style={{ backgroundColor: '#F8F9FA' }}>
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
            Sign in to your account
          </p>
        </div>

        <div
          className="rounded-lg shadow-lg p-8"
          style={{ backgroundColor: 'white' }}
        >
          <form onSubmit={handleSubmit} className="space-y-6">
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
                autoComplete="username"
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
                  autoComplete="current-password"
                  required
                  value={formData.password}
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
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 transform -translate-y-1/2 p-1 rounded hover:bg-gray-100"
                  style={{ color: '#7F8C8D' }}
                >
                  {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                </button>
              </div>
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
              {isLoading ? 'Signing in...' : 'Sign in'}
            </button>
          </form>

          <div className="mt-6 text-center">
            <p style={{ color: '#7F8C8D' }}>
              Don't have an account?{' '}
              <Link
                to="/register"
                className="font-medium"
                style={{ color: '#FF6B4A' }}
              >
                Register
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}