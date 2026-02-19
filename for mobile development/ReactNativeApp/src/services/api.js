import axios from 'axios';
import {API_BASE_URL, endpoints} from '../config/api';

class APIService {
  constructor() {
    this.baseURL = API_BASE_URL;
    this.token = null;
    
    // Configure axios defaults
    this.client = axios.create({
      baseURL: this.baseURL,
      timeout: 10000,
      headers: {
        'Content-Type': 'application/json',
      },
    });
    
    // Request interceptor to add auth token
    this.client.interceptors.request.use(
      (config) => {
        if (this.token) {
          config.headers.Authorization = `Token ${this.token}`;
        }
        return config;
      },
      (error) => {
        return Promise.reject(error);
      }
    );
    
    // Response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401) {
          // Token expired or invalid
          this.clearToken();
          // You could trigger a logout action here
        }
        return Promise.reject(error);
      }
    );
  }

  setToken(token) {
    this.token = token;
  }

  clearToken() {
    this.token = null;
  }

  async request(endpoint, options = {}) {
    try {
      const response = await this.client({
        url: endpoint,
        ...options,
      });
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  handleError(error) {
    if (error.response) {
      // Server responded with error status
      return {
        status: error.response.status,
        message: error.response.data?.detail || error.response.data?.error || 'API Error',
        data: error.response.data,
      };
    } else if (error.request) {
      // Network error
      return {
        status: 0,
        message: 'Network error. Please check your connection.',
        data: null,
      };
    } else {
      // Other error
      return {
        status: -1,
        message: error.message || 'Unknown error occurred',
        data: null,
      };
    }
  }

  // Authentication methods
  async login(username, password) {
    return this.request(endpoints.LOGIN, {
      method: 'POST',
      data: {username, password},
    });
  }

  async logout() {
    return this.request(endpoints.LOGOUT, {
      method: 'POST',
    });
  }

  async getTokenInfo() {
    return this.request(endpoints.TOKEN_INFO);
  }

  async refreshToken() {
    return this.request(endpoints.REFRESH_TOKEN, {
      method: 'POST',
    });
  }

  // Mobile API methods
  async getDashboardSummary() {
    return this.request(endpoints.DASHBOARD);
  }

  async getServerStatus() {
    return this.request(endpoints.SERVER_STATUS);
  }

  async getNetworkDevices() {
    return this.request(endpoints.NETWORK_DEVICES);
  }

  async getAlerts(params = {}) {
    const query = new URLSearchParams(params).toString();
    return this.request(`${endpoints.ALERTS}?${query}`);
  }

  async getServerDetail(serverId) {
    return this.request(endpoints.SERVER_DETAIL(serverId));
  }

  async getServerMetrics(serverId, range = '24h') {
    const query = new URLSearchParams({range}).toString();
    return this.request(`${endpoints.SERVER_METRICS(serverId)}?${query}`);
  }

  async ingestAgentData(data) {
    return this.request(endpoints.AGENT_INGEST, {
      method: 'POST',
      data,
    });
  }
}

export default new APIService();
