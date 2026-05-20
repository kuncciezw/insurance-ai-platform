import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { CurrencyProvider } from './contexts/CurrencyContext';
import { PricingSettingsProvider } from './contexts/PricingSettingsContext';

import Login from './components/Login';
import Register from './components/Register';
import SystemSettings from './components/SystemSettings';
import Dashboard from './components/Dashboard';
import Policies from './components/Policies';
import PolicyDetail from './components/PolicyDetail';
import ClaimsList from './components/ClaimsList';
import ClaimDetail from './components/ClaimDetail';
import FraudDetection from './components/FraudDetection';
import PremiumCalculator from './components/PremiumCalculator';
import OnboardingWizard from './components/OnboardingWizard';

function ProtectedRoute({ children, permission }) {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ backgroundColor: '#F8F9FA' }}>
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-t-transparent rounded-full animate-spin mx-auto mb-4" 
               style={{ borderColor: '#FF6B4A', borderTopColor: 'transparent' }}></div>
          <p style={{ color: '#7F8C8D' }}>Loading...</p>
        </div>
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  return children;
}

function AdminRoute({ children }) {
  const { user, loading, isAdmin } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ backgroundColor: '#F8F9FA' }}>
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-t-transparent rounded-full animate-spin mx-auto mb-4" 
               style={{ borderColor: '#FF6B4A', borderTopColor: 'transparent' }}></div>
          <p style={{ color: '#7F8C8D' }}>Loading...</p>
        </div>
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  if (!isAdmin()) {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ backgroundColor: '#F8F9FA' }}>
        <div className="text-center max-w-md p-8 bg-white rounded-xl shadow-lg">
          <div className="w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4" 
               style={{ backgroundColor: '#FEE2E2' }}>
            <svg className="w-8 h-8" style={{ color: '#DC2626' }} fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          </div>
          <h2 className="text-2xl font-bold mb-2" style={{ color: '#2C3E50' }}>
            Access Denied
          </h2>
          <p className="mb-6" style={{ color: '#7F8C8D' }}>
            You don't have permission to access this page. Only Super Admin and Admin users can access this feature.
          </p>
          <button
            onClick={() => window.location.href = '/dashboard'}
            className="px-6 py-2 rounded-lg text-white font-medium transition-colors"
            style={{ backgroundColor: '#FF6B4A' }}
            onMouseEnter={(e) => e.target.style.backgroundColor = '#E55A3A'}
            onMouseLeave={(e) => e.target.style.backgroundColor = '#FF6B4A'}
          >
            Go to Dashboard
          </button>
        </div>
      </div>
    );
  }

  return children;
}

function RoleBasedRoute({ children, allowedRoles }) {
  const { user, loading, hasRole } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ backgroundColor: '#F8F9FA' }}>
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-t-transparent rounded-full animate-spin mx-auto mb-4" 
               style={{ borderColor: '#FF6B4A', borderTopColor: 'transparent' }}></div>
          <p style={{ color: '#7F8C8D' }}>Loading...</p>
        </div>
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  if (!hasRole(allowedRoles)) {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ backgroundColor: '#F8F9FA' }}>
        <div className="text-center max-w-md p-8 bg-white rounded-xl shadow-lg">
          <div className="w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4" 
               style={{ backgroundColor: '#FEE2E2' }}>
            <svg className="w-8 h-8" style={{ color: '#DC2626' }} fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          </div>
          <h2 className="text-2xl font-bold mb-2" style={{ color: '#2C3E50' }}>
            Access Denied
          </h2>
          <p className="mb-6" style={{ color: '#7F8C8D' }}>
            Your role does not have permission to access this feature.
          </p>
          <button
            onClick={() => window.location.href = '/dashboard'}
            className="px-6 py-2 rounded-lg text-white font-medium transition-colors"
            style={{ backgroundColor: '#FF6B4A' }}
            onMouseEnter={(e) => e.target.style.backgroundColor = '#E55A3A'}
            onMouseLeave={(e) => e.target.style.backgroundColor = '#FF6B4A'}
          >
            Go to Dashboard
          </button>
        </div>
      </div>
    );
  }

  return children;
}

function App() {
  return (
    <Router>
      <AuthProvider>
        <CurrencyProvider>
          <PricingSettingsProvider>
            <Routes>
              <Route path="/login" element={<Login />} />
              <Route path="/register" element={<Register />} />

              <Route
                path="/dashboard"
                element={
                  <ProtectedRoute>
                    <Dashboard />
                  </ProtectedRoute>
                }
              />

              <Route
                path="/onboarding"
                element={
                  <ProtectedRoute permission="can_create_policyholders">
                    <OnboardingWizard />
                  </ProtectedRoute>
                }
              />
              
              <Route
                path="/policies"
                element={
                  <ProtectedRoute>
                    <Policies />
                  </ProtectedRoute>
                }
              />

              <Route
                path="/policies/:id"
                element={
                  <ProtectedRoute>
                    <PolicyDetail />
                  </ProtectedRoute>
                }
              />
              
              <Route
                path="/claims"
                element={
                  <ProtectedRoute>
                    <ClaimsList />
                  </ProtectedRoute>
                }
              />

              <Route
                path="/claims/:id"
                element={
                  <ProtectedRoute>
                    <ClaimDetail />
                  </ProtectedRoute>
                }
              />
              
              <Route
                path="/fraud-detection"
                element={
                  <RoleBasedRoute allowedRoles={['SUPER_ADMIN', 'ADMIN', 'CLAIMS_ADJUSTER', 'FRAUD_INVESTIGATOR']}>
                    <FraudDetection />
                  </RoleBasedRoute>
                }
              />
              
              <Route
                path="/premium-calculator"
                element={
                  <RoleBasedRoute allowedRoles={['SUPER_ADMIN', 'ADMIN', 'UNDERWRITER']}>
                    <PremiumCalculator />
                  </RoleBasedRoute>
                }
              />

              <Route
                path="/settings"
                element={
                  <AdminRoute>
                    <SystemSettings />
                  </AdminRoute>
                }
              />

              <Route path="/" element={<Navigate to="/dashboard" replace />} />
              <Route path="*" element={<Navigate to="/dashboard" replace />} />
            </Routes>
          </PricingSettingsProvider>
        </CurrencyProvider>
      </AuthProvider>
    </Router>
  );
}

export default App;