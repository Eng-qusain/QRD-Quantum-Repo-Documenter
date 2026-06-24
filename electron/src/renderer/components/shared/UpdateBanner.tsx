import React, { useEffect, useState } from 'react';
import {
  Alert, AlertTitle, Button, Snackbar, Box, Typography,
  LinearProgress, CircularProgress, Paper, Chip,
} from '@mui/material';
import { useAppSelector, useAppDispatch } from '../../store/hooks';
import {
  removeNotification, setBackendStatus,
} from '../../store/slices/uiSlice';
import { apiClient } from '../../utils/apiClient';

// ─── Update Banner ────────────────────────────────────────────────────────────
export const UpdateBanner: React.FC = () => {
  const { updateDownloaded } = useAppSelector((s) => s.ui);

  if (!updateDownloaded) return null;

  return (
    <Alert
      severity="success"
      action={
        <Button size="small" onClick={() => window.electron?.['updater:install']?.()}>
          Restart & Update
        </Button>
      }
      sx={{ borderRadius: 0 }}
    >
      <AlertTitle>Update Ready</AlertTitle>
      A new version has been downloaded. Restart to apply.
    </Alert>
  );
};

// ─── Backend Status ───────────────────────────────────────────────────────────
type InstallState =
  | { phase: 'idle' }
  | { phase: 'installing'; message: string }
  | { phase: 'error'; message: string };

export const BackendStatus: React.FC = () => {
  const dispatch = useAppDispatch();
  const status = useAppSelector((s) => s.ui.backendStatus);
  const [install, setInstall] = useState<InstallState>({ phase: 'idle' });

  // Listen for install events from main process
  useEffect(() => {
    const offInstalling = window.electron?.on('backend:installing', () => {
      setInstall({ phase: 'installing', message: 'Preparing Python environment…' });
    });

    const offProgress = window.electron?.on('backend:install-progress', (...args: unknown[]) => {
      const msg = args[0] as string;
      setInstall({ phase: 'installing', message: msg });
    });

    const offDone = window.electron?.on('backend:install-done', () => {
      setInstall({ phase: 'idle' });
    });

    const offError = window.electron?.on('backend:install-error', (...args: unknown[]) => {
      const msg = args[0] as string;
      setInstall({ phase: 'error', message: msg });
    });

    return () => {
      offInstalling?.();
      offProgress?.();
      offDone?.();
      offError?.();
    };
  }, []);

  // Poll backend health
  useEffect(() => {
    if (install.phase === 'installing') return; // don't poll while installing

    const check = async () => {
      try {
        await apiClient.get('/health');
        dispatch(setBackendStatus('connected'));
      } catch {
        dispatch(setBackendStatus('disconnected'));
      }
    };
    check();
    const interval = setInterval(check, 10_000);
    return () => clearInterval(interval);
  }, [dispatch, install.phase]);

  // ── Full-screen installing overlay ────────────────────────────────────────
  if (install.phase === 'installing') {
    return (
      <Box
        sx={{
          position: 'fixed', inset: 0, zIndex: 9999,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          bgcolor: 'background.default',
        }}
      >
        <Paper elevation={3} sx={{ p: 5, maxWidth: 480, width: '90%', textAlign: 'center', borderRadius: 3 }}>
          <CircularProgress size={56} sx={{ mb: 3 }} />

          <Typography variant="h5" fontWeight={700} gutterBottom>
            Setting Up RepoDoc Pro
          </Typography>

          <Typography variant="body2" color="text.secondary" mb={3}>
            This only happens once on first launch. Python packages are being
            installed to power the documentation engine.
          </Typography>

          <LinearProgress sx={{ mb: 2, borderRadius: 1 }} />

          <Typography variant="caption" color="text.secondary" sx={{ fontFamily: 'monospace' }}>
            {install.message}
          </Typography>

          <Box mt={3}>
            <Chip label="Do not close the app" color="warning" size="small" />
          </Box>
        </Paper>
      </Box>
    );
  }

  // ── Install error screen ──────────────────────────────────────────────────
  if (install.phase === 'error') {
    return (
      <Box
        sx={{
          position: 'fixed', inset: 0, zIndex: 9999,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          bgcolor: 'background.default',
        }}
      >
        <Paper elevation={3} sx={{ p: 5, maxWidth: 500, width: '90%', textAlign: 'center', borderRadius: 3 }}>
          <Typography variant="h5" fontWeight={700} color="error" gutterBottom>
            Setup Failed
          </Typography>

          <Typography variant="body2" color="text.secondary" mb={2}>
            RepoDoc Pro could not install its Python dependencies.
            Please make sure <strong>Python 3.10 or newer</strong> is installed on your system.
          </Typography>

          <Alert severity="error" sx={{ textAlign: 'left', mb: 3, fontFamily: 'monospace', fontSize: 12 }}>
            {install.message}
          </Alert>

          <Typography variant="body2" color="text.secondary" mb={3}>
            Download Python from{' '}
            <Typography
              component="span"
              variant="body2"
              color="primary"
              sx={{ cursor: 'pointer', textDecoration: 'underline' }}
              onClick={() => window.electron?.openPath('https://python.org/downloads')}
            >
              python.org/downloads
            </Typography>
            {' '}then restart the app.
          </Typography>

          <Button
            variant="contained"
            onClick={() => window.electron?.restartBackend().then(() => setInstall({ phase: 'idle' }))}
          >
            Retry
          </Button>
        </Paper>
      </Box>
    );
  }

  // ── Normal disconnected banner ────────────────────────────────────────────
  if (status === 'connected') return null;

  return (
    <Alert severity="error" sx={{ borderRadius: 0 }}>
      Backend disconnected. Export features are unavailable.
      <Button size="small" sx={{ ml: 1 }} onClick={() => window.electron?.restartBackend()}>
        Restart Backend
      </Button>
    </Alert>
  );
};

// ─── Notification Snackbar ────────────────────────────────────────────────────
export const NotificationSnackbar: React.FC = () => {
  const dispatch = useAppDispatch();
  const notifications = useAppSelector((s) => s.ui.notifications);
  const latest = notifications[notifications.length - 1];

  if (!latest) return null;

  return (
    <Snackbar
      open
      autoHideDuration={4000}
      onClose={() => dispatch(removeNotification(latest.id))}
      anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
    >
      <Alert
        severity={latest.type}
        onClose={() => dispatch(removeNotification(latest.id))}
        variant="filled"
        elevation={6}
      >
        {latest.message}
      </Alert>
    </Snackbar>
  );
};
