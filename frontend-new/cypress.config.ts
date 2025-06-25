import { defineConfig } from "cypress";
import { devServer } from "@cypress/vite-dev-server";
import path from "path";

export default defineConfig({
  // Global configuration
  viewportWidth: 1280,
  viewportHeight: 720,
  video: true,
  screenshotOnRunFailure: true,

  // E2E Testing configuration
  e2e: {
    baseUrl: "http://localhost:8080",
    supportFile: "cypress/support/e2e.ts",
    specPattern: "cypress/e2e/**/*.cy.{js,jsx,ts,tsx}",

    // Following Cypress best practices for test isolation
    testIsolation: true,

    // Optimize for CI/CD
    watchForFileChanges: false,

    setupNodeEvents(on, config) {
      // Task handlers for API mocking and test utilities
      on("task", {
        // Reset test database or state if needed
        resetTestData() {
          return null;
        },

        // Seed test data
        seedTestData(data) {
          console.log("Seeding test data:", data);
          return null;
        },

        // Check if backend is ready
        checkBackendHealth() {
          return fetch("http://localhost:8000/health")
            .then((res) => res.ok)
            .catch(() => false);
        },
      });

      // Browser launch options
      on("before:browser:launch", (browser, launchOptions) => {
        if (browser.name === "chrome") {
          launchOptions.args.push("--disable-dev-shm-usage");
          launchOptions.args.push("--disable-web-security");
        }
        return launchOptions;
      });

      return config;
    },
  },

  // Component Testing configuration
  component: {
    devServer(devServerConfig) {
      return devServer({
        ...devServerConfig,
        framework: "react",
        viteConfig: {
          resolve: {
            alias: {
              "@": path.resolve(__dirname, "./src"),
            },
          },
        },
      });
    },
    supportFile: "cypress/support/component.ts",
    specPattern: "src/**/*.cy.{js,jsx,ts,tsx}",
    indexHtmlFile: "cypress/support/component-index.html",
  },

  // Environment variables
  env: {
    API_BASE_URL: "http://localhost:8000",
    POLLING_INTERVAL: 1000,
    TEST_USER_EMAIL: "test@example.com",
  },

  // Retry configuration
  retries: {
    runMode: 2, // Retry failed tests in CI
    openMode: 0, // No retries in interactive mode
  },

  // Timeouts following Cypress best practices
  defaultCommandTimeout: 10000,
  requestTimeout: 15000,
  responseTimeout: 15000,
  pageLoadTimeout: 30000,

  // File exclusions
  excludeSpecPattern: ["**/node_modules/**", "**/dist/**", "**/build/**"],
});
