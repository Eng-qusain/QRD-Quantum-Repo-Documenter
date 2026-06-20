import React, { useEffect } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { Box } from '@mui/material';
import { MainLayout } from './components/layout/MainLayout';
import { DashboardPage } from './components/features/scanner/DashboardPage';
import { ScannerPage } from './components/features/scanner/ScannerPage';
import { ExportPage } from './components/features/export/ExportPage';
import { SettingsPage } from './components/features/settings/SettingsPage';
import { useElectronEvents } from './hooks/useElectronEvents';
import { useAppDispatch } from './store/hooks';
import { setTheme } from './store/slices/uiSlice';
import { UpdateBanner } from './components/shared/UpdateBanner';
import { BackendStatus } from './components/shared/BackendStatus';

export const App: React.FC = () => {
  const dispatch = useAppDispatch();
  useElectronEvents();

  useEffect(() => {
    // Load persisted theme on startup
    window.electron?.storeGet('theme').then((theme) => {
      if (theme === 'light' || theme === 'dark') {
        dispatch(setTheme(theme));
      }
    });
  }, [dispatch]);

  return (
    <Box sx={{ display: 'flex', height: '100vh', overflow: 'hidden' }}>
      <MainLayout>
        <BackendStatus />
        <UpdateBanner />
        <Routes>
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/scanner" element={<ScannerPage />} />
          <Route path="/export" element={<ExportPage />} />
          <Route path="/settings" element={<SettingsPage />} />
        </Routes>
      </MainLayout>
    </Box>
  );
};
