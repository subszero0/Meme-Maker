/// <reference types="cypress" />

/**
 * CRITICAL PATH E2E TESTS
 * Following testing pyramid best practices - only the most essential user journeys
 * These tests focus on business-critical paths that MUST work in production
 */

describe("Critical User Paths (Production Essential)", () => {
  beforeEach(() => {
    cy.visit("/");
    cy.setupApiMocks();
  });

  /**
   * CRITICAL PATH 1: Happy Path Video Processing
   * This is the primary user journey - if this fails, the app is broken
   */
  it("should complete the primary video processing workflow", () => {
    // This single test covers the most important user journey
    // Step 1: Enter URL
    cy.get('[data-testid="url-input"]').type(
      "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    );
    cy.get('[data-testid="extract-button"]').click();

    // Step 2: Verify metadata loads
    cy.wait("@getMetadata");
    cy.contains("E2E Test Video").should("be.visible");

    // Step 3: Configure and process
    cy.contains("720p").click();
    cy.get('[data-testid="start-time-input"]').clear().type("0:10");
    cy.get('[data-testid="end-time-input"]').clear().type("0:40");
    cy.get('[data-testid="create-clip-button"]').click();

    // Step 4: Verify completion
    cy.wait("@createJob");
    cy.wait("@getJobStatus");
    cy.get('[data-testid="download-button"]').should("be.visible");
  });

  /**
   * CRITICAL PATH 2: Error Recovery
   * Users must be able to recover from errors gracefully
   */
  it("should handle critical errors with recovery options", () => {
    // Test network failure recovery
    cy.intercept("GET", "/api/metadata*", { statusCode: 500 }).as(
      "serverError",
    );

    cy.get('[data-testid="url-input"]').type(
      "https://youtube.com/watch?v=test",
    );
    cy.get('[data-testid="extract-button"]').click();

    cy.wait("@serverError");
    cy.contains("error").should("be.visible");
    cy.get('[data-testid="retry-button"]').should("be.visible");
  });

  /**
   * CRITICAL PATH 3: Mobile Responsiveness
   * Mobile users are critical for business success
   */
  it("should work on mobile devices", () => {
    cy.viewport(375, 667); // iPhone SE

    cy.get('[data-testid="url-input"]').should("be.visible");
    cy.get('[data-testid="extract-button"]').should("be.visible");

    // Verify mobile-specific interactions work
    cy.get('[data-testid="url-input"]').type(
      "https://youtube.com/watch?v=mobile-test",
    );
    cy.get('[data-testid="extract-button"]').click();

    cy.wait("@getMetadata");
    cy.contains("E2E Test Video").should("be.visible");
  });
});

/**
 * CROSS-BROWSER CRITICAL TESTS
 * These run the same critical path across different browsers
 * Only testing what absolutely must work everywhere
 */
describe("Cross-Browser Critical Functionality", () => {
  beforeEach(() => {
    cy.visit("/");
    cy.setupApiMocks();
  });

  it("should work consistently across browsers", () => {
    // This test will be run by Cypress across different browsers
    // We only test the core functionality that must work everywhere

    // Basic functionality test
    cy.get('[data-testid="url-input"]').should("be.visible");
    cy.get('[data-testid="extract-button"]').should("be.visible");

    // Quick workflow verification
    cy.get('[data-testid="url-input"]').type(
      "https://youtube.com/watch?v=browser-test",
    );
    cy.get('[data-testid="extract-button"]').click();

    cy.wait("@getMetadata");
    cy.contains("E2E Test Video").should("be.visible");
  });
});
