import React, { useState, useEffect } from 'react';
import {
  Box, Card, CardContent, Typography, TextField, Button, Switch,
  FormControlLabel, Divider, Stack, Chip, Alert, Grid, IconButton,
  InputAdornment, useTheme,
} from '@mui/material';
import { Visibility, VisibilityOff, Save, DarkMode, LightMode, RestartAlt } from '@mui/icons-material';
import { useAppDispatch, useAppSelector } from '../../../store/hooks';
import { toggleTheme } from '../../../store/slices/uiSlice';
import { addExcludePattern, removeExcludePattern, setExcludePatterns } from '../../../store/slices/projectSlice';
import { addNotification } from '../../../store/slices/uiSlice';

export const SettingsPage: React.FC = () => {
  const theme = useTheme();
  const dispatch = useAppDispatch();
  const currentTheme = useAppSelector((s) => s.ui.theme);
  const excludePatterns = useAppSelector((s) => s.project.excludePatterns);

  const [anthropicKey, setAnthropicKey] = useState('');
  const [openaiKey, setOpenaiKey] = useState('');
  const [showAnthropicKey, setShowAnthropicKey] = useState(false);
  const [showOpenaiKey, setShowOpenaiKey] = useState(false);
  const [newPattern, setNewPattern] = useState('');

  const handleSaveKeys = async () => {
    await window.electron?.storeSet('anthropicApiKey', anthropicKey);
    await window.electron?.storeSet('openaiApiKey', openaiKey);
    dispatch(addNotification({ type: 'success', message: 'API keys saved' }));
  };

  const handleAddPattern = () => {
    if (newPattern.trim()) {
      dispatch(addExcludePattern(newPattern.trim()));
      setNewPattern('');
    }
  };

  const handleRestartBackend = async () => {
    await window.electron?.restartBackend();
    dispatch(addNotification({ type: 'info', message: 'Backend restarting...' }));
  };

  return (
    <Box sx={{ p: 3, maxWidth: 800, mx: 'auto', overflow: 'auto', height: '100%' }}>
      <Typography variant="h5" fontWeight={700} mb={3}>Settings</Typography>

      {/* Appearance */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" fontWeight={600} gutterBottom>Appearance</Typography>
          <FormControlLabel
            control={
              <Switch
                checked={currentTheme === 'dark'}
                onChange={() => dispatch(toggleTheme())}
                icon={<LightMode />}
                checkedIcon={<DarkMode />}
              />
            }
            label={`${currentTheme === 'dark' ? 'Dark' : 'Light'} Mode`}
          />
        </CardContent>
      </Card>

      {/* AI Configuration */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" fontWeight={600} gutterBottom>AI Documentation</Typography>
          <Alert severity="info" sx={{ mb: 2 }}>
            AI summaries are generated per-file during export. Keys are stored locally and never sent to RepoDoc servers.
          </Alert>
          <Stack spacing={2}>
            <TextField
              label="Anthropic API Key"
              placeholder="sk-ant-..."
              value={anthropicKey}
              onChange={(e) => setAnthropicKey(e.target.value)}
              type={showAnthropicKey ? 'text' : 'password'}
              size="small"
              fullWidth
              InputProps={{
                endAdornment: (
                  <InputAdornment position="end">
                    <IconButton size="small" onClick={() => setShowAnthropicKey(!showAnthropicKey)}>
                      {showAnthropicKey ? <VisibilityOff /> : <Visibility />}
                    </IconButton>
                  </InputAdornment>
                ),
              }}
            />
            <TextField
              label="OpenAI API Key (fallback)"
              placeholder="sk-..."
              value={openaiKey}
              onChange={(e) => setOpenaiKey(e.target.value)}
              type={showOpenaiKey ? 'text' : 'password'}
              size="small"
              fullWidth
              InputProps={{
                endAdornment: (
                  <InputAdornment position="end">
                    <IconButton size="small" onClick={() => setShowOpenaiKey(!showOpenaiKey)}>
                      {showOpenaiKey ? <VisibilityOff /> : <Visibility />}
                    </IconButton>
                  </InputAdornment>
                ),
              }}
            />
            <Button variant="outlined" startIcon={<Save />} onClick={handleSaveKeys} sx={{ alignSelf: 'flex-start' }}>
              Save API Keys
            </Button>
          </Stack>
        </CardContent>
      </Card>

      {/* Exclude Patterns */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" fontWeight={600} gutterBottom>
            Scanner Exclude Patterns
          </Typography>
          <Typography variant="body2" color="text.secondary" mb={2}>
            Files and directories matching these patterns will be ignored during scanning.
          </Typography>
          <Stack direction="row" spacing={1} mb={2}>
            <TextField
              size="small"
              placeholder="e.g. *.log or tmp/"
              value={newPattern}
              onChange={(e) => setNewPattern(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleAddPattern()}
              sx={{ flex: 1 }}
            />
            <Button variant="outlined" onClick={handleAddPattern}>Add</Button>
          </Stack>
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.75 }}>
            {excludePatterns.map((p) => (
              <Chip
                key={p}
                label={p}
                size="small"
                onDelete={() => dispatch(removeExcludePattern(p))}
                sx={{ fontFamily: 'monospace' }}
              />
            ))}
          </Box>
        </CardContent>
      </Card>

      {/* Backend */}
      <Card>
        <CardContent>
          <Typography variant="h6" fontWeight={600} gutterBottom>Backend</Typography>
          <Stack direction="row" alignItems="center" spacing={2}>
            <Button
              variant="outlined"
              color="warning"
              startIcon={<RestartAlt />}
              onClick={handleRestartBackend}
            >
              Restart Backend
            </Button>
            <Typography variant="body2" color="text.secondary">
              Restarts the Python API server. Use if export fails unexpectedly.
            </Typography>
          </Stack>
        </CardContent>
      </Card>
    </Box>
  );
};
