/// <reference types="cypress" />

describe("Video Processing E2E Workflow", () => {
  beforeEach(() => {
    // Visit the app (baseUrl is configured in cypress.config.ts)
    cy.visit("/");

    // Set up API mocks for consistent testing
    cy.setupApiMocks();
  });

  describe("Complete Happy Path Workflow", () => {
    it("should process a video from URL input to download", () => {
      // Following Cypress best practices: test one main workflow per test

      // Step 1: Verify initial state
      cy.contains("Enter a Video URL").should("be.visible");
      cy.get('[data-testid="url-input"]').should("be.visible");
      cy.get('[data-testid="extract-button"]').should("be.visible");

      // Step 2: Enter valid YouTube URL
      const testUrl = "https://www.youtube.com/watch?v=dQw4w9WgXcQ";
      cy.get('[data-testid="url-input"]').type(testUrl);
      cy.get('[data-testid="extract-button"]').click();

      // Step 3: Wait for metadata to load and verify video details
      cy.wait("@getMetadata");
      cy.contains("E2E Test Video").should("be.visible");
      cy.contains("2:00").should("be.visible"); // Duration display
      cy.contains("Test Channel").should("be.visible");

      // Step 4: Verify format selector is populated
      cy.get('[data-testid="format-selector"]').should("be.visible");
      cy.contains("360p").should("be.visible");
      cy.contains("720p").should("be.visible");

      // Step 5: Configure clip settings
      // Select 720p resolution
      cy.contains("720p").click();

      // Set custom start and end times
      cy.get('[data-testid="start-time-input"]').clear().type("0:10");
      cy.get('[data-testid="end-time-input"]').clear().type("0:40");

      // Step 6: Create clip job
      cy.get('[data-testid="create-clip-button"]').click();

      // Step 7: Verify job creation and processing UI
      cy.wait("@createJob");
      cy.contains("Processing").should("be.visible");

      // Verify progress indicators
      cy.get('[data-testid="progress-bar"]').should("be.visible");
      cy.get('[data-testid="processing-stage"]').should("be.visible");

      // Step 8: Wait for job completion
      cy.wait("@getJobStatus");
      cy.contains("Completed").should("be.visible");

      // Step 9: Verify download and sharing options
      cy.get('[data-testid="download-button"]').should("be.visible");
      cy.get('[data-testid="copy-link-button"]').should("be.visible");
      cy.get('[data-testid="share-options"]').should("be.visible");

      // Step 10: Test download functionality
      cy.get('[data-testid="download-button"]').click();

      // Verify cleanup API call
      cy.wait("@deleteClip");
    });

    it("should handle different video platforms", () => {
      const platforms = [
        "https://www.youtube.com/watch?v=test",
        "https://youtu.be/test",
        "https://vimeo.com/123456789",
      ];

      platforms.forEach((url) => {
        // Reset between iterations
        cy.reload();
        cy.setupApiMocks();

        cy.get('[data-testid="url-input"]').type(url);
        cy.get('[data-testid="extract-button"]').click();

        cy.wait("@getMetadata");
        cy.contains("E2E Test Video").should("be.visible");
      });
    });
  });

  describe("Error Handling Scenarios", () => {
    it("should handle invalid video URLs gracefully", () => {
      const invalidUrl = "https://invalid-video-url.com";

      cy.get('[data-testid="url-input"]').type(invalidUrl);
      cy.get('[data-testid="extract-button"]').click();

      // Should show error message
      cy.contains("Invalid video URL").should("be.visible");
      cy.get('[data-testid="try-again-button"]').should("be.visible");
    });

    it("should validate clip duration limits", () => {
      // Enter valid URL first
      cy.get('[data-testid="url-input"]').type(
        "https://youtube.com/watch?v=test",
      );
      cy.get('[data-testid="extract-button"]').click();

      cy.wait("@getMetadata");

      // Try to set clip duration > 3 minutes (180 seconds)
      cy.get('[data-testid="start-time-input"]').clear().type("0:00");
      cy.get('[data-testid="end-time-input"]').clear().type("4:00"); // 240 seconds

      // Should show validation error
      cy.contains("Maximum clip duration is 3 minutes").should("be.visible");
      cy.get('[data-testid="create-clip-button"]').should("be.disabled");
    });

    it("should handle network timeouts and provide retry option", () => {
      // Mock slow response
      cy.intercept("GET", "/api/metadata*", {
        delay: 30000, // 30 second delay
        statusCode: 408,
        body: { error: "Request timeout" },
      }).as("slowMetadata");

      cy.get('[data-testid="url-input"]').type(
        "https://slow-response.com/video",
      );
      cy.get('[data-testid="extract-button"]').click();

      // Should show timeout error and retry option
      cy.contains("Request timeout").should("be.visible");
      cy.get('[data-testid="retry-button"]').should("be.visible");
    });
  });

  describe("User Experience and Accessibility", () => {
    it("should be keyboard navigable", () => {
      // Test keyboard navigation through the form
      cy.get("body").tab(); // Focus first element
      cy.focused().should("have.attr", "data-testid", "url-input");

      cy.focused().type("https://youtube.com/watch?v=test");
      cy.focused().tab(); // Move to extract button
      cy.focused().should("have.attr", "data-testid", "extract-button");

      cy.focused().type("{enter}"); // Submit with keyboard
      cy.wait("@getMetadata");
    });

    it("should have proper ARIA labels and roles", () => {
      cy.get('[data-testid="url-input"]')
        .should("have.attr", "aria-label")
        .and("contain", "video URL");

      cy.get('[data-testid="extract-button"]').should(
        "have.attr",
        "role",
        "button",
      );

      // Check for proper heading structure
      cy.get("h1").should("exist");
    });

    it("should be responsive on different viewport sizes", () => {
      const viewports = [
        { width: 320, height: 568 }, // iPhone SE
        { width: 768, height: 1024 }, // iPad
        { width: 1920, height: 1080 }, // Desktop
      ];

      viewports.forEach((viewport) => {
        cy.viewport(viewport.width, viewport.height);

        // Verify key elements are visible and properly sized
        cy.get('[data-testid="url-input"]').should("be.visible");
        cy.get('[data-testid="extract-button"]').should("be.visible");

        // On mobile, elements should stack vertically
        if (viewport.width < 768) {
          cy.get('[data-testid="main-container"]').should(
            "have.css",
            "flex-direction",
            "column",
          );
        }
      });
    });
  });

  describe("Performance and Loading States", () => {
    it("should show appropriate loading states during processing", () => {
      cy.get('[data-testid="url-input"]').type(
        "https://youtube.com/watch?v=test",
      );

      // Measure and verify extraction loading state
      cy.get('[data-testid="extract-button"]').click();
      cy.get('[data-testid="loading-spinner"]').should("be.visible");
      cy.get('[data-testid="extract-button"]').should("be.disabled");

      cy.wait("@getMetadata");
      cy.get('[data-testid="loading-spinner"]').should("not.exist");
    });

    it("should complete workflow within performance budget", () => {
      // Measure total workflow time
      const startTime = Date.now();

      cy.get('[data-testid="url-input"]').type(
        "https://youtube.com/watch?v=test",
      );
      cy.get('[data-testid="extract-button"]').click();

      cy.wait("@getMetadata");

      // Configure clip
      cy.get('[data-testid="start-time-input"]').clear().type("0:10");
      cy.get('[data-testid="end-time-input"]').clear().type("0:40");
      cy.contains("720p").click();

      cy.get('[data-testid="create-clip-button"]').click();
      cy.wait("@createJob");
      cy.wait("@getJobStatus");

      // Verify total time is within budget
      cy.then(() => {
        const endTime = Date.now();
        const totalTime = endTime - startTime;
        expect(totalTime).to.be.lessThan(10000); // 10 second budget
      });
    });
  });

  describe("Social Sharing Integration", () => {
    it("should generate correct sharing URLs for different platforms", () => {
      // Complete workflow to get to sharing state
      cy.get('[data-testid="url-input"]').type(
        "https://youtube.com/watch?v=test",
      );
      cy.get('[data-testid="extract-button"]').click();
      cy.wait("@getMetadata");

      cy.get('[data-testid="start-time-input"]').clear().type("0:10");
      cy.get('[data-testid="end-time-input"]').clear().type("0:40");
      cy.get('[data-testid="create-clip-button"]').click();

      cy.wait("@createJob");
      cy.wait("@getJobStatus");

      // Test social media sharing buttons
      const socialPlatforms = [
        { platform: "twitter", domain: "twitter.com" },
        { platform: "facebook", domain: "facebook.com" },
        { platform: "whatsapp", domain: "whatsapp.com" },
        { platform: "reddit", domain: "reddit.com" },
      ];

      socialPlatforms.forEach(({ platform, domain }) => {
        cy.get(`[data-testid="share-${platform}"]`)
          .should("have.attr", "href")
          .and("contain", domain);
      });
    });

    it("should copy download link to clipboard", () => {
      // Complete workflow
      cy.get('[data-testid="url-input"]').type(
        "https://youtube.com/watch?v=test",
      );
      cy.get('[data-testid="extract-button"]').click();
      cy.wait("@getMetadata");
      cy.get('[data-testid="create-clip-button"]').click();
      cy.wait("@createJob");
      cy.wait("@getJobStatus");

      // Mock clipboard API
      cy.window().then((win) => {
        cy.stub(win.navigator.clipboard, "writeText").resolves();
      });

      cy.get('[data-testid="copy-link-button"]').click();
      cy.contains("Link copied").should("be.visible");
    });
  });
});
