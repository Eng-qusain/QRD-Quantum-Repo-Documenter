import React, { useEffect, useRef, useState } from 'react';
import {
  Box, Grid, Card, CardContent, Typography, Button, FormControl,
  InputLabel, Select, MenuItem, Switch, FormControlLabel, Slider,
  TextField, Divider, LinearProgress, Stack, Chip, Alert,
  ToggleButtonGroup, ToggleButton, useTheme, Stepper, Step, StepLabel,
} from '@mui/material';
import {
  PlayArrow, Stop, FolderOpen, Description, CheckCircle, Error as ErrorIcon,
} from '@mui/icons-material';
import { useAppDispatch, useAppSelector } from '../../../store/hooks';
import { setExportOptions, startExport, cancelExport, clearCurrentJob, updateJobProgress } from '../../../store/slices/exportSlice';
import { addNotification } from '../../../store/slices/uiSlice';
import { apiClient } from '../../../utils/apiClient';

const EXPORT_MODES = [
  { value: 'single', label: 'Single PDF', desc: 'One combined PDF for the whole project' },
  { value: 'folder', label: 'Folder PDFs', desc: 'One PDF per top-level folder' },
  { value: 'file', label: 'Per File', desc: 'Individual PDF for each file' },
  { value: 'package', label: 'Documentation Package', desc: 'Full package with architecture, stats, AI summaries' },
];

