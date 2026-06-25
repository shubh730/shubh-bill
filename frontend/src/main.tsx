import React from 'react';
import ReactDOM from 'react-dom/client';
import { CssBaseline, ThemeProvider, createTheme } from '@mui/material';
import App from './App';
import './styles.css';

const theme = createTheme({
  palette: {
    mode: 'light',
    primary: { main: '#0f766e' },
    secondary: { main: '#b45309' },
    background: { default: '#f8fafc', paper: '#ffffff' },
    text: { primary: '#111827', secondary: '#4b5563' }
  },
  shape: { borderRadius: 8 },
  typography: {
    fontFamily: ['Inter', 'Roboto', 'Arial', 'sans-serif'].join(','),
    button: { textTransform: 'none', fontWeight: 700 }
  },
  components: {
    MuiButton: { styleOverrides: { root: { minHeight: 42 } } },
    MuiTextField: { defaultProps: { size: 'small' } },
    MuiCard: { styleOverrides: { root: { boxShadow: '0 1px 2px rgba(15, 23, 42, 0.08)' } } }
  }
});

ReactDOM.createRoot(document.getElementById('root') as HTMLElement).render(
  <React.StrictMode>
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <App />
    </ThemeProvider>
  </React.StrictMode>
);
