/**
 * Simplified Smoke Tests - Critical User Flows Only
 * 
 * Reduced from 25+ tests to 3 focused tests following TestsToDo.md Phase 1.4:
 * - Core user flow (80% of business value)
 * - Invalid URL handling (critical error case)
 * - Terms acceptance (legal requirement)
 * 
 * Removed: Mobile tests, accessibility tests, performance tests, deep linking
 */

describe("🚀 Critical User Flows", () => {
  const TEST_YOUTUBE_URL = "https://www.youtube.com/watch?v=dQw4w9WgXcQ";
  const INVALID_URL = "https://example.com/not-a-video";

  beforeEach(() => {
    cy.visit("/");

    // Mock API responses for reliable testing
    cy.intercept("POST", "/api/v1/metadata", (req) => {
      if (req.body.url.includes("youtube.com") || req.body.url.includes("youtu.be")) {
        req.reply({
          statusCode: 200,
          body: {
            url: req.body.url,
            title: "Rick Astley - Never Gonna Give You Up",
            duration: 212,
          },
        });
      } else {
        req.reply({
          statusCode: 400,
          body: { detail: "Invalid or unsupported video URL" },
        });
      }
    }).as("fetchMetadata");

    cy.intercept("POST", "/api/v1/jobs", {
      statusCode: 200,
      body: { jobId: "test-job-123" },
    }).as("createJob");

    cy.intercept("GET", "/api/v1/jobs/test-job-123", {
      statusCode: 200,
      body: {
        status: "done",
        progress: 100,
        download_url: "https://example.com/download/test-video.mp4",
      },
    }).as("jobStatus");
  });

  it("should complete the core video clipping flow", () => {
    // Arrange & Act: Paste URL and get metadata
    cy.get('[data-testid="url-input"]').type(TEST_YOUTUBE_URL);
    cy.get('[data-testid="analyze-button"]').click();

    // Assert: Metadata loads
    cy.get('[data-testid="video-metadata"]', { timeout: 10000 }).should("be.visible");
    cy.get('[data-testid="video-title"]').should("contain.text", "Rick Astley");

    // Act: Set trim points (5 second clip)
    cy.get('[data-testid="start-time-input"]').clear().type("00:05.000");
    cy.get('[data-testid="end-time-input"]').clear().type("00:10.000");

    // Assert: Duration calculated correctly
    cy.get('[data-testid="clip-duration"]').should("contain.text", "5 seconds");

    // Act: Accept terms and create job
    cy.get('[data-testid="terms-checkbox"]').check();
    cy.get('[data-testid="create-clip-button"]').click();

    // Assert: Job created and download ready
    cy.wait("@createJob");
    cy.wait("@jobStatus");
    
    cy.get('[data-testid="download-btn"]', { timeout: 30000 }).should("be.visible");
    cy.contains("Clip ready!").should("be.visible");
    
    // Assert: Download link is correct
    cy.get('[data-testid="download-btn"]')
      .invoke("attr", "href")
      .should("include", "example.com/download/test-video.mp4");
  });

  it("should handle invalid URLs gracefully", () => {
    // Act: Submit invalid URL
    cy.get('[data-testid="url-input"]').type(INVALID_URL);
    cy.get('[data-testid="analyze-button"]').click();

    // Assert: Error message shown
    cy.get('[data-testid="url-error"]', { timeout: 10000 })
      .should("be.visible")
      .and("contain.text", "valid video URL");
  });

  it("should enforce terms acceptance", () => {
    // Arrange: Navigate to trim page with valid URL
    cy.visit(`/trim?url=${encodeURIComponent(TEST_YOUTUBE_URL)}`);
    cy.get('[data-testid="video-metadata"]', { timeout: 10000 }).should("be.visible");

    // Act: Try to create job without accepting terms
    cy.get('[data-testid="start-time-input"]').clear().type("00:05.000");
    cy.get('[data-testid="end-time-input"]').clear().type("00:10.000");

    // Assert: Create button should be disabled without terms
    cy.get('[data-testid="create-clip-button"]').should("be.disabled");

    // Act: Accept terms
    cy.get('[data-testid="terms-checkbox"]').check();

    // Assert: Create button should now be enabled
    cy.get('[data-testid="create-clip-button"]').should("not.be.disabled");
  });
}); 