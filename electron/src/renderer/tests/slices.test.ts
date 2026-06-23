import { describe, it, expect } from 'vitest';
import { configureStore } from '@reduxjs/toolkit';
import uiReducer, {
  setTheme, toggleTheme, addNotification, removeNotification,
  setSidebarCollapsed, setBackendStatus,
} from '../store/slices/uiSlice';
import projectReducer, {
  setProjectPath, clearProject, addExcludePattern,
  removeExcludePattern, setSelectedFiles,
} from '../store/slices/projectSlice';
import exportReducer, {
  setExportOptions, setExportMode, clearCurrentJob,
} from '../store/slices/exportSlice';

// ─── UI Slice ─────────────────────────────────────────────────────────────────

describe('uiSlice', () => {
  function makeStore() {
    return configureStore({ reducer: { ui: uiReducer } });
  }

  it('has correct initial state', () => {
    const store = makeStore();
    const state = store.getState().ui;
    expect(state.theme).toBe('dark');
    expect(state.sidebarCollapsed).toBe(false);
    expect(state.notifications).toEqual([]);
    expect(state.backendStatus).toBe('disconnected');
  });

  it('setTheme changes theme', () => {
    const store = makeStore();
    store.dispatch(setTheme('light'));
    expect(store.getState().ui.theme).toBe('light');
  });

  it('toggleTheme switches dark→light and light→dark', () => {
    const store = makeStore();
    expect(store.getState().ui.theme).toBe('dark');
    store.dispatch(toggleTheme());
    expect(store.getState().ui.theme).toBe('light');
    store.dispatch(toggleTheme());
    expect(store.getState().ui.theme).toBe('dark');
  });

  it('addNotification adds with id and timestamp', () => {
    const store = makeStore();
    store.dispatch(addNotification({ type: 'success', message: 'Done!' }));
    const notes = store.getState().ui.notifications;
    expect(notes).toHaveLength(1);
    expect(notes[0].message).toBe('Done!');
    expect(notes[0].type).toBe('success');
    expect(notes[0].id).toBeTruthy();
    expect(notes[0].timestamp).toBeGreaterThan(0);
  });

  it('removeNotification removes by id', () => {
    const store = makeStore();
    store.dispatch(addNotification({ type: 'info', message: 'Hello' }));
    const id = store.getState().ui.notifications[0].id;
    store.dispatch(removeNotification(id));
    expect(store.getState().ui.notifications).toHaveLength(0);
  });

  it('setSidebarCollapsed toggles sidebar', () => {
    const store = makeStore();
    store.dispatch(setSidebarCollapsed(true));
    expect(store.getState().ui.sidebarCollapsed).toBe(true);
  });

  it('setBackendStatus updates correctly', () => {
    const store = makeStore();
    store.dispatch(setBackendStatus('connected'));
    expect(store.getState().ui.backendStatus).toBe('connected');
    store.dispatch(setBackendStatus('error'));
    expect(store.getState().ui.backendStatus).toBe('error');
  });
});

// ─── Project Slice ────────────────────────────────────────────────────────────

describe('projectSlice', () => {
  function makeStore() {
    return configureStore({ reducer: { project: projectReducer } });
  }

  it('setProjectPath sets path and name', () => {
    const store = makeStore();
    store.dispatch(setProjectPath('/home/user/my-project'));
    const s = store.getState().project;
    expect(s.path).toBe('/home/user/my-project');
    expect(s.name).toBe('my-project');
    expect(s.isLoaded).toBe(false);
  });

  it('clearProject resets to initial state', () => {
    const store = makeStore();
    store.dispatch(setProjectPath('/some/path'));
    store.dispatch(clearProject());
    expect(store.getState().project.path).toBeNull();
    expect(store.getState().project.name).toBeNull();
  });

  it('addExcludePattern adds pattern', () => {
    const store = makeStore();
    store.dispatch(addExcludePattern('*.log'));
    const patterns = store.getState().project.excludePatterns;
    expect(patterns).toContain('*.log');
  });

  it('addExcludePattern does not add duplicates', () => {
    const store = makeStore();
    store.dispatch(addExcludePattern('*.log'));
    store.dispatch(addExcludePattern('*.log'));
    const patterns = store.getState().project.excludePatterns;
    const count = patterns.filter((p: string) => p === '*.log').length;
    expect(count).toBe(1);
  });

  it('removeExcludePattern removes specific pattern', () => {
    const store = makeStore();
    store.dispatch(addExcludePattern('*.tmp'));
    store.dispatch(removeExcludePattern('*.tmp'));
    expect(store.getState().project.excludePatterns).not.toContain('*.tmp');
  });

  it('setSelectedFiles updates selection', () => {
    const store = makeStore();
    store.dispatch(setSelectedFiles(['file1.py', 'file2.py']));
    expect(store.getState().project.selectedFiles).toEqual(['file1.py', 'file2.py']);
  });
});

// ─── Export Slice ─────────────────────────────────────────────────────────────

describe('exportSlice', () => {
  function makeStore() {
    return configureStore({ reducer: { export: exportReducer } });
  }

  it('has correct initial state', () => {
    const store = makeStore();
    const s = store.getState().export;
    expect(s.options.mode).toBe('single');
    expect(s.options.includeAI).toBe(true);
    expect(s.options.theme).toBe('default');
    expect(s.currentJob).toBeNull();
    expect(s.isExporting).toBe(false);
  });

  it('setExportOptions merges partial updates', () => {
    const store = makeStore();
    store.dispatch(setExportOptions({ theme: 'dark', fontSize: 11 }));
    const opts = store.getState().export.options;
    expect(opts.theme).toBe('dark');
    expect(opts.fontSize).toBe(11);
    expect(opts.mode).toBe('single'); // unchanged
  });

  it('setExportMode updates mode only', () => {
    const store = makeStore();
    store.dispatch(setExportMode('package'));
    expect(store.getState().export.options.mode).toBe('package');
  });

  it('clearCurrentJob moves job to history', () => {
    const store = makeStore();
    // Manually inject a completed job
    store.dispatch({ type: 'export/start/fulfilled', payload: { jobId: 'test-123' } });
    store.dispatch({ type: 'export/updateJobProgress', payload: { status: 'completed', progress: 100 } });
    store.dispatch(clearCurrentJob());
    const s = store.getState().export;
    expect(s.currentJob).toBeNull();
    expect(s.isExporting).toBe(false);
  });
});
