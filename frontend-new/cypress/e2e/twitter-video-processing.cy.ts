/// <reference types="cypress" />

describe("Twitter Video Processing", () => {
  beforeEach(() => {
    cy.visit("/");
  });

  it("should process a Twitter video URL", () => {
    // Check if URL input accepts Twitter URLs
    cy.get('[data-cy="url-input"]')
      .type("https://twitter.com/user/status/123456789")
      .should("have.value", "https://twitter.com/user/status/123456789");

    // Verify placeholder includes Twitter
    cy.get('[data-cy="url-input"]')
      .should("have.attr", "placeholder")
      .and("match", /x\.com/i);

    // Check validation message includes Twitter/X
    cy.get("body").should("contain.text", "Twitter");
  });

  it("should handle X.com domains", () => {
    cy.get('[data-cy="url-input"]')
      .type("https://x.com/user/status/123456789")
      .should("have.value", "https://x.com/user/status/123456789");
  });

  it("should handle mobile Twitter domains", () => {
    cy.get('[data-cy="url-input"]')
      .type("https://mobile.twitter.com/user/status/123456789")
      .should("have.value", "https://mobile.twitter.com/user/status/123456789");
  });

  // Mock test for actual processing workflow
  it("should mock Twitter video processing workflow", () => {
    // Intercept API calls for Twitter metadata
    cy.intercept("POST", "**/api/v1/metadata", {
      statusCode: 200,
      body: {
        title: "Test Twitter Video",
        duration: 30,
        thumbnail_url: "https://example.com/thumb.jpg",
        resolutions: ["720p", "480p", "360p"],
        platform: "twitter"
      }
    }).as("getMetadata");

    // Intercept job creation
    cy.intercept("POST", "**/api/v1/jobs", {
      statusCode: 201,
      body: {
        job_id: "twitter_test_123",
        status: "queued"
      }
    }).as("createJob");

    // Enter Twitter URL
    cy.get('[data-cy="url-input"]')
      .type("https://twitter.com/user/status/123456789");

    // Submit form
    cy.get('[data-cy="submit-button"]').click();

    // Wait for metadata call
    cy.wait("@getMetadata");

    // Verify video player shows metadata
    cy.get('[data-cy="video-title"]').should("contain", "Test Twitter Video");
    cy.get('[data-cy="video-duration"]').should("contain", "30");

    // Start processing
    cy.get('[data-cy="process-button"]').click();

    // Wait for job creation
    cy.wait("@createJob");

    // Verify processing starts
    cy.get('[data-cy="processing-status"]').should("contain", "Processing");
  });
}); 