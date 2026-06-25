import react from '@vitejs/plugin-react';
import { defineConfig } from 'vitest/config';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      // Local dev: forward API calls to the Python dev server.
      '/api': {
        target: 'http://127.0.0.1:8787',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
    },
  },
  test: {
    environment: 'jsdom',
    globals: true,
    css: false,
    // Unit tests live in src/; tests-e2e/ is Playwright and must not be picked
    // up by vitest (its test() comes from @playwright/test).
    include: ['src/**/*.{test,spec}.{ts,tsx}'],
  },
});
