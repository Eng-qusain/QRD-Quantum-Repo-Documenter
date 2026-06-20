import { contextBridge, ipcRenderer } from 'electron';

// ─── Type Definitions ─────────────────────────────────────────────────────────
export interface ElectronAPI {
  // Dialogs
  openDirectory: () => Promise<string | null>;
  saveFile: (opts?: { defaultPath?: string; filters?: Array<{ name: string; extensions: string[] }> }) => Promise<string | null>;
  openSaveDirectory: () => Promise<string | null>;

  // Shell
  openPath: (path: string) => Promise<void>;
  showItemInFolder: (path: string) => Promise<void>;

  // Store
  storeGet: (key: string) => Promise<unknown>;
  storeSet: (key: string, value: unknown) => Promise<void>;

  // Projects
  addRecentProject: (path: string) => Promise<void>;

  // Backend
  getBackendPort: () => Promise<number>;
  restartBackend: () => Promise<void>;

  // File system
  fsExists: (path: string) => Promise<boolean>;
  readFile: (path: string) => Promise<string>;

  // Event listeners
  on: (channel: string, listener: (...args: unknown[]) => void) => () => void;
  once: (channel: string, listener: (...args: unknown[]) => void) => void;
  removeListener: (channel: string, listener: (...args: unknown[]) => void) => void;

  // Platform
  platform: NodeJS.Platform;
}

// ─── Allowed Channels ─────────────────────────────────────────────────────────
const ALLOWED_RECEIVE_CHANNELS = [
  'menu:open-project',
  'menu:export-single',
  'menu:export-package',
  'menu:toggle-theme',
  'menu:about',
  'menu:open-recent',
  'backend:crashed',
  'updater:update-available',
  'updater:update-downloaded',
] as const;

// ─── Context Bridge ───────────────────────────────────────────────────────────
const electronAPI: ElectronAPI = {
  // Dialogs
  openDirectory: () => ipcRenderer.invoke('dialog:open-directory'),
  saveFile: (opts) => ipcRenderer.invoke('dialog:save-file', opts || {}),
  openSaveDirectory: () => ipcRenderer.invoke('dialog:open-save-directory'),

  // Shell
  openPath: (path) => ipcRenderer.invoke('shell:open-path', path),
  showItemInFolder: (path) => ipcRenderer.invoke('shell:show-item', path),

  // Store
  storeGet: (key) => ipcRenderer.invoke('store:get', key),
  storeSet: (key, value) => ipcRenderer.invoke('store:set', key, value),

  // Projects
  addRecentProject: (path) => ipcRenderer.invoke('projects:add-recent', path),

  // Backend
  getBackendPort: () => ipcRenderer.invoke('backend:port'),
  restartBackend: () => ipcRenderer.invoke('backend:restart'),

  // File system
  fsExists: (path) => ipcRenderer.invoke('fs:exists', path),
  readFile: (path) => ipcRenderer.invoke('fs:read-file', path),

  // Event listeners
  on: (channel, listener) => {
    const allowed = ALLOWED_RECEIVE_CHANNELS as readonly string[];
    if (!allowed.includes(channel)) {
      console.warn(`Channel "${channel}" is not in the allowlist`);
      return () => {};
    }
    const wrappedListener = (_event: Electron.IpcRendererEvent, ...args: unknown[]) =>
      listener(...args);
    ipcRenderer.on(channel, wrappedListener);
    return () => ipcRenderer.removeListener(channel, wrappedListener);
  },

  once: (channel, listener) => {
    const allowed = ALLOWED_RECEIVE_CHANNELS as readonly string[];
    if (!allowed.includes(channel)) return;
    ipcRenderer.once(channel, (_event, ...args) => listener(...args));
  },

  removeListener: (channel, listener) => {
    ipcRenderer.removeListener(channel, listener as never);
  },

  // Platform info
  platform: process.platform,
};

contextBridge.exposeInMainWorld('electron', electronAPI);
