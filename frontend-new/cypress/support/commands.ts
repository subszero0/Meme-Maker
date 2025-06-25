/// <reference types="cypress" />

// ===========================
// Element Selection Commands
// Following Cypress best practices for data-cy selectors
// ===========================

/**
 * Get element by data-cy attribute (exact match)
 * Follows Cypress best practice of using data attributes for testing
 */
Cypress.Commands.add("getBySel", (selector: string, ...args) => {
  return cy.get(`[data-cy=${selector}]`, ...args);
});

/**
 * Get element by data-cy attribute (partial match)
 * Useful for dynamic selectors
 */
Cypress.Commands.add("getBySelLike", (selector: string, ...args) => {
  return cy.get(`[data-cy*=${selector}]`, ...args);
});

// ===========================
// API Mocking Commands
// ===========================

/**
 * Set up API intercepts for consistent testing
 * Mocks all backend endpoints with realistic responses
 */
Cypress.Commands.add("setupApiMocks", () => {
  // Health check endpoint
  cy.intercept("GET", "/health", {
    statusCode: 200,
    body: { status: "ok", version: "1.0.0" },
  }).as("healthCheck");

  // Video metadata endpoint
  cy.intercept("GET", "/api/metadata*", (req) => {
    const url = req.url;

    if (url.includes("invalid")) {
      req.reply({
        statusCode: 400,
        body: { error: "Invalid video URL" },
      });
    } else {
      req.reply({
        statusCode: 200,
        body: {
          title: "E2E Test Video",
          duration: 120,
          thumbnail: "https://example.com/thumb.jpg",
          upload_date: "2024-01-01",
          uploader: "Test Channel",
          formats: [
            {
              format_id: "18",
              ext: "mp4",
              resolution: "360p",
              filesize: 10485760,
              fps: 30,
              width: 640,
              height: 360,
            },
            {
              format_id: "22",
              ext: "mp4",
              resolution: "720p",
              filesize: 52428800,
              fps: 30,
              width: 1280,
              height: 720,
            },
          ],
        },
      });
    }
  }).as("getMetadata");

  // Job creation endpoint
  cy.intercept("POST", "/api/clips", (req) => {
    const jobId = `e2e-job-${Date.now()}`;
    req.reply({
      statusCode: 200,
      body: {
        id: jobId,
        status: "queued",
        progress: 0,
        created_at: new Date().toISOString(),
        url: req.body.url,
        in_ts: req.body.in_ts,
        out_ts: req.body.out_ts,
        format_id: req.body.format_id,
      },
    });
  }).as("createJob");

  // Job status endpoint with progression simulation
  cy.intercept("GET", "/api/jobs/*", (req) => {
    const jobId = req.url.split("/").pop();

    // Simulate job progression
    req.reply({
      statusCode: 200,
      body: {
        id: jobId,
        status: "completed",
        progress: 100,
        download_url: `https://example.com/download/${jobId}.mp4`,
        filename: `${jobId}.mp4`,
        created_at: new Date().toISOString(),
        completed_at: new Date().toISOString(),
      },
    });
  }).as("getJobStatus");

  // File cleanup endpoint
  cy.intercept("DELETE", "/api/clips/*", {
    statusCode: 200,
    body: { message: "File deleted successfully" },
  }).as("deleteClip");
});

/**
 * Reset API mocks to clean state
 */
Cypress.Commands.add("resetApiMocks", () => {
  cy.window().then((win) => {
    win.localStorage.clear();
    win.sessionStorage.clear();
  });
});

// ===========================
// Application-Specific Commands
// ===========================

/**
 * Wait for video metadata to load completely
 */
Cypress.Commands.add("waitForVideoMetadata", () => {
  cy.wait("@getMetadata");
  cy.getBySel("video-title").should("be.visible");
  cy.getBySel("video-duration").should("be.visible");
  cy.getBySel("format-selector").should("be.visible");
});

/**
 * Wait for job processing to complete
 */
Cypress.Commands.add("waitForJobCompletion", (jobId: string) => {
  cy.wait("@createJob");
  cy.wait("@getJobStatus");

  // Wait for completion UI elements
  cy.getBySel("download-button").should("be.visible");
  cy.getBySel("share-options").should("be.visible");
});

