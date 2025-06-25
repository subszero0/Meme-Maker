/// <reference types="cypress" />

describe("Video Processing E2E Workflow", () => {
  beforeEach(() => {
    cy.visit("/");
    cy.setupApiMocks();
  });

  describe("Complete Happy Path Workflow", () => {
    it("should process a video from URL input to download", () => {
      // Step 1: Verify initial state
      cy.contains("Enter a Video URL").should("be.visible");
      cy.get('[data-testid="url-input"]').should("be.visible");

      // Step 2: Enter valid YouTube URL
      const testUrl = "https://www.youtube.com/watch?v=dQw4w9WgXcQ";
      cy.get('[data-testid="url-input"]').type(testUrl);
      cy.get('[data-testid="extract-button"]').click();

      // Step 3: Wait for metadata and verify video details
      cy.wait("@getMetadata");
      cy.contains("E2E Test Video").should("be.visible");
      cy.contains("2:00").should("be.visible");

      // Step 4: Configure clip settings
      cy.contains("720p").click();
      cy.get('[data-testid="start-time-input"]').clear().type("0:10");
      cy.get('[data-testid="end-time-input"]').clear().type("0:40");

      // Step 5: Create clip job
      cy.get('[data-testid="create-clip-button"]').click();

      // Step 6: Verify processing UI
      cy.wait("@createJob");
      cy.contains("Processing").should("be.visible");

      // Step 7: Wait for completion
      cy.wait("@getJobStatus");
      cy.contains("Completed").should("be.visible");

      // Step 8: Verify download options
      cy.get('[data-testid="download-button"]').should("be.visible");
    });

    it("should handle different video platforms", () => {
      const platforms = [
        "https://www.youtube.com/watch?v=test",
        "https://youtu.be/test",
        "https://vimeo.com/123456789",
      ];

      platforms.forEach((url) => {
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
    it("should handle invalid URLs gracefully", () => {
      const invalidUrl = "https://invalid-video-url.com";

      cy.get('[data-testid="url-input"]').type(invalidUrl);
      cy.get('[data-testid="extract-button"]').click();

      cy.contains("Invalid video URL").should("be.visible");
    });

    it("should validate clip duration limits", () => {
      cy.get('[data-testid="url-input"]').type(
        "https://youtube.com/watch?v=test",
      );
      cy.get('[data-testid="extract-button"]').click();
      cy.wait("@getMetadata");

      // Try to set clip duration > 3 minutes
      cy.get('[data-testid="start-time-input"]').clear().type("0:00");
      cy.get('[data-testid="end-time-input"]').clear().type("4:00");

      cy.contains("Maximum clip duration is 3 minutes").should("be.visible");
    });

    it("should handle network timeouts with retry option", () => {
      cy.intercept("GET", "/api/metadata*", {
        delay: 30000,
        statusCode: 408,
        body: { error: "Request timeout" },
      }).as("slowMetadata");

      cy.get('[data-testid="url-input"]').type(
        "https://slow-response.com/video",
      );
      cy.get('[data-testid="extract-button"]').click();

      cy.contains("Request timeout").should("be.visible");
      cy.get('[data-testid="retry-button"]').should("be.visible");
    });
  });

  describe("User Experience and Accessibility", () => {
    it("should be keyboard navigable", () => {
      cy.get("body").tab();
      cy.focused().should("have.attr", "data-testid", "url-input");

      cy.focused().type("https://youtube.com/watch?v=test");
      cy.focused().tab();
      cy.focused().should("have.attr", "data-testid", "extract-button");

      cy.focused().type("{enter}");
      cy.wait("@getMetadata");
    });

    it("should have proper ARIA labels", () => {
      cy.get('[data-testid="url-input"]')
        .should("have.attr", "aria-label")
        .and("contain", "video URL");

      cy.get('[data-testid="extract-button"]').should(
        "have.attr",
        "role",
        "button",
      );
    });

    it("should be responsive on different viewports", () => {
      const viewports = [
        { width: 320, height: 568 }, // Mobile
        { width: 768, height: 1024 }, // Tablet
        { width: 1920, height: 1080 }, // Desktop
      ];

      viewports.forEach((viewport) => {
        cy.viewport(viewport.width, viewport.height);

        cy.get('[data-testid="url-input"]').should("be.visible");
        cy.get('[data-testid="extract-button"]').should("be.visible");
      });
    });
  });

  describe("Performance Testing", () => {
    it("should complete workflow within performance budget", () => {
      const startTime = Date.now();

      cy.get('[data-testid="url-input"]').type(
        "https://youtube.com/watch?v=test",
      );
      cy.get('[data-testid="extract-button"]').click();
      cy.wait("@getMetadata");

      cy.get('[data-testid="start-time-input"]').clear().type("0:10");
      cy.get('[data-testid="end-time-input"]').clear().type("0:40");
      cy.contains("720p").click();
      cy.get('[data-testid="create-clip-button"]').click();

      cy.wait("@createJob");
      cy.wait("@getJobStatus");

      cy.then(() => {
        const totalTime = Date.now() - startTime;
        expect(totalTime).to.be.lessThan(10000); // 10 second budget
      });
    });

    it("should show appropriate loading states", () => {
      cy.get('[data-testid="url-input"]').type(
        "https://youtube.com/watch?v=test",
      );

      cy.get('[data-testid="extract-button"]').click();
      cy.get('[data-testid="loading-spinner"]').should("be.visible");
      cy.get('[data-testid="extract-button"]').should("be.disabled");

      cy.wait("@getMetadata");
      cy.get('[data-testid="loading-spinner"]').should("not.exist");
    });
  });

  describe("Social Sharing Integration", () => {
    it("should generate correct sharing URLs", () => {
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
