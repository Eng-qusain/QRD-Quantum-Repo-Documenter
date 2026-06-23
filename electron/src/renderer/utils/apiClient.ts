// utils/apiClient.ts
import axios from 'axios';
import { snakeToCamel, camelToSnake } from './caseConversion';

let _port = 8765;

// Allow dynamic port resolution from Electron
if (typeof window !== 'undefined' && window.electron) {
  window.electron.getBackendPort().then((p: number) => { if (p) _port = p; });
}

export const apiClient = axios.create({
  baseURL: `http://localhost:${_port}`,
  timeout: 120_000,
  headers: { 'Content-Type': 'application/json' },
});

apiClient.interceptors.request.use((config) => {
  config.baseURL = `http://localhost:${_port}`;

  // Convert outgoing camelCase request bodies to snake_case for FastAPI/Pydantic.
  if (config.data && typeof config.data === 'object') {
    config.data = camelToSnake(config.data);
  }
  // Query params also follow the same convention on this backend.
  if (config.params && typeof config.params === 'object') {
    config.params = camelToSnake(config.params);
  }

  return config;
});

apiClient.interceptors.response.use(
  (res) => {
    // Convert incoming snake_case JSON responses to camelCase for the frontend.
    if (res.data && typeof res.data === 'object') {
      res.data = snakeToCamel(res.data);
    }
    return res;
  },
  (err) => {
    const msg = err.response?.data?.detail || err.message || 'Request failed';
    return Promise.reject(new Error(msg));
  }
);
