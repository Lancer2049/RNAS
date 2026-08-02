import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './tests/e2e',
  timeout: 30000,
  retries: 1,
  // CRITICAL: all spec files share the same live VM3 backend (scenario
  // tests apply configs / create sessions while empty-state tests assert
  // "no sessions"). Parallel workers pollute shared state and cause
  // non-deterministic flaky failures (and browser OOM under 8 workers).
  // Serial execution is the only reliable isolation here.
  workers: 1,
  fullyParallel: false,
  use: {
    baseURL: 'http://192.168.0.203:8099',
    headless: true,
  },
});
