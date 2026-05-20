const API_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000/api';

class ApiService {
  constructor() {
    this.baseURL = API_URL;
    this.accessToken = localStorage.getItem('access_token');
    this.refreshToken = localStorage.getItem('refresh_token');
    this.isRefreshing = false;
    this.refreshSubscribers = [];
  }

  getAccessToken() {
    return this.accessToken;
  }

  setTokens(access, refresh) {
    this.accessToken = access;
    this.refreshToken = refresh;
    localStorage.setItem('access_token', access);
    localStorage.setItem('refresh_token', refresh);
  }

  clearTokens() {
    this.accessToken = null;
    this.refreshToken = null;
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
  }

  onRefreshed(token) {
    this.refreshSubscribers.forEach(callback => callback(token));
    this.refreshSubscribers = [];
  }

  addRefreshSubscriber(callback) {
    this.refreshSubscribers.push(callback);
  }

  async refreshAccessToken() {
    if (this.isRefreshing) {
      return new Promise((resolve) => {
        this.addRefreshSubscriber((token) => {
          resolve(!!token);
        });
      });
    }

    this.isRefreshing = true;

    try {
      console.log('🔄 Refreshing access token...');
      const response = await fetch(`${this.baseURL}/dashboard/auth/token/refresh/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ refresh: this.refreshToken }),
      });

      if (!response.ok) {
        console.log('🔴 Token refresh failed, clearing tokens');
        this.clearTokens();
        this.isRefreshing = false;
        this.onRefreshed(null);
        return false;
      }

      const data = await response.json();
      console.log('✅ Token refreshed successfully');
      
      this.setTokens(data.access, this.refreshToken);
      this.isRefreshing = false;
      this.onRefreshed(data.access);
      
      return true;
    } catch (error) {
      console.error('❌ Token refresh error:', error);
      this.clearTokens();
      this.isRefreshing = false;
      this.onRefreshed(null);
      return false;
    }
  }

  async request(endpoint, options = {}) {
    const normalizedEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
    const url = `${this.baseURL}${normalizedEndpoint}`;
    const isFormData = options.body instanceof FormData;
    const headers = {
      ...(isFormData ? {} : { 'Content-Type': 'application/json' }),
      ...options.headers,
    };

    if (this.accessToken) {
      headers['Authorization'] = `Bearer ${this.accessToken}`;
    }

    console.log('🔵 API Request:', {
      url,
      method: options.method || 'GET',
      hasAuth: !!this.accessToken,
      isFormData
    });

    try {
      const response = await fetch(url, {
        ...options,
        headers,
      });

      console.log('🟢 API Response:', {
        status: response.status,
        statusText: response.statusText
      });

      if (response.status === 401 && this.refreshToken && !options._retry) {
        console.log('🔄 Attempting token refresh...');
        const refreshed = await this.refreshAccessToken();
        
        if (refreshed) {
          return this.request(endpoint, { ...options, _retry: true });
        } else {
          window.location.href = '/login?reason=session_expired';
          throw new Error('Session expired. Please log in again.');
        }
      }

      return this.handleResponse(response);
    } catch (error) {
      console.error('🔴 API request failed:', error);
      
      if (error instanceof TypeError && error.message.includes('fetch')) {
        const networkError = new Error('Unable to connect to server. Please check your internet connection.');
        networkError.status = 0;
        networkError.isNetworkError = true;
        throw networkError;
      }
      
      throw error;
    }
  }

  async handleResponse(response) {
    const contentType = response.headers.get('content-type');
    const isJson = contentType && contentType.includes('application/json');
    
    let data;
    try {
      data = isJson ? await response.json() : await response.text();
    } catch (parseError) {
      data = { detail: 'Invalid response from server' };
    }

    console.log('📦 Response Data:', data);

    if (!response.ok) {
      let errorMessage = 'An error occurred';
      
      if (typeof data === 'string') {
        errorMessage = data;
      } else if (data.detail) {
        errorMessage = data.detail;
      } else if (data.message) {
        errorMessage = data.message;
      } else if (data.error) {
        errorMessage = data.error;
      } else if (data.non_field_errors) {
        errorMessage = Array.isArray(data.non_field_errors) 
          ? data.non_field_errors.join(', ') 
          : data.non_field_errors;
      } else if (typeof data === 'object') {
        const firstErrorEntry = Object.entries(data).find(([key, v]) => v);
        if (firstErrorEntry) {
          const [field, value] = firstErrorEntry;
          const errorText = Array.isArray(value) ? value[0] : value;
          errorMessage = `${field}: ${errorText}`;
        }
      }

      const statusMessages = {
        400: 'Invalid request. Please check your input.',
        401: 'Authentication failed. Please log in again.',
        403: 'You do not have permission to perform this action.',
        404: 'The requested resource was not found.',
        409: 'This action conflicts with existing data.',
        422: 'Invalid data provided. Please check your input.',
        429: 'Too many requests. Please try again later.',
        500: 'Server error. Please try again later.',
        502: 'Server is temporarily unavailable.',
        503: 'Service is currently unavailable. Please try again later.',
      };

      if (errorMessage === 'An error occurred' && statusMessages[response.status]) {
        errorMessage = statusMessages[response.status];
      }

      const error = new Error(errorMessage);
      error.status = response.status;
      error.data = data;
      
      console.error('❌ API Error:', {
        status: response.status,
        message: errorMessage
      });
      
      throw error;
    }

    return data;
  }

  // Auth endpoints
  async login(username, password) {
    console.log('🔐 Attempting login for:', username);
    const data = await this.request('/dashboard/auth/login/', {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    });
    this.setTokens(data.tokens.access, data.tokens.refresh);
    localStorage.setItem('user', JSON.stringify(data.user));
    return data;
  }

  async register(userData) {
    console.log('📝 Attempting registration');
    const data = await this.request('/dashboard/auth/register/', {
      method: 'POST',
      body: JSON.stringify(userData),
    });
    this.setTokens(data.tokens.access, data.tokens.refresh);
    localStorage.setItem('user', JSON.stringify(data.user));
    return data;
  }

  async logout() {
    if (this.refreshToken) {
      try {
        await this.request('/dashboard/auth/logout/', {
          method: 'POST',
          body: JSON.stringify({ refresh_token: this.refreshToken }),
        });
      } catch (error) {
        console.error('Logout error:', error);
      }
    }
    this.clearTokens();
  }

  async getCurrentUser() {
    return await this.request('/dashboard/auth/profile/');
  }

  // User Management
  async getUsers(params = {}) {
    const queryString = new URLSearchParams(params).toString();
    return this.request(`/dashboard/users/${queryString ? `?${queryString}` : ''}`);
  }

  async createUser(data) {
    return this.request('/dashboard/users/', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async updateUser(id, data) {
    return this.request(`/dashboard/users/${id}/`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async deleteUser(id) {
    return this.request(`/dashboard/users/${id}/`, {
      method: 'DELETE',
    });
  }

  // Company Profile
  async getCompanyProfile() {
    return this.request('/dashboard/company-profile/');
  }

  async updateCompanyProfile(data) {
    return this.request('/dashboard/company-profile/', {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }
  
  // Roles & Permissions
  async getRoles() {
    return this.request('/dashboard/roles/permissions/');
  }

  async getPermissions() {
    return this.request('/dashboard/roles/permissions/');
  }

  async updateRolePermission(roleId, permissionId, value) {
    return this.request(`/dashboard/roles/${roleId}/permissions/`, {
      method: 'PUT',
      body: JSON.stringify({ [permissionId]: value }),
    });
  }

  async resetRolePermissions(roleId) {
    return this.request(`/dashboard/roles/${roleId}/permissions/reset/`, {
      method: 'POST',
    });
  }

  async getPermissionAuditLog(params = {}) {
    const queryString = new URLSearchParams(params).toString();
    return this.request(`/dashboard/roles/permissions/audit/${queryString ? `?${queryString}` : ''}`);
  }

  async bulkUpdatePermissions(data) {
    return this.request('/dashboard/roles/permissions/bulk/', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }
  
  // Dashboard
  async getDashboardStats() {
    return this.request('/dashboard/statistics/');
  }

  async getRecentActivity() {
    return this.request('/dashboard/activity/');
  }

  async getClaimsActivity(period = '12months') {
    return await this.request(`/dashboard/activity/?period=${period}`);
  }

  async getFraudStats(period = '30days') {
    return await this.request(`/fraud-detection/stats/?period=${period}`);
  }

  // Global Pricing Settings
  async getGlobalPricingSettings() {
    return this.request('/system-settings/pricing/');
  }

  async updateGlobalPricingSettings(data) {
    return this.request('/system-settings/pricing/', {
      method: 'PATCH',
      body: JSON.stringify(data),
    });
  }


  // Policyholders — supports ?search=&page_size= for server-side searching
  async getPolicyholders(params = {}) {
    const queryString = new URLSearchParams(params).toString();
    const data = await this.request(
      `/fraud-detection/policyholders/${queryString ? `?${queryString}` : ''}`
    );
    return data.results ? data : { results: data };
  }

  async getPolicyholder(id) {
    return this.request(`/fraud-detection/policyholders/${id}/`);
  }

  async createPolicyholder(data) {
    return this.request('/fraud-detection/policyholders/', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async updatePolicyholder(id, data) {
    return this.request(`/fraud-detection/policyholders/${id}/`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async deletePolicyholder(id) {
    return this.request(`/fraud-detection/policyholders/${id}/`, {
      method: 'DELETE',
    });
  }

  // Vehicles — supports ?search=&policyholder= for server-side searching
  async getVehicles(params = {}) {
    const queryString = new URLSearchParams(params).toString();
    return this.request(
      `/fraud-detection/vehicles/${queryString ? `?${queryString}` : ''}`
    );
  }

  async getVehicle(id) {
    return this.request(`/fraud-detection/vehicles/${id}/`);
  }

  async createVehicle(data) {
    return this.request('/fraud-detection/vehicles/', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async updateVehicle(id, data) {
    return this.request(`/fraud-detection/vehicles/${id}/`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async deleteVehicle(id) {
    return this.request(`/fraud-detection/vehicles/${id}/`, {
      method: 'DELETE',
    });
  }

  // Policies
  async getPolicies(params = {}) {
    const queryString = new URLSearchParams(params).toString();
    return this.request(`/fraud-detection/policies/${queryString ? `?${queryString}` : ''}`);
  }

  async getPolicy(id) {
    return this.request(`/fraud-detection/policies/${id}/`);
  }

  async createPolicy(data) {
    return this.request('/fraud-detection/policies/', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async updatePolicy(id, data) {
    return this.request(`/fraud-detection/policies/${id}/`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async deletePolicy(id) {
    return this.request(`/fraud-detection/policies/${id}/`, {
      method: 'DELETE',
    });
  }

  // Claims
  async getClaims(params = {}) {
    const queryString = new URLSearchParams(params).toString();
    return this.request(`/fraud-detection/claims/${queryString ? `?${queryString}` : ''}`);
  }

  async getClaim(id) {
    return this.request(`/fraud-detection/claims/${id}/`);
  }

  async autoProcessClaim(claimId) {
    return await this.request(`/claims-automation/claims/${claimId}/auto-process/`, {
      method: 'POST',
    });
  }

  async createClaim(data) {
    const isFormData = data instanceof FormData;
    return this.request('/fraud-detection/claims/', {
      method: 'POST',
      body: isFormData ? data : JSON.stringify(data),
    });
  }

  async updateClaim(id, data) {
    const isFormData = data instanceof FormData;
    return this.request(`/fraud-detection/claims/${id}/`, {
      method: 'PATCH', // (PATCH is correct based on your existing code)
      body: isFormData ? data : JSON.stringify(data),
    });
  }

  async deleteClaim(id) {
    return this.request(`/fraud-detection/claims/${id}/`, {
      method: 'DELETE',
    });
  }

  async processClaim(id) {
    return this.request(`/fraud-detection/claims/${id}/process/`, {
      method: 'POST',
    });
  }

  // Fraud Detection
  async detectFraud(claimData) {
    return this.request('/fraud-detection/fraud/analyze-claim/', {
      method: 'POST',
      body: JSON.stringify(claimData),
    });
  }

  async getFraudHistory(params = {}) {
    const queryString = new URLSearchParams(params).toString();
    return this.request(`/fraud-detection/fraud/history/${queryString ? `?${queryString}` : ''}`);
  }

  // Premium Calculator
  async calculatePremium(data) {
    return this.request('/dynamic-pricing/calculate-premium/', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async estimateClaimDirect(data) {
    return this.request('/claims-automation/estimate-cost-direct/', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  // Claims Estimator
  async estimateClaim(data) {
    return this.request('/claims-automation/estimate-cost/', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }
}

export const api = new ApiService();