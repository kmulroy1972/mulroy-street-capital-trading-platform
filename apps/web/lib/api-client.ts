import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'https://mulroystreetcap.com/api';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token if exists
apiClient.interceptors.request.use((config) => {
  if (typeof window !== 'undefined') {
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

// API functions
export const api = {
  // MSC API endpoints
  getHealth: () => apiClient.get('/health'),
  getAccount: () => apiClient.get('/account'),
  getPositions: () => apiClient.get('/positions'),
  getOrders: (limit: number = 25) => 
    apiClient.get('/orders', { params: { limit } }),
  getMarketClock: () => apiClient.get('/clock'),
  
  // Admin endpoints
  getStrategies: () => apiClient.get('/api/strategies'),
  toggleStrategy: (name: string, status: string) =>
    apiClient.put(`/api/strategies/${name}/toggle`, status),
  getConfig: () => apiClient.get('/api/config'),
  updateConfig: (config: Record<string, unknown>) => apiClient.put('/api/config', config),
  flattenAll: () => apiClient.post('/api/controls/flatten_all'),
  setTradingEnabled: (enabled: boolean) =>
    apiClient.post('/api/controls/trading_enabled', enabled),
};