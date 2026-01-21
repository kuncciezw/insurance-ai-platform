import { createContext, useContext, useState, useEffect, useRef, useCallback } from 'react';
import { api } from '../services/api';

const AuthContext = createContext(undefined);

// Inactivity timeout: 10 minutes (600000ms)
const INACTIVITY_TIMEOUT = 10 * 60 * 1000;
// Warning before logout: 1 minute before timeout (540000ms)
const WARNING_TIME = 9 * 60 * 1000;

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [permissions, setPermissions] = useState({});
  const [isLoading, setIsLoading] = useState(true);
  
  const inactivityTimerRef = useRef(null);
  const warningTimerRef = useRef(null);
  const lastActivityRef = useRef(Date.now());
  const warningShownRef = useRef(false);
  const isInitializedRef = useRef(false);

  // Clear all timers
  const clearTimers = useCallback(() => {
    if (inactivityTimerRef.current) {
      clearTimeout(inactivityTimerRef.current);
      inactivityTimerRef.current = null;
    }
    if (warningTimerRef.current) {
      clearTimeout(warningTimerRef.current);
      warningTimerRef.current = null;
    }
    warningShownRef.current = false;
  }, []);

  // Handle automatic logout due to inactivity
  const handleInactivityLogout = useCallback(async () => {
    clearTimers();
    
    try {
      await api.logout();
    } catch (error) {
      console.error('Logout failed:', error);
    } finally {
      setUser(null);
      setPermissions({});
      // Redirect to login with message
      window.location.href = '/login?reason=inactivity';
    }
  }, [clearTimers]);

  // Reset inactivity timer
  const resetInactivityTimer = useCallback(() => {
    if (!user) return;

    lastActivityRef.current = Date.now();
    warningShownRef.current = false;
    clearTimers();

    // Set warning timer (9 minutes)
    warningTimerRef.current = setTimeout(() => {
      if (!warningShownRef.current) {
        warningShownRef.current = true;
        window.dispatchEvent(new CustomEvent('inactivity-warning'));
      }
    }, WARNING_TIME);

    // Set logout timer (10 minutes)
    inactivityTimerRef.current = setTimeout(() => {
      handleInactivityLogout();
    }, INACTIVITY_TIMEOUT);
  }, [user, clearTimers, handleInactivityLogout]);

  // Handle user activity
  const handleActivity = useCallback(() => {
    if (user) {
      resetInactivityTimer();
    }
  }, [user, resetInactivityTimer]);

  // Keep me active (when user responds to warning)
  const stayActive = useCallback(() => {
    resetInactivityTimer();
  }, [resetInactivityTimer]);

  // Restore session on mount
  useEffect(() => {
    const restoreSession = async () => {
      // Prevent multiple initializations
      if (isInitializedRef.current) {
        return;
      }
      isInitializedRef.current = true;

      try {
        const storedUser = localStorage.getItem('user');
        const accessToken = api.getAccessToken();
        const refreshToken = localStorage.getItem('refresh_token');
        
        console.log('🔍 Checking stored session:', {
          hasUser: !!storedUser,
          hasAccessToken: !!accessToken,
          hasRefreshToken: !!refreshToken
        });

        if (storedUser && accessToken && refreshToken) {
          try {
            // Verify token is still valid by making a test request
            try {
              const currentUser = await api.getCurrentUser();
              console.log('✅ Session restored successfully');
              setUser(currentUser);
              setPermissions(currentUser.permissions || {});
            } catch (verifyError) {
              console.log('⚠️ Token verification failed, attempting refresh...');
              
              // Try to refresh the token
              const refreshed = await api.refreshAccessToken();
              if (refreshed) {
                const currentUser = await api.getCurrentUser();
                console.log('✅ Session restored after token refresh');
                setUser(currentUser);
                setPermissions(currentUser.permissions || {});
              } else {
                console.log('❌ Token refresh failed, clearing session');
                api.clearTokens();
              }
            }
          } catch (parseError) {
            console.error('Failed to parse stored user:', parseError);
            api.clearTokens();
          }
        } else {
          console.log('ℹ️ No stored session found');
        }
      } catch (error) {
        console.error('Session restoration error:', error);
        api.clearTokens();
      } finally {
        setIsLoading(false);
      }
    };

    restoreSession();
  }, []); // Empty dependency array - only run once on mount

  // Start inactivity tracking after user is set
  useEffect(() => {
    if (user && !isLoading) {
      resetInactivityTimer();
    }
  }, [user, isLoading, resetInactivityTimer]);

  // Set up activity listeners
  useEffect(() => {
    if (!user) return;

    const events = ['mousedown', 'keydown', 'scroll', 'touchstart', 'click'];
    
    events.forEach(event => {
      document.addEventListener(event, handleActivity, { passive: true });
    });

    return () => {
      events.forEach(event => {
        document.removeEventListener(event, handleActivity);
      });
      clearTimers();
    };
  }, [user, handleActivity, clearTimers]);

  const login = async (username, password) => {
    try {
      const response = await api.login(username, password);
      setUser(response.user);
      setPermissions(response.user.permissions || {});
      console.log('✅ Login successful');
    } catch (error) {
      console.error('❌ Login failed:', error);
      throw error;
    }
  };

  const register = async (data) => {
    try {
      const response = await api.register(data);
      setUser(response.user);
      setPermissions(response.user.permissions || {});
      console.log('✅ Registration successful');
    } catch (error) {
      console.error('❌ Registration failed:', error);
      throw error;
    }
  };

  const logout = async () => {
    clearTimers();
    try {
      await api.logout();
      console.log('✅ Logout successful');
    } catch (error) {
      console.error('❌ Logout failed:', error);
    } finally {
      setUser(null);
      setPermissions({});
    }
  };

  // Permission check helpers
  const hasPermission = useCallback((permission) => {
    return permissions[permission] === true;
  }, [permissions]);

  const hasRole = useCallback((roles) => {
    if (!user || !user.role) return false;
    if (Array.isArray(roles)) {
      return roles.includes(user.role);
    }
    return user.role === roles;
  }, [user]);

  const isAdmin = useCallback(() => {
    return hasRole(['SUPER_ADMIN', 'ADMIN']);
  }, [hasRole]);

  const isSuperAdmin = useCallback(() => {
    return hasRole('SUPER_ADMIN');
  }, [hasRole]);

  return (
    <AuthContext.Provider
      value={{
        user,
        permissions,
        isAuthenticated: !!user,
        loading: isLoading,
        login,
        register,
        logout,
        hasPermission,
        hasRole,
        isAdmin,
        isSuperAdmin,
        stayActive,
        handleInactivityLogout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}