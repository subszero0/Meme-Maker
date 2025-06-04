import "cypress-real-events";
import "@percy/cypress";

// Extend Cypress types to include Percy commands
declare global {
  namespace Cypress {
    interface Chainable {
      percySnapshot(name: string, options?: { widths?: number[] }): void;
    }
  }
}

// Handle React hydration errors and other uncaught exceptions
Cypress.on('uncaught:exception', (err, runnable) => {
  // React hydration error #418 - ignore during tests
  if (err.message.includes('Minified React error #418')) {
    return false;
  }
  
  // Other common hydration/React errors to ignore during visual tests
  if (err.message.includes('Hydration failed')) {
    return false;
  }
  
  if (err.message.includes('Text content does not match server-rendered HTML')) {
    return false;
  }
  
  // Allow other errors to fail the test
  return true;
});

// Wait for app to be ready before visual tests
beforeEach(() => {
  // Wait for Next.js hydration to complete
  cy.window().should('have.property', 'next');
  cy.wait(500); // Allow time for hydration to complete
});
