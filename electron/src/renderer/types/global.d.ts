/**
 * Global type augmentation for the renderer process.
 *
 * The preload script (src/preload/preload.ts) exposes a typed `ElectronAPI`
 * object on `window.electron` via `contextBridge.exposeInMainWorld`. This file
 * tells TypeScript that the property exists at runtime so renderer code can
 * call `window.electron.xxx()` without a "Property does not exist" error.
 *
 * This file is picked up automatically by tsconfig's `include` glob
 * (src/renderer/**\/*) since it lives inside src/renderer/.
 */
import type { ElectronAPI } from '../preload/preload';

declare global {
  interface Window {
    electron?: ElectronAPI;
  }
}

// Required to make this a module (not a global script) so `declare global` works correctly.
export {};
