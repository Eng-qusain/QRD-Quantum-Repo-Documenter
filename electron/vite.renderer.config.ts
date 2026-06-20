import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

// Manual chunk groups — kept as a lookup table, applied via a function so it
// works on both classic Rollup (Vite 5) and the newer Rolldown bundler
// (Vite 7+), which only accepts a function for manualChunks.
const CHUNK_GROUPS: Record<string, string[]> = {
  vendor: ['react', 'react-dom', 'react-router-dom'],
  mui: ['@mui/material', '@mui/icons-material'],
  redux: ['@reduxjs/toolkit', 'react-redux'],
  highlighter: ['react-syntax-highlighter'],
};

function manualChunks(id: string): string | undefined {
  for (const [chunkName, packages] of Object.entries(CHUNK_GROUPS)) {
    if (packages.some((pkg) => id.includes(`/node_modules/${pkg}/`) || id.includes(`/node_modules/${pkg.split('/')[0]}/`))) {
      return chunkName;
    }
  }
  return undefined;
}

export default defineConfig({
  plugins: [react()],
  root: path.join(__dirname, 'src/renderer'),
  base: './',
  build: {
    outDir: path.join(__dirname, 'dist/renderer'),
    emptyOutDir: true,
    rollupOptions: {
      output: {
        manualChunks,
      },
    },
  },
  server: {
    port: 5173,
    strictPort: true,
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, 'src/renderer'),
    },
  },
  define: {
    'process.env.NODE_ENV': JSON.stringify(process.env.NODE_ENV || 'development'),
  },
});
