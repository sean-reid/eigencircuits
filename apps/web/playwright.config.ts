import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './tests-e2e',
  fullyParallel: false,
  retries: 0,
  use: {
    baseURL: 'http://localhost:5173',
    screenshot: 'only-on-failure',
  },
  webServer: [
    {
      command: 'pnpm dev:api',
      url: 'http://127.0.0.1:8787/health',
      reuseExistingServer: true,
      timeout: 60_000,
    },
    {
      command: 'pnpm dev:web',
      url: 'http://localhost:5173',
      reuseExistingServer: true,
      timeout: 60_000,
    },
  ],
});
