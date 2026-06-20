import { createSlice, PayloadAction } from '@reduxjs/toolkit';

export interface SearchResult {
  filePath: string;
  relativePath: string;
  lineNumber?: number;
  snippet?: string;
  matchType: 'filename' | 'extension' | 'content';
}

export interface ScannerState {
  searchQuery: string;
  searchResults: SearchResult[];
  isSearching: boolean;
  selectedFileContent: string | null;
  selectedFilePath: string | null;
  previewLanguage: string;
  treeExpanded: string[];
  viewMode: 'tree' | 'list' | 'stats';
}

const initialState: ScannerState = {
  searchQuery: '',
  searchResults: [],
  isSearching: false,
  selectedFileContent: null,
  selectedFilePath: null,
  previewLanguage: 'text',
  treeExpanded: [],
  viewMode: 'tree',
};

export const scannerSlice = createSlice({
  name: 'scanner',
  initialState,
  reducers: {
    setSearchQuery: (state, action: PayloadAction<string>) => {
      state.searchQuery = action.payload;
    },
    setSearchResults: (state, action: PayloadAction<SearchResult[]>) => {
      state.searchResults = action.payload;
    },
    setIsSearching: (state, action: PayloadAction<boolean>) => {
      state.isSearching = action.payload;
    },
    setSelectedFile: (
      state,
      action: PayloadAction<{ content: string; path: string; language: string } | null>
    ) => {
      if (action.payload) {
        state.selectedFileContent = action.payload.content;
        state.selectedFilePath = action.payload.path;
        state.previewLanguage = action.payload.language;
      } else {
        state.selectedFileContent = null;
        state.selectedFilePath = null;
        state.previewLanguage = 'text';
      }
    },
    setTreeExpanded: (state, action: PayloadAction<string[]>) => {
      state.treeExpanded = action.payload;
    },
    setViewMode: (state, action: PayloadAction<ScannerState['viewMode']>) => {
      state.viewMode = action.payload;
    },
    clearSearch: (state) => {
      state.searchQuery = '';
      state.searchResults = [];
    },
  },
});

export const {
  setSearchQuery,
  setSearchResults,
  setIsSearching,
  setSelectedFile,
  setTreeExpanded,
  setViewMode,
  clearSearch,
} = scannerSlice.actions;

export default scannerSlice.reducer;
