import { defineConfig, devices } from "@playwright/test";

// Target is supplied by the runner:
//   - CI: http://localhost:3000 (ephemeral docker-compose stack)
//   - aiserver: https://sadot.lavit.io (live site)
// The app is mounted under /crm (next.config.js basePath); tests add that prefix.
const baseURL = process.env.E2E_BASE_URL || "http://localhost:3000";

export default defineConfig({
  testDir: "./tests",
  // Smoke runs are small and order-independent but we keep them serial so a
  // single worker is enough and live runs stay gentle on the server.
  fullyParallel: false,
  workers: 1,
  timeout: 45_000,
  expect: { timeout: 10_000 },
  retries: process.env.CI ? 1 : 0,
  // Artifacts so you can literally "see" each run (HTML report + trace + video).
  reporter: [["list"], ["html", { open: "never" }]],
  use: {
    baseURL,
    trace: "on",
    screenshot: "on",
    video: "retain-on-failure",
    ignoreHTTPSErrors: true,
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
});
