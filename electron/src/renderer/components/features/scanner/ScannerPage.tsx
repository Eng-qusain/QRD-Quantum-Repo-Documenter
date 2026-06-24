import React, { useState, useCallback } from 'react';
import {
  Box, Grid, Typography, TextField, InputAdornment,
  IconButton, Chip, Stack, ToggleButtonGroup,
  ToggleButton, Tooltip, useTheme, CircularProgress,
} from '@mui/material';
import {
  Search, Clear, ViewList, AccountTree, BarChart, FolderOpen,
} from '@mui/icons-material';
import { useAppSelector, useAppDispatch } from '../../../store/hooks';
import { setSearchQuery, setViewMode, setSelectedFile } from '../../../store/slices/scannerSlice';
import { FileTreeView } from './FileTreeView';
import { CodePreview } from './CodePreview';
import { StatsPanel } from './StatsPanel';
import { apiClient } from '../../../utils/apiClient';

export const ScannerPage: React.FC = () => {
  const theme = useTheme();
  const dispatch = useAppDispatch();
  const { fileTree, flatFiles, stats, isLoaded } = useAppSelector((s) => s.project);
  const { searchQuery, viewMode, selectedFilePath } = useAppSelector((s) => s.scanner);
  const [loadingFile, setLoadingFile] = useState(false);

  const handleFileSelect = useCallback(async (filePath: string) => {
    setLoadingFile(true);
    try {
      const res = await apiClient.get('/scanner/file-content', {
        params: { path: filePath, max_lines: 3000 },
      });
      const ext = filePath.split('.').pop() || 'text';
      dispatch(setSelectedFile({
        content: res.data.content,
        path: filePath,
        language: ext,
      }));
    } catch (err) {
      console.error('Failed to load file:', err);
    } finally {
      setLoadingFile(false);
    }
  }, [dispatch]);

  if (!isLoaded) {
    return (
      <Box sx={{ p: 4, textAlign: 'center' }}>
        <FolderOpen sx={{ fontSize: 64, color: 'text.disabled', mb: 2 }} />
        <Typography variant="h6" color="text.secondary">
          No project loaded. Open a project from the Dashboard.
        </Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      {/* Toolbar */}
      <Box
        sx={{
          px: 2, py: 1.5,
          borderBottom: `1px solid ${theme.palette.divider}`,
          bgcolor: theme.palette.background.paper,
          display: 'flex',
          alignItems: 'center',
          gap: 2,
          flexShrink: 0,
        }}
      >
        <TextField
          size="small"
          placeholder="Search files…"
          value={searchQuery}
          onChange={(e) => dispatch(setSearchQuery(e.target.value))}
          sx={{ width: 280 }}
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <Search fontSize="small" />
              </InputAdornment>
            ),
            endAdornment: searchQuery ? (
              <InputAdornment position="end">
                <IconButton size="small" onClick={() => dispatch(setSearchQuery(''))}>
                  <Clear fontSize="small" />
                </IconButton>
              </InputAdornment>
            ) : null,
          }}
        />

        <Stack direction="row" spacing={1}>
          <Chip label={`${flatFiles.length.toLocaleString()} files`} size="small" />
          {stats && (
            <Chip
              label={`${stats.totalLines.toLocaleString()} lines`}
              size="small"
              color="primary"
              variant="outlined"
            />
          )}
        </Stack>

        <Box sx={{ flex: 1 }} />

        <ToggleButtonGroup
          value={viewMode}
          exclusive
          size="small"
          onChange={(_, v) => v && dispatch(setViewMode(v))}
        >
          <ToggleButton value="tree"><Tooltip title="Tree View"><AccountTree fontSize="small" /></Tooltip></ToggleButton>
          <ToggleButton value="list"><Tooltip title="List View"><ViewList fontSize="small" /></Tooltip></ToggleButton>
          <ToggleButton value="stats"><Tooltip title="Statistics"><BarChart fontSize="small" /></Tooltip></ToggleButton>
        </ToggleButtonGroup>
      </Box>

      {/* Main content */}
      <Box sx={{ flex: 1, overflow: 'hidden', display: 'flex' }}>
        {viewMode === 'stats' ? (
          <Box sx={{ flex: 1, overflow: 'auto', p: 2 }}>
            <StatsPanel stats={stats} />
          </Box>
        ) : (
          <Grid container sx={{ height: '100%' }}>
            {/* File tree / list panel */}
            <Grid
              item
              xs={4}
              sx={{
                borderRight: `1px solid ${theme.palette.divider}`,
                overflow: 'auto',
                height: '100%',
              }}
            >
              <FileTreeView
                fileTree={fileTree}
                flatFiles={flatFiles}
                searchQuery={searchQuery}
                viewMode={viewMode}
                onFileSelect={handleFileSelect}
                selectedPath={selectedFilePath}
              />
            </Grid>

            {/* Code preview panel */}
            <Grid item xs={8} sx={{ height: '100%', overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
              {loadingFile ? (
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', flex: 1 }}>
                  <CircularProgress size={32} />
                </Box>
              ) : (
                <CodePreview />
              )}
            </Grid>
          </Grid>
        )}
      </Box>
    </Box>
  );
};
