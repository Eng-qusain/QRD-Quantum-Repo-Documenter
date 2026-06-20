// utils/apiClient.ts
import axios from 'axios';

let _port = 8765;

// Allow dynamic port resolution from Electron
if (typeof window !== 'undefined' && window.electron) {
  window.electron.getBackendPort().then((p) => { if (p) _port = p; });
}

export const apiClient = axios.create({
  baseURL: `http://localhost:${_port}`,
  timeout: 120_000,
  headers: { 'Content-Type': 'application/json' },
});

apiClient.interceptors.request.use((config) => {
  config.baseURL = `http://localhost:${_port}`;
  return config;
});

apiClient.interceptors.response.use(
  (res) => res,
  (err) => {
    const msg = err.response?.data?.detail || err.message || 'Request failed';
    return Promise.reject(new Error(msg));
  }
);
