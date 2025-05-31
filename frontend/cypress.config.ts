import { defineConfig } from 'cypress';

export default defineConfig({
  e2e: {
    baseUrl: 'http://localhost:3000',
    supportFile: 'cypress/support/e2e.ts',
    video: false,
    screenshotOnRunFailure: false,
    viewportWidth: 1280,
    viewportHeight: 720,
    defaultCommandTimeout: 10000,
    requestTimeout: 10000,
    responseTimeout: 10000,
    setupNodeEvents(on, config) {
      // implement node event listeners here
    },
  },
  // Percy configuration for visual regression testing
  env: {
    percy: {
      projectToken: process.env.PERCY_TOKEN || 'percy-token-placeholder',
      viewports: [
        { width: 375, height: 667, name: 'mobile' },    // iPhone SE
        { width: 768, height: 1024, name: 'tablet' },   // iPad
        { width: 1280, height: 720, name: 'desktop' }   // Desktop
      ]
    }
  }
}); 