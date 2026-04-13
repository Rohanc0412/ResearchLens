import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./tests",
  webServer: {
    command: "corepack pnpm --filter web dev --host 127.0.0.1 --port 4173",
    reuseExistingServer: true,
    timeout: 120000,
    url: "http://127.0.0.1:4173",
  },
  use: {
    baseURL: "http://127.0.0.1:4173",
    headless: true,
  },
});

