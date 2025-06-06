describe("🚀 Smoke Test - Critical User Flows", () => {
  const TEST_YOUTUBE_URL = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"; // Rick Roll - short and reliable
  const INVALID_URL = "https://example.com/not-a-video";
  const PRIVATE_VIDEO_URL =
    "https://www.youtube.com/watch?v=invalid-private-video";

  beforeEach(() => {
    // Start from homepage
    cy.visit("/");

    // Ensure API is healthy before running tests
    cy.request("GET", "http://localhost:8000/health").then((response) => {
      expect(response.status).to.eq(200);
    });
  });

  describe("✅ Happy Path - Complete Video Clip Flow", () => {
    it("should successfully clip a YouTube video from start to finish", () => {
      // Step 1: Paste URL and get metadata
      cy.get('[data-testid="url-input"]').as('urlInput');
      cy.get('@urlInput').type(TEST_YOUTUBE_URL);
      cy.get('@urlInput').should("have.value", TEST_YOUTUBE_URL);

      cy.get('[data-testid="analyze-button"]').click();

      // Wait for metadata to load
      cy.get('[data-testid="video-metadata"]', { timeout: 10000 }).should(
        "be.visible",
      );

      cy.get('[data-testid="video-title"]').should(
        "contain.text",
        "Rick Astley",
      );

      // Step 2: Set trim points (5 seconds clip)
      cy.get('[data-testid="start-time"]').as('startInput');
      cy.get('@startInput').clear();
      cy.get('@startInput').type("00:05.000");

      cy.get('[data-testid="end-time"]').as('endInput');
      cy.get('@endInput').clear();
      cy.get('@endInput').type("00:10.000");

      // Verify duration is calculated correctly
      cy.get('[data-testid="clip-duration-text"]').as('clipDuration');
      cy.get('@clipDuration').should(
        "contain.text",
        "5.0 seconds",
      );

      // Step 3: Accept terms and create job
      cy.get('[data-testid="rights-checkbox"]').as('termsCheckbox');
      cy.get('@termsCheckbox').check();
      cy.get('@termsCheckbox').should("be.checked");

      cy.get('[data-testid="clip-btn"]').click();

      // Step 4: Wait for job completion and download
      cy.get('[data-testid="job-status"]', { timeout: 30000 }).should(
        "contain.text",
        "ready",
      );

      cy.get('[data-testid="download-btn"]').as('downloadBtn');
      cy.get('@downloadBtn').should("be.visible");
      cy.get('@downloadBtn').should("not.be.disabled");

      // Verify download link functionality
      cy.get('@downloadBtn')
        .invoke("attr", "href")
        .should("contain", ".mp4");

      // Test the download (verify it's a valid presigned URL)
      cy.get('@downloadBtn')
        .invoke("attr", "href")
        .then((downloadUrl) => {
          cy.request("HEAD", downloadUrl as string).then((response) => {
            expect(response.status).to.eq(200);
            expect(response.headers["content-type"]).to.contain("video");
          });
        });

      // Verify auto-copy functionality
      cy.get('[data-testid="copy-feedback"]').should(
        "contain.text",
        "Copied to clipboard",
      );
    });

    it("should handle slider-based trimming correctly", () => {
      // Navigate to trim page with URL
      cy.visit(`/trim?url=${encodeURIComponent(TEST_YOUTUBE_URL)}`);

      // Wait for video to load
      cy.get('[data-testid="video-player"]', { timeout: 10000 }).should(
        "be.visible",
      );

      // Test slider interaction
      cy.get('[data-testid="timeline-slider"]').should("be.visible");

      // Simulate dragging start handle
      cy.get('[data-testid="slider-handle-0"]')
        .trigger("mousedown", { which: 1 })
        .trigger("mousemove", { clientX: 100 })
        .trigger("mouseup");

      // Simulate dragging end handle
      cy.get('[data-testid="slider-handle-1"]')
        .trigger("mousedown", { which: 1 })
        .trigger("mousemove", { clientX: 200 })
        .trigger("mouseup");

      // Verify time inputs update
      cy.get('[data-testid="start-time"]').should(
        "not.have.value",
        "00:00.000",
      );

      cy.get('[data-testid="end-time"]').should(
        "not.have.value",
        "00:05.000",
      );
    });
  });

  describe("❌ Error State Validation", () => {
    it("should reject clips longer than 30 minutes", () => {
      // Navigate with a longer video URL
      cy.visit(`/trim?url=${encodeURIComponent(TEST_YOUTUBE_URL)}`);

      cy.get('[data-testid="video-metadata"]', { timeout: 10000 }).should(
        "be.visible",
      );

      // Try to set a 31-minute clip
      cy.get('[data-testid="start-time"]').clear().type("00:00.000");

      cy.get('[data-testid="end-time"]').clear().type("31:00.000");

      // Should show error message
      cy.get('[data-testid="duration-error-message"]')
        .should("be.visible")
        .and("contain.text", "30 minutes or less");

      // Create button should be disabled
      cy.get('[data-testid="clip-btn"]').should("be.disabled");
    });

    it("should handle invalid URLs gracefully", () => {
      cy.get('[data-testid="url-input"]').type(INVALID_URL);

      cy.get('[data-testid="analyze-button"]').click();

      // Should show error message
      cy.get('[data-testid="notification-message"]', { timeout: 10000 })
        .should("be.visible")
        .and("contain.text", "Failed to load video");
    });

    it("should enforce terms acceptance", () => {
      cy.visit(`/trim?url=${encodeURIComponent(TEST_YOUTUBE_URL)}`);

      cy.get('[data-testid="video-metadata"]', { timeout: 10000 }).should(
        "be.visible",
      );

      // Set valid trim points
      cy.get('[data-testid="start-time"]').clear().type("00:05.000");

      cy.get('[data-testid="end-time"]').clear().type("00:10.000");

      // Don't check terms checkbox
      cy.get('[data-testid="rights-checkbox"]').should("not.be.checked");

      // Button should be disabled
      cy.get('[data-testid="clip-btn"]').should("be.disabled");

      // Show error message
      cy.get('[data-testid="submit-error-message"]').should(
        "contain.text",
        "You must accept the terms",
      );
    });

    it("should handle queue full scenario", () => {
      // Mock queue full response
      cy.intercept("POST", "/api/v1/jobs", {
        statusCode: 429,
        body: { detail: "Queue is full. Please try again later." },
      }).as("queueFull");

      cy.visit(`/trim?url=${encodeURIComponent(TEST_YOUTUBE_URL)}`);

      cy.get('[data-testid="video-metadata"]', { timeout: 10000 }).should(
        "be.visible",
      );

      // Set valid clip and accept terms
      cy.get('[data-testid="start-time"]').clear().type("00:05.000");

      cy.get('[data-testid="end-time"]').clear().type("00:10.000");

      cy.get('[data-testid="rights-checkbox"]').check();

      cy.get('[data-testid="clip-btn"]').click();

      cy.wait("@queueFull");

      // Should show queue full error
      cy.get('[data-testid="queue-full-banner"]')
        .should("be.visible")
        .and("contain.text", "queue is full");
    });
  });

  describe("📱 Mobile Responsiveness", () => {
    beforeEach(() => {
      // Test on mobile viewport
      cy.viewport(360, 640);
    });

    it("should have touch-friendly controls on mobile", () => {
      cy.visit(`/trim?url=${encodeURIComponent(TEST_YOUTUBE_URL)}`);

      cy.get('[data-testid="video-metadata"]', { timeout: 10000 }).should(
        "be.visible",
      );

      // Slider handles should be large enough for touch
      cy.get('[data-testid="slider-handle-0"]')
        .should("have.css", "width")
        .and("match", /^(1[6-9]|[2-9]\d|\d{3,})px$/); // >= 16px

      cy.get('[data-testid="slider-handle-1"]')
        .should("have.css", "height")
        .and("match", /^(1[6-9]|[2-9]\d|\d{3,})px$/); // >= 16px

      // Buttons should be touch-friendly
      cy.get('[data-testid="clip-btn"]')
        .should("have.css", "min-height")
        .and("match", /^(4[4-9]|[5-9]\d|\d{3,})px$/); // >= 44px
    });

    it("should handle mobile layout correctly", () => {
      cy.visit("/");

      // Main container should not overflow
      cy.get("body").should("have.css", "overflow-x", "hidden");

      // Navigation should be responsive
      cy.get('[data-testid="main-nav"]').should("be.visible");

      // Form elements should be properly sized
      cy.get('[data-testid="url-input"]')
        .should("be.visible")
        .and("have.css", "width")
        .and("not.eq", "0px");

      cy.get('[data-testid="video-metadata"]', { timeout: 10000 }).should(
        "be.visible",
      );

      cy.get('[data-testid="start-time"]').should("be.visible");
      cy.get('[data-testid="end-time"]').should("be.visible");

      // Verify focus is managed correctly
      cy.get('[data-testid="start-time"]').focus();
      cy.get('[data-testid="start-time"]').should("have.focus");
    });
  });

  describe("♿ Accessibility Validation", () => {
    it("should have proper focus management", () => {
      cy.visit("/");

      // Tab through key elements using keyboard commands
      cy.get('[data-testid="url-input"]').as('urlInput');
      cy.get('@urlInput').focus();
      cy.focused().should("have.attr", "data-testid", "url-input");

      // Enter URL to enable the analyze button
      cy.get('@urlInput').type(TEST_YOUTUBE_URL);

      // Wait for validation to complete and button to be enabled
      cy.get('[data-testid="analyze-button"]').should("not.be.disabled", { timeout: 10000 });
      cy.get('[data-testid="analyze-button"]').focus();
      cy.focused().should("have.attr", "data-testid", "analyze-button");

      // Focus should be visible (check for outline or box-shadow)
      cy.focused().then(($el) => {
        const outlineStyle = $el.css("outline-style");
        const boxShadow = $el.css("box-shadow");
        expect(outlineStyle !== "none" || boxShadow !== "none").to.be.true;
      });
    });

    it("should have proper ARIA labels", () => {
      cy.visit(`/trim?url=${encodeURIComponent(TEST_YOUTUBE_URL)}`);

      cy.get('[data-testid="video-metadata"]', { timeout: 10000 }).should(
        "be.visible",
      );

      // Slider should have proper ARIA attributes
      cy.get('[data-testid="timeline-slider"]')
        .should("have.attr", "role", "slider")
        .and("have.attr", "aria-label");

      // Form controls should be properly labeled
      cy.get('[data-testid="start-time"]').should(
        "have.attr",
        "aria-label",
        "Start time",
      );
      cy.get('[data-testid="end-time"]').should(
        "have.attr",
        "aria-label",
        "End time",
      );
      cy.get('[data-testid="rights-checkbox"]').should(
        "have.attr",
        "aria-label",
        "I have the rights to use this video",
      );
      cy.get('[data-testid="clip-btn"]').should(
        "have.attr",
        "aria-label",
        "Create and download clip",
      );
    });
  });

  describe("🔗 Link Sharing & Deep Links", () => {
    it("should handle direct navigation to trim page", () => {
      const testUrl = encodeURIComponent(TEST_YOUTUBE_URL);
      cy.visit(`/trim?url=${testUrl}&start=5&end=10`);

      // Should automatically load video metadata
      cy.get('[data-testid="video-metadata"]', { timeout: 10000 }).should(
        "be.visible",
      );

      // Should pre-populate trim points from URL params
      cy.get('[data-testid="start-time"]').should(
        "have.value",
        "00:05.000",
      );

      cy.get('[data-testid="end-time"]').should("have.value", "00:10.000");
    });

    it("should update URL when trim points change", () => {
      cy.visit(`/trim?url=${encodeURIComponent(TEST_YOUTUBE_URL)}`);

      cy.get('[data-testid="video-metadata"]', { timeout: 10000 }).should(
        "be.visible",
      );

      cy.get('[data-testid="start-time"]').clear().type("00:15.000");

      // URL should update with new start time
      cy.url().should("include", "start=15");
    });
  });

  describe("⚡ Performance Validation", () => {
    it("should load initial page quickly", () => {
      const startTime = Date.now();

      cy.visit("/").then(() => {
        const loadTime = Date.now() - startTime;
        expect(loadTime).to.be.lessThan(3000); // 3 second threshold
      });

      // Critical content should be visible quickly
      cy.get('[data-testid="url-input"]', { timeout: 2000 }).should(
        "be.visible",
      );
    });

    it("should handle multiple rapid interactions", () => {
      cy.visit(`/trim?url=${encodeURIComponent(TEST_YOUTUBE_URL)}`);

      cy.get('[data-testid="video-metadata"]', { timeout: 10000 }).should(
        "be.visible",
      );

      for (let i = 1; i <= 5; i++) {
        cy.get('[data-testid="start-time"]')
          .clear()
          .type(`00:0${i}.000`);
        cy.get('[data-testid="end-time"]')
          .clear()
          .type(`00:1${i}.000`);
      }

      cy.get('[data-testid="clip-duration-text"]').should(
        "contain.text",
        "10.0 seconds",
      );
    });
  });
});
