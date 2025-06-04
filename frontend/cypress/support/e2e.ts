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
Cypress.on("uncaught:exception", (err, runnable) => {
  // React hydration error #418 - ignore during tests
  if (err.message.includes("Minified React error #418")) {
    return false;
  }

  // Other common hydration/React errors to ignore during visual tests
  if (err.message.includes("Hydration failed")) {
    return false;
  }

  if (
    err.message.includes("Text content does not match server-rendered HTML")
  ) {
    return false;
  }

  // Ignore WebGL and system-level errors common in CI environments
  if (err.message.includes("WebGL")) {
    return false;
  }

  if (err.message.includes("UPower")) {
    return false;
  }

  // Allow other errors to fail the test
  return true;
});

// Wait for app to be ready before visual tests
beforeEach(() => {
  // Wait for React/Next.js app to be ready by checking for the main app container
  // This works for both development and production builds
  // Increase timeout for slower CI environments
  cy.get("body", { timeout: 10000 }).should("be.visible");
  cy.wait(1000); // Allow time for initial hydration/rendering to complete
});
