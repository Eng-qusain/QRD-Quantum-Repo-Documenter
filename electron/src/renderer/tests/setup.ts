// src/renderer/tests/setup.ts
import '@testing-library/jest-dom';

// Mock Electron API
Object.defineProperty(window, 'electron', {
  value: {
    openDirectory: vi.fn().mockResolvedValue('/mock/project'),
    saveFile: vi.fn().mockResolvedValue('/mock/output.pdf'),
    openSaveDirectory: vi.fn().mockResolvedValue('/mock/output'),
    openPath: vi.fn().mockResolvedValue(undefined),
    showItemInFolder: vi.fn().mockResolvedValue(undefined),
    storeGet: vi.fn().mockResolvedValue(null),
    storeSet: vi.fn().mockResolvedValue(undefined),
    addRecentProject: vi.fn().mockResolvedValue(undefined),
    getBackendPort: vi.fn().mockResolvedValue(8765),
    restartBackend: vi.fn().mockResolvedValue(undefined),
    fsExists: vi.fn().mockResolvedValue(true),
    readFile: vi.fn().mockResolvedValue(''),
    on: vi.fn().mockReturnValue(() => {}),
    once: vi.fn(),
    removeListener: vi.fn(),
    platform: 'linux',
  },
  writable: false,
});