/**
 * Complete full video processing workflow
 */
Cypress.Commands.add(
  "completeVideoWorkflow",
  (videoUrl: string, options = {}) => {
    const {
      startTime = "0:10",
      endTime = "0:40",
      resolution = "720p",
    } = options;

    // Step 1: Enter video URL
    cy.getBySel("url-input").clear().type(videoUrl);
    cy.getBySel("extract-button").click();

    // Step 2: Wait for metadata to load
    cy.waitForVideoMetadata();

    // Step 3: Configure clip settings
    cy.getBySel("start-time-input").clear().type(startTime);
    cy.getBySel("end-time-input").clear().type(endTime);

    // Select resolution
    cy.getBySel("format-selector")
      .find(`[data-resolution="${resolution}"]`)
      .click();

    // Step 4: Create clip
    cy.getBySel("create-clip-button").click();

    // Step 5: Wait for completion
    cy.waitForJobCompletion("test-job");
  },
);

/**
 * Login command (placeholder for future authentication)
 */
Cypress.Commands.add(
  "login",
  (email = "test@example.com", password = "password123") => {
    cy.log(`Login not required for current app. Email: ${email}`);
  },
);

// ===========================
// Utility Commands
// ===========================

/**
 * Custom command to check element accessibility
 */
Cypress.Commands.add("checkA11y", (selector?: string) => {
  // This will be enhanced when we add cypress-axe
  if (selector) {
    cy.get(selector).should("have.attr", "role").or("have.attr", "aria-label");
  } else {
    cy.get("body").should("exist");
  }
});

/**
 * Command to measure performance
 */
Cypress.Commands.add("measurePerformance", (actionCallback: () => void) => {
  cy.window().then((win) => {
    const startTime = win.performance.now();

    actionCallback();

    cy.then(() => {
      const endTime = win.performance.now();
      const duration = endTime - startTime;

      cy.log(`Performance: Action took ${duration.toFixed(2)}ms`);

      // Assert performance budget (configurable)
      expect(duration).to.be.lessThan(5000); // 5 second max
    });
  });
});

/**
 * Command to simulate real user typing with delays
 */
Cypress.Commands.add(
  "typeRealistic",
  { prevSubject: "element" },
  (subject, text: string) => {
    // Type with realistic human-like delays
    cy.wrap(subject).type(text, {
      delay: 100, // 100ms between keystrokes
      force: false, // Don't force, wait for element to be interactable
    });
  },
);

// ===========================
// Visual Testing Commands (for future enhancement)
// ===========================

/**
 * Take visual snapshot for regression testing
 */
Cypress.Commands.add("visualSnapshot", (name: string) => {
  // Placeholder for visual regression testing
  // Will be enhanced when we add visual testing tools
  cy.screenshot(name, {
    capture: "viewport",
    blackout: [".timestamp", ".dynamic-content"],
  });
});

// ===========================
// Type Declarations
// ===========================

declare global {
  namespace Cypress {
    interface Chainable {
      getBySel(
        selector: string,
        ...args: unknown[]
      ): Chainable<JQuery<HTMLElement>>;
      getBySelLike(
        selector: string,
        ...args: unknown[]
      ): Chainable<JQuery<HTMLElement>>;
      setupApiMocks(): Chainable<null>;
      resetApiMocks(): Chainable<null>;
      waitForVideoMetadata(): Chainable<null>;
      waitForJobCompletion(jobId: string): Chainable<null>;
      completeVideoWorkflow(
        videoUrl: string,
        options?: {
          startTime?: string;
          endTime?: string;
          resolution?: string;
        },
      ): Chainable<null>;
      login(email?: string, password?: string): Chainable<null>;
      checkA11y(selector?: string): Chainable<null>;
      measurePerformance(actionCallback: () => void): Chainable<null>;
      typeRealistic(text: string): Chainable<JQuery<HTMLElement>>;
      visualSnapshot(name: string): Chainable<null>;
    }
  }
}
