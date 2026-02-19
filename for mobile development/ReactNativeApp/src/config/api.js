export const API_BASE_URL = 'http://10.0.2.2:8000/api';

export const endpoints = {
  // Authentication
  LOGIN: '/auth/token/',
  LOGOUT: '/auth/logout/',
  TOKEN_INFO: '/auth/token/info/',
  REFRESH_TOKEN: '/auth/token/refresh/',
  
  // Mobile API
  DASHBOARD: '/mobile/dashboard/',
  SERVER_STATUS: '/mobile/server-status/',
  NETWORK_DEVICES: '/mobile/network-devices/',
  ALERTS: '/mobile/alerts/',
  SERVER_DETAIL: (id) => `/mobile/server/${id}/`,
  SERVER_METRICS: (id) => `/mobile/server/${id}/metrics/`,
  AGENT_INGEST: '/mobile/agent/ingest/',
};