export const ExportPage: React.FC = () => {
  const theme = useTheme();
  const dispatch = useAppDispatch();
  const { options, currentJob, isExporting } = useAppSelector((s) => s.export);
  const { path: projectPath, name: projectName, isLoaded } = useAppSelector((s) => s.project);
  const wsRef = useRef<WebSocket | null>(null);
  const [backendPort, setBackendPort] = useState(8765);

  useEffect(() => {
    window.electron?.getBackendPort().then((p: number) => setBackendPort(p || 8765));
  }, []);

  // WebSocket progress tracking
  useEffect(() => {
    if (!currentJob?.id) return;

    const ws = new WebSocket(`ws://localhost:${backendPort}/export/ws/${currentJob.id}`);
    wsRef.current = ws;

    ws.onmessage = (e) => {
      const data = JSON.parse(e.data);
      dispatch(updateJobProgress({
        status: data.status,
        progress: data.progress,
        currentFile: data.message,
        processedFiles: data.processed_files,
        totalFiles: data.total_files,
        outputFiles: data.output_files || [],
        error: data.error,
      }));

      if (data.status === 'completed') {
        dispatch(addNotification({ type: 'success', message: 'Export completed!' }));
        ws.close();
      } else if (data.status === 'failed') {
        dispatch(addNotification({ type: 'error', message: `Export failed: ${data.error}` }));
        ws.close();
      }
    };

    ws.onerror = () => {
      dispatch(addNotification({ type: 'warning', message: 'Progress connection lost — polling...' }));
    };

    return () => ws.close();
  }, [currentJob?.id, backendPort, dispatch]);

  const handleStartExport = async () => {
    if (!projectPath) return;

    let outputPath = options.outputPath;
    if (!outputPath) {
      if (options.mode === 'single') {
        const p = await window.electron?.saveFile({ defaultPath: `${projectName}_docs.pdf` });
        if (!p) return;
        outputPath = p;
      } else {
        const p = await window.electron?.openSaveDirectory();
        if (!p) return;
        outputPath = p;
      }
      dispatch(setExportOptions({ outputPath }));
    }

    try {
      await dispatch(startExport({
        projectPath,
        options: { ...options, outputPath },
      })).unwrap();
    } catch (err) {
      dispatch(addNotification({ type: 'error', message: `Failed to start export: ${err}` }));
    }
  };

  const handleCancel = async () => {
    if (currentJob?.id) {
      await dispatch(cancelExport(currentJob.id));
    }
  };

  const handleOpenOutput = () => {
    const files = currentJob?.outputFiles;
    if (files?.length) {
      window.electron?.showItemInFolder(files[0]);
    }
  };

  if (!isLoaded) {
    return (
      <Box sx={{ p: 4, textAlign: 'center' }}>
        <Description sx={{ fontSize: 64, color: 'text.disabled', mb: 2 }} />
        <Typography variant="h6" color="text.secondary">
          Open a project first to export documentation.
        </Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3, maxWidth: 1000, mx: 'auto', overflow: 'auto', height: '100%' }}>
      <Typography variant="h5" fontWeight={700} mb={3}>
        Export Documentation
      </Typography>

      <Grid container spacing={3}>
        {/* Left: Configuration */}
        <Grid item xs={12} md={7}>
          {/* Export Mode */}
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Typography variant="h6" fontWeight={600} gutterBottom>Export Mode</Typography>
              <Grid container spacing={1.5}>
                {EXPORT_MODES.map((m) => (
                  <Grid item xs={6} key={m.value}>
                    <Box
                      onClick={() => dispatch(setExportOptions({ mode: m.value as any }))}
                      sx={{
                        p: 1.5, borderRadius: 2, cursor: 'pointer',
                        border: `2px solid ${options.mode === m.value ? theme.palette.primary.main : theme.palette.divider}`,
                        bgcolor: options.mode === m.value
                          ? `${theme.palette.primary.main}15`
                          : 'transparent',
                        transition: 'all 0.15s',
                        '&:hover': { borderColor: theme.palette.primary.light },
                      }}
                    >
                      <Typography variant="subtitle2" fontWeight={600}>{m.label}</Typography>
                      <Typography variant="caption" color="text.secondary">{m.desc}</Typography>
                    </Box>
                  </Grid>
                ))}
              </Grid>
            </CardContent>
          </Card>

          {/* Content Options */}
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Typography variant="h6" fontWeight={600} gutterBottom>Content</Typography>
              <Grid container spacing={0}>
                {[
                  ['includeTOC', 'Table of Contents'],
                  ['includeStats', 'Project Statistics'],
                  ['includeAI', 'AI Documentation'],
                  ['includeCharts', 'Charts & Plots'],
                  ['includeDependencies', 'Dependency Analysis'],
                  ['syntaxHighlighting', 'Syntax Highlighting'],
                  ['lineNumbers', 'Line Numbers'],
                  ['includeArchitecture', 'Architecture Diagrams'],
                ].map(([key, label]) => (
                  <Grid item xs={6} key={key}>
                    <FormControlLabel
                      control={
                        <Switch
                          size="small"
                          checked={Boolean(options[key as keyof typeof options])}
                          onChange={(e) => dispatch(setExportOptions({ [key]: e.target.checked }))}
                        />
                      }
                      label={<Typography variant="body2">{label}</Typography>}
                    />
                  </Grid>
                ))}
              </Grid>
            </CardContent>
          </Card>

          {/* Format Options */}
          <Card>
            <CardContent>
              <Typography variant="h6" fontWeight={600} gutterBottom>Format</Typography>
              <Grid container spacing={2}>
                <Grid item xs={4}>
                  <FormControl fullWidth size="small">
                    <InputLabel>Paper Size</InputLabel>
                    <Select
                      value={options.paperSize}
                      label="Paper Size"
                      onChange={(e) => dispatch(setExportOptions({ paperSize: e.target.value as any }))}
                    >
                      {['A4', 'Letter', 'A3'].map((s) => <MenuItem key={s} value={s}>{s}</MenuItem>)}
                    </Select>
                  </FormControl>
                </Grid>
                <Grid item xs={4}>
                  <FormControl fullWidth size="small">
                    <InputLabel>Theme</InputLabel>
                    <Select
                      value={options.theme}
                      label="Theme"
                      onChange={(e) => dispatch(setExportOptions({ theme: e.target.value as any }))}
                    >
                      {['default', 'dark', 'github', 'monokai'].map((t) => (
                        <MenuItem key={t} value={t}>{t.charAt(0).toUpperCase() + t.slice(1)}</MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                </Grid>
                <Grid item xs={4}>
                  <FormControl fullWidth size="small">
                    <InputLabel>Orientation</InputLabel>
                    <Select
                      value={options.orientation}
                      label="Orientation"
                      onChange={(e) => dispatch(setExportOptions({ orientation: e.target.value as any }))}
                    >
                      <MenuItem value="portrait">Portrait</MenuItem>
                      <MenuItem value="landscape">Landscape</MenuItem>
                    </Select>
                  </FormControl>
                </Grid>
                <Grid item xs={12}>
                  <Typography variant="body2" gutterBottom>
                    Font Size: {options.fontSize}pt
                  </Typography>
                  <Slider
                    value={options.fontSize}
                    min={7} max={14} step={1}
                    marks={[{value:7,label:'7'},{value:9,label:'9'},{value:11,label:'11'},{value:14,label:'14'}]}
                    onChange={(_, v) => dispatch(setExportOptions({ fontSize: v as number }))}
                    size="small"
                  />
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>

        {/* Right: Summary + Actions */}
        <Grid item xs={12} md={5}>
          <Card sx={{ mb: 3, position: 'sticky', top: 0 }}>
            <CardContent>
              <Typography variant="h6" fontWeight={600} gutterBottom>Export Summary</Typography>
              <Stack spacing={1} mb={3}>
                <Stack direction="row" justifyContent="space-between">
                  <Typography variant="body2" color="text.secondary">Project</Typography>
                  <Typography variant="body2" fontWeight={600}>{projectName}</Typography>
                </Stack>
                <Stack direction="row" justifyContent="space-between">
                  <Typography variant="body2" color="text.secondary">Mode</Typography>
                  <Chip label={options.mode} size="small" color="primary" />
                </Stack>
                <Stack direction="row" justifyContent="space-between">
                  <Typography variant="body2" color="text.secondary">Theme</Typography>
                  <Typography variant="body2">{options.theme}</Typography>
                </Stack>
                <Stack direction="row" justifyContent="space-between">
                  <Typography variant="body2" color="text.secondary">Paper</Typography>
                  <Typography variant="body2">{options.paperSize} {options.orientation}</Typography>
                </Stack>
                {options.includeAI && (
                  <Alert severity="info" sx={{ py: 0 }}>
                    <Typography variant="caption">AI docs require API key in Settings</Typography>
                  </Alert>
                )}
              </Stack>

              <Divider sx={{ mb: 2 }} />

              {/* Progress */}
              {currentJob && (
                <Box mb={2}>
                  <Stack direction="row" justifyContent="space-between" mb={0.5}>
                    <Typography variant="body2">
                      {currentJob.status === 'completed' ? 'Complete!' :
                       currentJob.status === 'failed' ? 'Failed' :
                       currentJob.status === 'cancelled' ? 'Cancelled' :
                       `${currentJob.processedFiles}/${currentJob.totalFiles} files`}
                    </Typography>
                    <Typography variant="body2" color="primary">
                      {Math.round(currentJob.progress)}%
                    </Typography>
                  </Stack>
                  <LinearProgress
                    variant="determinate"
                    value={currentJob.progress}
                    color={currentJob.status === 'failed' ? 'error' : currentJob.status === 'completed' ? 'success' : 'primary'}
                    sx={{ mb: 0.5 }}
                  />
                  {currentJob.currentFile && (
                    <Typography variant="caption" color="text.secondary" noWrap>
                      {currentJob.currentFile}
                    </Typography>
                  )}
                  {currentJob.error && (
                    <Alert severity="error" sx={{ mt: 1, py: 0 }}>{currentJob.error}</Alert>
                  )}
                </Box>
              )}

              {/* Action Buttons */}
              <Stack spacing={1}>
                {!isExporting || currentJob?.status === 'completed' ? (
                  <Button
                    fullWidth
                    variant="contained"
                    size="large"
                    startIcon={<PlayArrow />}
                    onClick={handleStartExport}
                    disabled={isExporting && currentJob?.status !== 'completed'}
                  >
                    Start Export
                  </Button>
                ) : (
                  <Button
                    fullWidth
                    variant="outlined"
                    color="error"
                    startIcon={<Stop />}
                    onClick={handleCancel}
                  >
                    Cancel Export
                  </Button>
                )}

                {currentJob?.status === 'completed' && currentJob.outputFiles.length > 0 && (
                  <Button
                    fullWidth
                    variant="outlined"
                    startIcon={<FolderOpen />}
                    onClick={handleOpenOutput}
                  >
                    Open Output Folder
                  </Button>
                )}

                {currentJob && ['completed', 'failed', 'cancelled'].includes(currentJob.status) && (
                  <Button variant="text" size="small" onClick={() => dispatch(clearCurrentJob())}>
                    Clear
                  </Button>
                )}
              </Stack>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};
