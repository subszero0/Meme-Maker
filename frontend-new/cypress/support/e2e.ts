// Import commands.js using ES2015 syntax:
import './commands';

// Alternatively you can use CommonJS syntax:
// require('./commands')

// ===========================
// Global Configuration
// ===========================

// Hide fetch/XHR requests from command log for cleaner output
const app = window.top;
if (app && !app.document.head.querySelector('[data-hide-command-log-request]')) {
  const style = app.document.createElement('style');
  style.innerHTML = '.command-name-request, .command-name-xhr { display: none }';
  style.setAttribute('data-hide-command-log-request', '');
  app.document.head.appendChild(style);
}

// ===========================
// Error Handling
// ===========================

// Prevent Cypress from failing on uncaught exceptions from the app
// This is useful for React development builds that may have warnings
Cypress.on('uncaught:exception', (err, runnable) => {
  // Return false to prevent the test from failing
  // Only for known safe errors
  if (err.message.includes('ResizeObserver loop limit exceeded') ||
      err.message.includes('Non-Error promise rejection captured') ||
      err.message.includes('Network request failed')) {
    return false;
  }
  
  // Fail the test for other errors
  return true;
});

// ===========================
// Test Setup and Cleanup
// ===========================

beforeEach(() => {
  // Set up API intercepts for consistent testing
  cy.setupApiMocks();
  
  // Ensure clean state
  cy.clearLocalStorage();
  cy.clearAllSessionStorage();
  
  // Check backend health before tests
  cy.task('checkBackendHealth').then((isHealthy) => {
    if (!isHealthy) {
      cy.log('⚠️ Backend is not responding. Some tests may fail.');
    }
  });
});

afterEach(() => {
  // Cleanup after each test
  cy.resetApiMocks();
  
  // Take screenshot on failure (configured globally)
  // Clean up any downloads
  cy.task('resetTestData');
});

// ===========================
// Global Test Utilities
// ===========================

declare global {
  namespace Cypress {
    interface Chainable {
      /**
       * Custom command to select DOM element by data-cy attribute.
       * Following Cypress best practices for stable selectors.
       * @example cy.getBySel('submit-button')
       */
      getBySel(selector: string, ...args: any[]): Chainable<JQuery<HTMLElement>>;
      
      /**
       * Custom command to select DOM element by data-cy attribute (partial match).
       * @example cy.getBySelLike('submit')
       */
      getBySelLike(selector: string, ...args: any[]): Chainable<JQuery<HTMLElement>>;
      
      /**
       * Custom command to set up API mocks for testing.
       */
      setupApiMocks(): Chainable<null>;
      
      /**
       * Custom command to reset API mocks.
       */
      resetApiMocks(): Chainable<null>;
      
      /**
       * Custom command to wait for video metadata to load.
       */
      waitForVideoMetadata(): Chainable<null>;
      
      /**
       * Custom command to wait for job processing to complete.
       */
      waitForJobCompletion(jobId: string): Chainable<null>;
      
      /**
       * Custom command to complete full video processing workflow.
       */
      completeVideoWorkflow(videoUrl: string, options?: {
        startTime?: string;
        endTime?: string;
        resolution?: string;
      }): Chainable<null>;
      
      /**
       * Custom command to login (if authentication is needed).
       */
      login(email?: string, password?: string): Chainable<null>;
    }
  }
} 