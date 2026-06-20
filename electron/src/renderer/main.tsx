import React from 'react';
import ReactDOM from 'react-dom/client';
import { Provider } from 'react-redux';
import { HashRouter } from 'react-router-dom';
import { ThemeProvider, CssBaseline } from '@mui/material';
import { store } from './store/store';
import { App } from './App';
import { useAppTheme } from './hooks/useAppTheme';

const ThemedApp: React.FC = () => {
  const theme = useAppTheme();
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <App />
    </ThemeProvider>
  );
};

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <Provider store={store}>
      <HashRouter>
        <ThemedApp />
      </HashRouter>
    </Provider>
  </React.StrictMode>
);
