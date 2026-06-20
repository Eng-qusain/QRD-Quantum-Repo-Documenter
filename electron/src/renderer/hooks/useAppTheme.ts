import { useMemo } from 'react';
import { createTheme } from '@mui/material';
import { useAppSelector } from './useAppSelector';

export const useAppTheme = () => {
  const mode = useAppSelector((s) => s.ui.theme);
  return useMemo(() => createTheme({
    palette: {
      mode,
      primary: { main: '#2196f3' },
      secondary: { main: '#9c27b0' },
      background: {
        default: mode === 'dark' ? '#0d1117' : '#f5f5f5',
        paper: mode === 'dark' ? '#161b22' : '#ffffff',
      },
    },
    typography: {
      fontFamily: '"Inter", "Segoe UI", Arial, sans-serif',
    },
    shape: { borderRadius: 8 },
    components: {
      MuiCard: { defaultProps: { elevation: 0 }, styleOverrides: { root: { border: '1px solid', borderColor: mode === 'dark' ? '#30363d' : '#e0e0e0' } } },
    },
  }), [mode]);
};
