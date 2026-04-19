import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./tests",
  webServer: {
    command: "corepack pnpm --filter web dev --host localhost --port 4273",
    reuseExistingServer: true,
    timeout: 120000,
    url: "http://localhost:4273",
  },
  use: {
    baseURL: "http://localhost:4273",
    headless: true,
  },
});

