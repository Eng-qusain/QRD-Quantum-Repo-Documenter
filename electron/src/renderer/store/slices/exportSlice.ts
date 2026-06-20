import { createSlice, PayloadAction, createAsyncThunk } from '@reduxjs/toolkit';
import { apiClient } from '../../utils/apiClient';

// ─── Types ───────────────────────────────────────────────────────────────────
export type ExportMode = 'single' | 'folder' | 'file' | 'package';

export interface ExportOptions {
  mode: ExportMode;
  outputPath: string;
  includeAI: boolean;
  includeCharts: boolean;
  includeTOC: boolean;
  includeStats: boolean;
  includeDependencies: boolean;
  includeArchitecture: boolean;
  syntaxHighlighting: boolean;
  lineNumbers: boolean;
  maxCsvRows: number;
  paperSize: 'A4' | 'Letter' | 'A3';
  orientation: 'portrait' | 'landscape';
  theme: 'default' | 'dark' | 'github' | 'monokai';
  fontSize: number;
  selectedFiles?: string[];
}

export interface ExportJob {
  id: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
  progress: number;
  currentFile: string;
  totalFiles: number;
  processedFiles: number;
  outputFiles: string[];
  error?: string;
  startedAt?: string;
  completedAt?: string;
  estimatedTimeRemaining?: number;
}

export interface ExportState {
  options: ExportOptions;
  currentJob: ExportJob | null;
  jobHistory: ExportJob[];
  isExporting: boolean;
}

// ─── Async Thunks ─────────────────────────────────────────────────────────────
export const startExport = createAsyncThunk(
  'export/start',
  async (
    params: { projectPath: string; options: ExportOptions },
    { rejectWithValue }
  ) => {
    try {
      const response = await apiClient.post('/export/start', params);
      return response.data;
    } catch (error: unknown) {
      const err = error as { response?: { data?: { detail?: string } } };
      return rejectWithValue(err.response?.data?.detail || 'Export failed to start');
    }
  }
);

export const cancelExport = createAsyncThunk(
  'export/cancel',
  async (jobId: string, { rejectWithValue }) => {
    try {
      await apiClient.post(`/export/${jobId}/cancel`);
      return jobId;
    } catch (error: unknown) {
      const err = error as { response?: { data?: { detail?: string } } };
      return rejectWithValue(err.response?.data?.detail || 'Cancel failed');
    }
  }
);

// ─── Slice ────────────────────────────────────────────────────────────────────
const defaultOptions: ExportOptions = {
  mode: 'single',
  outputPath: '',
  includeAI: true,
  includeCharts: true,
  includeTOC: true,
  includeStats: true,
  includeDependencies: true,
  includeArchitecture: false,
  syntaxHighlighting: true,
  lineNumbers: true,
  maxCsvRows: 100,
  paperSize: 'A4',
  orientation: 'portrait',
  theme: 'default',
  fontSize: 9,
  selectedFiles: [],
};

const initialState: ExportState = {
  options: defaultOptions,
  currentJob: null,
  jobHistory: [],
  isExporting: false,
};

export const exportSlice = createSlice({
  name: 'export',
  initialState,
  reducers: {
    setExportOptions: (state, action: PayloadAction<Partial<ExportOptions>>) => {
      state.options = { ...state.options, ...action.payload };
    },
    setExportMode: (state, action: PayloadAction<ExportMode>) => {
      state.options.mode = action.payload;
    },
    updateJobProgress: (state, action: PayloadAction<Partial<ExportJob>>) => {
      if (state.currentJob) {
        Object.assign(state.currentJob, action.payload);
      }
    },
    clearCurrentJob: (state) => {
      if (state.currentJob) {
        state.jobHistory.unshift(state.currentJob);
        if (state.jobHistory.length > 20) state.jobHistory.pop();
      }
      state.currentJob = null;
      state.isExporting = false;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(startExport.pending, (state) => {
        state.isExporting = true;
      })
      .addCase(startExport.fulfilled, (state, action) => {
        state.currentJob = {
          id: action.payload.jobId,
          status: 'pending',
          progress: 0,
          currentFile: '',
          totalFiles: 0,
          processedFiles: 0,
          outputFiles: [],
          startedAt: new Date().toISOString(),
        };
      })
      .addCase(startExport.rejected, (state) => {
        state.isExporting = false;
      })
      .addCase(cancelExport.fulfilled, (state) => {
        if (state.currentJob) {
          state.currentJob.status = 'cancelled';
        }
        state.isExporting = false;
      });
  },
});

export const { setExportOptions, setExportMode, updateJobProgress, clearCurrentJob } =
  exportSlice.actions;

export default exportSlice.reducer;
