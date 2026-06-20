import React, { useEffect, useState } from 'react';
import { Alert, AlertTitle, Button, Snackbar, Box, Chip } from '@mui/material';
import { useAppSelector, useAppDispatch } from '../../store/hooks';
import {
  removeNotification, setUpdateAvailable, setUpdateDownloaded, setBackendStatus,
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
export const BackendStatus: React.FC = () => {
  const dispatch = useAppDispatch();
  const status = useAppSelector((s) => s.ui.backendStatus);

  useEffect(() => {
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
  }, [dispatch]);

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
