import { createSlice, PayloadAction, createAsyncThunk } from '@reduxjs/toolkit';
import { apiClient } from '../../utils/apiClient';

// ─── Types ───────────────────────────────────────────────────────────────────
export interface FileNode {
  id: string;
  name: string;
  path: string;
  relativePath: string;
  type: 'file' | 'directory';
  size: number;
  lineCount?: number;
  language?: string;
  extension: string;
  lastModified: string;
  children?: FileNode[];
}

export interface ProjectStats {
  totalFiles: number;
  totalDirectories: number;
  totalLines: number;
  totalSize: number;
  languageDistribution: Record<string, number>;
  extensionDistribution: Record<string, number>;
  largestFiles: Array<{ path: string; size: number; lines: number }>;
  averageFileSize: number;
  averageLineCount: number;
}

export interface ProjectState {
  path: string | null;
  name: string | null;
  fileTree: FileNode | null;
  flatFiles: FileNode[];
  stats: ProjectStats | null;
  isLoaded: boolean;
  isScanning: boolean;
  scanProgress: number;
  scanError: string | null;
  selectedFiles: string[];
  excludePatterns: string[];
  includePatterns: string[];
}

// ─── Async Thunks ─────────────────────────────────────────────────────────────
export const scanProject = createAsyncThunk(
  'project/scan',
  async (
    params: {
      path: string;
      excludePatterns?: string[];
      includePatterns?: string[];
    },
    { rejectWithValue }
  ) => {
    try {
      const response = await apiClient.post('/scanner/scan', params);
      return response.data;
    } catch (error: unknown) {
      const err = error as { response?: { data?: { detail?: string } } };
      return rejectWithValue(err.response?.data?.detail || 'Scan failed');
    }
  }
);

// ─── Slice ────────────────────────────────────────────────────────────────────
const initialState: ProjectState = {
  path: null,
  name: null,
  fileTree: null,
  flatFiles: [],
  stats: null,
  isLoaded: false,
  isScanning: false,
  scanProgress: 0,
  scanError: null,
  selectedFiles: [],
  excludePatterns: [
    '__pycache__',
    'node_modules',
    '.git',
    '.venv',
    'venv',
    'dist',
    'build',
    '.next',
    '.nuxt',
    'coverage',
    '.pytest_cache',
    '*.pyc',
    '*.egg-info',
  ],
  includePatterns: [],
};

export const projectSlice = createSlice({
  name: 'project',
  initialState,
  reducers: {
    setProjectPath: (state, action: PayloadAction<string>) => {
      state.path = action.payload;
      state.name = action.payload.split('/').pop() || action.payload;
      state.isLoaded = false;
      state.fileTree = null;
      state.flatFiles = [];
      state.stats = null;
    },
    clearProject: (state) => {
      Object.assign(state, initialState);
    },
    setScanProgress: (state, action: PayloadAction<number>) => {
      state.scanProgress = action.payload;
    },
    setSelectedFiles: (state, action: PayloadAction<string[]>) => {
      state.selectedFiles = action.payload;
    },
    toggleFileSelection: (state, action: PayloadAction<string>) => {
      const idx = state.selectedFiles.indexOf(action.payload);
      if (idx === -1) {
        state.selectedFiles.push(action.payload);
      } else {
        state.selectedFiles.splice(idx, 1);
      }
    },
    setExcludePatterns: (state, action: PayloadAction<string[]>) => {
      state.excludePatterns = action.payload;
    },
    addExcludePattern: (state, action: PayloadAction<string>) => {
      if (!state.excludePatterns.includes(action.payload)) {
        state.excludePatterns.push(action.payload);
      }
    },
    removeExcludePattern: (state, action: PayloadAction<string>) => {
      state.excludePatterns = state.excludePatterns.filter((p) => p !== action.payload);
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(scanProject.pending, (state) => {
        state.isScanning = true;
        state.scanError = null;
        state.scanProgress = 0;
      })
      .addCase(scanProject.fulfilled, (state, action) => {
        state.isScanning = false;
        state.isLoaded = true;
        state.scanProgress = 100;
        state.fileTree = action.payload.fileTree;
        state.flatFiles = action.payload.flatFiles;
        state.stats = action.payload.stats;
      })
      .addCase(scanProject.rejected, (state, action) => {
        state.isScanning = false;
        state.scanError = action.payload as string;
      });
  },
});

export const {
  setProjectPath,
  clearProject,
  setScanProgress,
  setSelectedFiles,
  toggleFileSelection,
  setExcludePatterns,
  addExcludePattern,
  removeExcludePattern,
} = projectSlice.actions;

export default projectSlice.reducer;
