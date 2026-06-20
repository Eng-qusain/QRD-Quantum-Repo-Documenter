// ─── uiSlice.ts ──────────────────────────────────────────────────────────────
import { createSlice, PayloadAction } from '@reduxjs/toolkit';

interface UIState {
  theme: 'light' | 'dark';
  sidebarCollapsed: boolean;
  activeTab: string;
  notifications: Notification[];
  updateAvailable: boolean;
  updateDownloaded: boolean;
  backendStatus: 'connected' | 'disconnected' | 'error';
}

interface Notification {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info';
  message: string;
  timestamp: number;
}

const initialState: UIState = {
  theme: 'dark',
  sidebarCollapsed: false,
  activeTab: 'dashboard',
  notifications: [],
  updateAvailable: false,
  updateDownloaded: false,
  backendStatus: 'disconnected',
};

export const uiSlice = createSlice({
  name: 'ui',
  initialState,
  reducers: {
    setTheme: (state, action: PayloadAction<'light' | 'dark'>) => {
      state.theme = action.payload;
      window.electron?.storeSet('theme', action.payload);
    },
    toggleTheme: (state) => {
      state.theme = state.theme === 'dark' ? 'light' : 'dark';
      window.electron?.storeSet('theme', state.theme);
    },
    setSidebarCollapsed: (state, action: PayloadAction<boolean>) => {
      state.sidebarCollapsed = action.payload;
    },
    setActiveTab: (state, action: PayloadAction<string>) => {
      state.activeTab = action.payload;
    },
    addNotification: (state, action: PayloadAction<Omit<Notification, 'id' | 'timestamp'>>) => {
      state.notifications.push({
        ...action.payload,
        id: Math.random().toString(36).slice(2),
        timestamp: Date.now(),
      });
    },
    removeNotification: (state, action: PayloadAction<string>) => {
      state.notifications = state.notifications.filter((n) => n.id !== action.payload);
    },
    setUpdateAvailable: (state, action: PayloadAction<boolean>) => {
      state.updateAvailable = action.payload;
    },
    setUpdateDownloaded: (state, action: PayloadAction<boolean>) => {
      state.updateDownloaded = action.payload;
    },
    setBackendStatus: (state, action: PayloadAction<UIState['backendStatus']>) => {
      state.backendStatus = action.payload;
    },
  },
});

export const {
  setTheme,
  toggleTheme,
  setSidebarCollapsed,
  setActiveTab,
  addNotification,
  removeNotification,
  setUpdateAvailable,
  setUpdateDownloaded,
  setBackendStatus,
} = uiSlice.actions;

export default uiSlice.reducer;
