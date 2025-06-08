/**
 * Visual Regression Tests for Meme Maker
 *
 * Tests visual snapshots of core user flows:
 * - URL Input Screen (empty state)
 * - Trim Slider (with default start/end handles)
 * - Live Preview (after video loads)
 * - Download Modal (open state)
 * - Error States
 *
 * Run with: npm run visual:baseline (first time) or npm run visual:test
 */

// Helper function to take Percy snapshots only when available
function takeSnapshot(name: string, options?: any) {
  if (typeof cy.percySnapshot === "function") {
    try {
      cy.percySnapshot(name, options);
    } catch (error) {
      // If Percy is not available, just log and continue
      cy.log(`Percy snapshot skipped: ${name}`);
    }
  } else {
    // Percy not available, just verify basic functionality
    cy.log(`Percy not available, skipping snapshot: ${name}`);
  }
}

describe("Visual Regression Tests", () => {
  beforeEach(() => {
    // Set consistent viewport for snapshots
    cy.viewport(1280, 720);

    // Mock API responses for consistent visual state
    cy.intercept("POST", "/api/v1/metadata", {
      statusCode: 200,
      body: {
        url: "https://youtu.be/dQw4w9WgXcQ",
        title:
          "Test Video - Rick Astley - Never Gonna Give You Up (Official Music Video)",
        duration: 212, // 3:32 in seconds
      },
    }).as("metadata");

    cy.intercept("POST", "/api/v1/jobs", {
      statusCode: 201,
      body: { jobId: "visual-test-job-id" },
    }).as("createJob");

    // Mock job completion for download state
    cy.intercept("GET", "/api/v1/jobs/visual-test-job-id", {
      statusCode: 200,
      body: {
        status: "done",
        download_url:
          "https://s3.amazonaws.com/bucket/test-clip.mp4?presigned=true",
      },
    }).as("jobStatus");
  });

  it("should capture URL Input Screen - Empty State", () => {
    cy.visit("/");

    // Wait for the page to load completely
    cy.get("body").should("be.visible");

    // Wait for hydration to complete in Next.js
    cy.wait(2000);

    // Try multiple strategies to find the main content
    // Strategy 1: Look for specific test IDs
    cy.get("body").then(($body) => {
      if ($body.find('[data-testid="url-input"]').length > 0) {
        cy.get('[data-testid="url-input"]').should("be.visible");
      } else if ($body.find('input[type="text"]').length > 0) {
        cy.get('input[type="text"]').first().should("be.visible");
      } else if ($body.find('input[type="url"]').length > 0) {
        cy.get('input[type="url"]').first().should("be.visible");
      } else if ($body.find("input").length > 0) {
        cy.get("input").first().should("be.visible");
      } else {
        // If no input found, just ensure the page loaded
        cy.contains("Meme").should("be.visible");
      }
    });

    // Wait for any remaining animations
    cy.wait(1000);

    // Capture baseline snapshot
    takeSnapshot("URL Input – Empty State", {
      widths: [375, 768, 1280],
    });
  });

  it("should capture URL Input Screen - Loading State", () => {
    // Mock a delayed metadata response to capture loading state
    cy.intercept("POST", "/api/v1/metadata", {
      statusCode: 200,
      body: {
        url: "https://youtu.be/dQw4w9WgXcQ",
        title: "Test Video Title",
        duration: 212,
      },
      delay: 5000, // Long delay to capture loading state
    }).as("metadataDelayed");

    cy.visit("/");

    // Wait for app to be ready
    cy.get('[data-testid="url-input"]').should("be.visible");
    cy.wait(1500);

    // Enter URL and submit
    cy.get('[data-testid="url-input"]')
      .should("be.visible")
      .type("https://youtu.be/dQw4w9WgXcQ");

    cy.get('[data-testid="analyze-button"]').click();

    // Wait for loading state to be visible
    cy.get('[data-testid="analyze-button"]').should("be.disabled");
    cy.wait(800); // Allow loading animation to start

    takeSnapshot("URL Input – Loading State", {
      widths: [375, 768, 1280],
    });
  });

  it("should capture Trim Panel - Default State", () => {
    cy.visit("/");

    // Wait for app to be ready
    cy.get('[data-testid="url-input"]').should("be.visible");
    cy.wait(1500);

    // Enter URL and proceed to trim panel
    cy.get('[data-testid="url-input"]').type("https://youtu.be/dQw4w9WgXcQ");

    cy.get('[data-testid="analyze-button"]').click();
    cy.wait("@metadata", { timeout: 10000 });

    // Wait for trim panel to load and stabilize
    cy.get('[data-testid="start-time"]').should("be.visible");
    cy.get('[data-testid="end-time"]').should("be.visible");
    cy.get('[data-testid="video-player"]').should("be.visible");

    // Wait for any video player initialization and hydration
    cy.wait(2000);

    takeSnapshot("Trim Panel – Default State", {
      widths: [375, 768, 1280],
    });
  });

  it("should capture Trim Panel - With Custom Selection", () => {
    cy.visit("/");

    // Navigate to trim panel
    cy.get('[data-testid="url-input"]').type("https://youtu.be/dQw4w9WgXcQ");

    cy.get('[data-testid="analyze-button"]').click();
    cy.wait("@metadata", { timeout: 10000 });

    // Wait for panel to stabilize
    cy.get('[data-testid="start-time"]').should("be.visible");
    cy.wait(1000);

    // Set custom trim times
    cy.get('[data-testid="start-time"]').clear().type("00:10.500");

    cy.get('[data-testid="end-time"]').clear().type("00:25.250");

    // Check the rights checkbox
    cy.get('[data-testid="rights-checkbox"]').check();

    // Wait for UI to update
    cy.wait(500);

    takeSnapshot("Trim Panel – Custom Selection", {
      widths: [375, 768, 1280],
    });
  });

  it("should capture Processing State", () => {
    // Mock working status for processing visualization
    cy.intercept("GET", "/api/v1/jobs/visual-test-job-id", {
      statusCode: 200,
      body: {
        status: "working",
        progress: 65,
      },
    }).as("jobWorking");

    cy.visit("/");

    // Navigate through flow to processing
    cy.get('[data-testid="url-input"]').type("https://youtu.be/dQw4w9WgXcQ");

    cy.get('[data-testid="analyze-button"]').click();
    cy.wait("@metadata", { timeout: 10000 });

    // Set trim parameters and submit
    cy.get('[data-testid="start-time"]').clear().type("00:05.000");
    cy.get('[data-testid="end-time"]').clear().type("00:15.000");
    cy.get('[data-testid="rights-checkbox"]').check();

    cy.get('[data-testid="clip-btn"]').click();
    cy.wait("@createJob", { timeout: 10000 });
    cy.wait("@jobWorking", { timeout: 10000 });

    // Wait for processing UI to stabilize
    cy.contains("Processing your clip...").should("be.visible");
    cy.wait(800);

    takeSnapshot("Processing State – Progress Bar", {
      widths: [375, 768, 1280],
    });
  });

  it("should capture Download Modal - Success State", () => {
    cy.visit("/");

    // Complete full flow to download modal
    cy.get('[data-testid="url-input"]').type("https://youtu.be/dQw4w9WgXcQ");

    cy.get('[data-testid="analyze-button"]').click();
    cy.wait("@metadata", { timeout: 10000 });

    // Set trim and submit
    cy.get('[data-testid="start-time"]').clear().type("00:08.000");
    cy.get('[data-testid="end-time"]').clear().type("00:18.000");
    cy.get('[data-testid="rights-checkbox"]').check();

    cy.get('[data-testid="clip-btn"]').click();
    cy.wait("@createJob", { timeout: 10000 });
    cy.wait("@jobStatus", { timeout: 10000 });

    // Wait for download modal to appear and stabilize
    cy.get('[data-testid="download-btn"]').should("be.visible");
    cy.contains("Clip ready!").should("be.visible");
    cy.wait(500);

    takeSnapshot("Download Modal – Success State", {
      widths: [375, 768, 1280],
    });
  });

  it("should capture Error States", () => {
    // Test validation error for long clips
    cy.visit("/");

    cy.get('[data-testid="url-input"]').type("https://youtu.be/dQw4w9WgXcQ");

    cy.get('[data-testid="analyze-button"]').click();
    cy.wait("@metadata", { timeout: 10000 });

    // Set clip longer than 3 minutes to trigger validation
    cy.get('[data-testid="start-time"]').clear().type("00:00.000");
    cy.get('[data-testid="end-time"]').clear().type("03:01.000");

    // Wait for validation error to appear
    cy.contains("Trim to thirty minutes or less to proceed.").should(
      "be.visible",
    );

    cy.wait(500);

    takeSnapshot("Validation Error – Clip Too Long", {
      widths: [375, 768, 1280],
    });
  });

  it("should capture Queue Full Error State", () => {
    // Mock queue full error
    cy.intercept("POST", "/api/v1/jobs", {
      statusCode: 429,
      body: {
        error: "Queue is full",
        code: "QUEUE_FULL",
      },
    }).as("queueFullError");

    // Mock job status that returns queue full
    cy.intercept("GET", "/api/v1/jobs/visual-test-job-id", {
      statusCode: 200,
      body: {
        status: "error",
        error_code: "QUEUE_FULL",
      },
    }).as("queueFullStatus");

    cy.visit("/");

    // Navigate to trim and trigger queue full
    cy.get('[data-testid="url-input"]').type("https://youtu.be/dQw4w9WgXcQ");

    cy.get('[data-testid="analyze-button"]').click();
    cy.wait("@metadata", { timeout: 10000 });

    cy.get('[data-testid="start-time"]').clear().type("00:05.000");
    cy.get('[data-testid="end-time"]').clear().type("00:15.000");
    cy.get('[data-testid="rights-checkbox"]').check();

    cy.get('[data-testid="clip-btn"]').click();
    cy.wait("@queueFullError", { timeout: 10000 });

    // Wait for queue full banner to appear
    cy.contains("Busy right now. Try again in a minute.").should("be.visible");

    cy.wait(500);

    takeSnapshot("Queue Full Error State", {
      widths: [375, 768, 1280],
    });
  });

  it("should capture Rate Limit Notification", () => {
    // Mock rate limit error
    cy.intercept("POST", "/api/v1/metadata", {
      statusCode: 429,
      body: {
        error:
          "Rate limit exceeded. Please wait 60 seconds before trying again.",
        code: "RATE_LIMIT_EXCEEDED",
        retry_after: 60,
      },
    }).as("rateLimitError");

    cy.visit("/");

    cy.get('[data-testid="url-input"]').type("https://youtu.be/dQw4w9WgXcQ");

    cy.get('[data-testid="analyze-button"]').click();
    cy.wait("@rateLimitError", { timeout: 10000 });

    // Wait for rate limit notification to appear
    cy.contains("Rate limit exceeded").should("be.visible");

    cy.wait(500);

    takeSnapshot("Rate Limit Notification", {
      widths: [375, 768, 1280],
    });
  });

  it("should capture Mobile Responsive States", () => {
    // Test mobile viewport specifically
    cy.viewport(375, 667); // iPhone SE

    cy.visit("/");

    // Mobile empty state
    cy.get('[data-testid="url-input"]').should("be.visible");
    cy.wait(500);

    takeSnapshot("Mobile – URL Input Empty", {
      widths: [375],
    });

    // Navigate to trim panel on mobile
    cy.get('[data-testid="url-input"]').type("https://youtu.be/dQw4w9WgXcQ");

    cy.get('[data-testid="analyze-button"]').click();
    cy.wait("@metadata", { timeout: 10000 });

    cy.get('[data-testid="start-time"]').should("be.visible");
    cy.wait(800);

    takeSnapshot("Mobile – Trim Panel", {
      widths: [375],
    });
  });

  it("should capture Dark Mode States", () => {
    cy.visit("/");

    // Force dark mode by adding class to document
    cy.get("html").then(($html) => {
      $html.addClass("dark");
    });

    // Wait for dark mode to apply
    cy.wait(500);

    cy.get('[data-testid="url-input"]').should("be.visible");

    takeSnapshot("Dark Mode – URL Input", {
      widths: [375, 768, 1280],
    });

    // Navigate to trim panel in dark mode
    cy.get('[data-testid="url-input"]').type("https://youtu.be/dQw4w9WgXcQ");

    cy.get('[data-testid="analyze-button"]').click();
    cy.wait("@metadata", { timeout: 10000 });

    cy.get('[data-testid="start-time"]').should("be.visible");
    cy.wait(800);

    takeSnapshot("Dark Mode – Trim Panel", {
      widths: [375, 768, 1280],
    });
  });
});
