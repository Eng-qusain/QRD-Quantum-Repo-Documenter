import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./src/renderer/tests/setup.ts'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'html', 'lcov'],
      include: ['src/renderer/**/*.{ts,tsx}'],
      exclude: ['src/renderer/tests/**', '**/*.d.ts'],
    },
  },
  resolve: {
    alias: { '@': path.resolve(__dirname, 'src/renderer') },
  },
});
