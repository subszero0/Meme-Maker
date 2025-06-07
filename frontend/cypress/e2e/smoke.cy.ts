describe("🚀 Smoke Test - Critical User Flows", () => {
  const TEST_YOUTUBE_URL = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"; // Rick Roll - short and reliable
  const INVALID_URL = "https://example.com/not-a-video";
  const PRIVATE_VIDEO_URL =
    "https://www.youtube.com/watch?v=invalid-private-video";

  beforeEach(() => {
    // Start from homepage
    cy.visit("/");

    // Add API interceptors for more reliable testing
    cy.intercept("POST", "/api/v1/metadata", (req) => {
      if (req.body.url.includes('youtube.com') || req.body.url.includes('youtu.be')) {
        req.reply({
          statusCode: 200,
          body: {
            url: req.body.url,
            title: "Rick Astley - Never Gonna Give You Up",
            duration: 212
          }
        });
      } else {
        req.reply({
          statusCode: 400,
          body: { detail: "Invalid or unsupported video URL" }
        });
      }
    }).as('fetchMetadata');

    cy.intercept("POST", "/api/v1/jobs", {
      statusCode: 200,
      body: { jobId: "test-job-123" }
    }).as('createJob');

    cy.intercept("GET", "/api/v1/jobs/test-job-123", {
      statusCode: 200,
      body: { 
        status: "done", 
        progress: 100,
        url: "https://example.com/download/test-video.mp4"
      }
    }).as('jobStatus');

    // Ensure API is healthy before running tests (with fallback)
    cy.request({
      method: "GET", 
      url: "http://localhost:8000/health",
      failOnStatusCode: false
    }).then((response) => {
      if (response.status === 200) {
        cy.log("✅ Backend API is available");
      } else {
        cy.log("⚠️ Backend API not available, using mocked responses");
      }
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

      // Step 2: Set trim points (5 seconds clip) - using correct format with milliseconds
      cy.get('[data-testid="start-time-input"]').as('startInput');
      cy.get('@startInput').clear();
      cy.get('@startInput').type("00:05.000");

      cy.get('[data-testid="end-time-input"]').as('endInput');
      cy.get('@endInput').clear();
      cy.get('@endInput').type("00:10.000");

      // Verify duration is calculated correctly
      cy.get('[data-testid="clip-duration"]').as('clipDuration');
      cy.get('@clipDuration').should(
        "contain.text",
        "5 seconds",
      );

      // Step 3: Accept terms and create job
      cy.get('[data-testid="terms-checkbox"]').as('termsCheckbox');
      cy.get('@termsCheckbox').check();
      cy.get('@termsCheckbox').should("be.checked");

      cy.get('[data-testid="create-clip-button"]').click();

      // Step 4: Wait for download modal to appear (homepage flow)
      cy.get('[data-testid="download-btn"]', { timeout: 30000 }).as('downloadBtn');
      cy.get('@downloadBtn').should("be.visible");
      cy.get('@downloadBtn').should("not.be.disabled");

      // Verify the modal title is shown
      cy.contains("Clip ready!").should("be.visible");

      // Verify download link functionality
      cy.get('@downloadBtn')
        .invoke("attr", "href")
        .should("include", "example.com/download/test-video.mp4");

      // Verify download button text
      cy.get('@downloadBtn').should("contain.text", "Download Now");
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
      cy.get('[data-testid="start-handle"]')
        .trigger("mousedown", { which: 1 })
        .trigger("mousemove", { clientX: 100 })
        .trigger("mouseup");

      // Simulate dragging end handle
      cy.get('[data-testid="end-handle"]')
        .trigger("mousedown", { which: 1 })
        .trigger("mousemove", { clientX: 200 })
        .trigger("mouseup");

      // Verify time inputs update
      cy.get('[data-testid="start-time-input"]').should(
        "not.have.value",
        "00:00:00",
      );

      cy.get('[data-testid="end-time-input"]').should(
        "not.have.value",
        "00:00:05",
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

      // Try to set a 31-minute clip - TrimPageContent expects HH:MM:SS format
      cy.get('[data-testid="start-time-input"]').clear().type("00:00:00");

      cy.get('[data-testid="end-time-input"]').clear().type("00:31:00");

      // Should show error message from TrimPageContent
      cy.get('[data-testid="duration-error"]')
        .should("be.visible")
        .and("contain.text", "thirty minutes");

      // Create button should be disabled
      cy.get('[data-testid="create-clip-button"]').should("be.disabled");
    });

    it("should handle invalid URLs gracefully", () => {
      cy.get('[data-testid="url-input"]').type(INVALID_URL);

      cy.get('[data-testid="analyze-button"]').click();

      // Should show error message
      cy.get('[data-testid="url-error"]', { timeout: 10000 })
        .should("be.visible")
        .and("contain.text", "valid video URL");
    });

    it("should enforce terms acceptance", () => {
      cy.visit(`/trim?url=${encodeURIComponent(TEST_YOUTUBE_URL)}`);

      cy.get('[data-testid="video-metadata"]', { timeout: 10000 }).should(
        "be.visible",
      );

      // Set valid trim points - TrimPageContent expects HH:MM:SS format
      cy.get('[data-testid="start-time-input"]').clear().type("00:00:05");

      cy.get('[data-testid="end-time-input"]').clear().type("00:00:10");

      // Don't check terms checkbox
      cy.get('[data-testid="terms-checkbox"]').should("not.be.checked");

      // Button should be disabled
      cy.get('[data-testid="create-clip-button"]').should("be.disabled");

      // Show error message
      cy.get('[data-testid="terms-error"]').should(
        "contain.text",
        "accept the terms",
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

      // Set valid clip and accept terms - TrimPageContent expects HH:MM:SS format
      cy.get('[data-testid="start-time-input"]').clear().type("00:00:05");

      cy.get('[data-testid="end-time-input"]').clear().type("00:00:10");

      cy.get('[data-testid="terms-checkbox"]').check();

      cy.get('[data-testid="create-clip-button"]').click();

      cy.wait("@queueFull");

      // Should show queue full error
      cy.get('[data-testid="queue-error"]')
        .should("be.visible")
        .and("contain.text", "Try again in a minute");
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
      cy.get('[data-testid="start-handle"]')
        .should("have.css", "width")
        .and("match", /^(4[4-9]|[5-9]\d|\d{3,})px$/); // >= 44px

      cy.get('[data-testid="end-handle"]')
        .should("have.css", "height")
        .and("match", /^(4[4-9]|[5-9]\d|\d{3,})px$/); // >= 44px

      // Buttons should be touch-friendly
      cy.get('[data-testid="create-clip-button"]')
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

      // Wait for button to be enabled before trying to focus
      cy.get('[data-testid="analyze-button"]').should("not.be.disabled");
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
      cy.get('[data-testid="start-time-input"]').then(($el) => {
        expect($el.attr("aria-label") || $el.attr("aria-labelledby")).to.exist;
      });

      cy.get('[data-testid="terms-checkbox"]').should(
        "have.attr",
        "aria-describedby",
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

      // Should pre-populate trim points from URL params (TrimPageContent format)
      cy.get('[data-testid="start-time-input"]').should(
        "have.value",
        "00:00:05",
      );

      cy.get('[data-testid="end-time-input"]').should("have.value", "00:00:10");
    });

    it("should update URL when trim points change", () => {
      cy.visit(`/trim?url=${encodeURIComponent(TEST_YOUTUBE_URL)}`);

      cy.get('[data-testid="video-metadata"]', { timeout: 10000 }).should(
        "be.visible",
      );

      // Use correct TrimPageContent format (HH:MM:SS)
      cy.get('[data-testid="start-time-input"]').clear().type("00:00:15");

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

      // Rapidly change trim points using correct TrimPageContent format (HH:MM:SS)
      for (let i = 5; i < 15; i++) {
        cy.get('[data-testid="start-time-input"]')
          .clear()
          .type(`00:00:${i.toString().padStart(2, "0")}`);
      }

      // Should handle all updates without errors
      cy.get('[data-testid="clip-duration"]').should("be.visible");
    });
  });
});
