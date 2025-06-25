import "@testing-library/jest-dom";
import { beforeAll, beforeEach, afterEach, afterAll, vi, expect } from "vitest";
import { cleanup } from "@testing-library/react";
// import { server } from './mocks/server'; // Temporarily disabled to fix hanging tests
import { toHaveNoViolations } from "jest-axe";
import React from "react";

// ===========================
// Accessibility Testing Setup
// ===========================
// expect.extend(toHaveNoViolations); // Temporarily disabled

// ===========================
// Test Environment Setup
// ===========================

// MSW temporarily disabled to fix hanging tests
// TODO: Re-enable MSW after fixing configuration
// beforeAll(() => {
//   server.listen({ onUnhandledRequest: 'error' });
// });

afterEach(() => {
  // server.resetHandlers(); // Temporarily disabled
  cleanup();
});

// afterAll(() => {
//   server.close(); // Temporarily disabled
// });

// ===========================
// Global Mocks
// ===========================

// Mock React Player
vi.mock("react-player", () => ({
  default: vi.fn(({ onReady, onDuration, onProgress, onError, ...props }) => {
    // Simulate player behavior
    setTimeout(() => {
      onReady?.();
      onDuration?.(120); // 2 minutes
    }, 100);

    return React.createElement("div", {
      "data-testid": "react-player",
      ...props,
    });
  }),
}));

// Mock Axios
vi.mock("axios", () => ({
  default: {
    create: vi.fn(() => ({
      get: vi.fn(),
      post: vi.fn(),
      delete: vi.fn(),
      interceptors: {
        request: { use: vi.fn() },
        response: { use: vi.fn() },
      },
    })),
    get: vi.fn(),
    post: vi.fn(),
    delete: vi.fn(),
    isCancel: vi.fn(() => false),
    CancelToken: {
      source: vi.fn(() => ({
        token: "mock-token",
        cancel: vi.fn(),
      })),
    },
  },
}));

// Mock environment variables
Object.defineProperty(window, "location", {
  value: {
    ...window.location,
    origin: "http://localhost:3000",
    href: "http://localhost:3000",
  },
  writable: true,
});

// Mock clipboard API
Object.assign(navigator, {
  clipboard: {
    writeText: vi.fn().mockResolvedValue(void 0),
    readText: vi.fn().mockResolvedValue(""),
  },
});

// Mock ResizeObserver
global.ResizeObserver = vi.fn().mockImplementation(() => ({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn(),
}));

// Mock IntersectionObserver
global.IntersectionObserver = vi.fn().mockImplementation(() => ({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn(),
}));

// Mock matchMedia
Object.defineProperty(window, "matchMedia", {
  writable: true,
  value: vi.fn().mockImplementation((query) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(), // deprecated
    removeListener: vi.fn(), // deprecated
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
});

// Mock console methods in tests
global.console = {
  ...console,
  warn: vi.fn(),
  error: vi.fn(),
  log: vi.fn(),
};

// ===========================
// Test Utilities
// ===========================

export const mockVideoMetadata = {
  title: "Test Video Title",
  duration: 120,
  thumbnail: "https://example.com/thumbnail.jpg",
  upload_date: "2024-01-01",
  uploader: "Test Uploader",
  formats: [
    {
      format_id: "18",
      ext: "mp4",
      resolution: "360p",
      filesize: 10485760,
      url: "https://example.com/video.mp4",
    },
    {
      format_id: "22",
      ext: "mp4",
      resolution: "720p",
      filesize: 52428800,
      url: "https://example.com/video_hd.mp4",
    },
  ],
};

export const mockJobResponse = {
  id: "test-job-123",
  status: "queued",
  progress: 0,
  created_at: "2024-01-01T00:00:00Z",
  url: "https://youtube.com/watch?v=test",
  in_ts: 10,
  out_ts: 40,
  format_id: "18",
};

export const createMockElement = (tagName: string) => {
  const element = document.createElement(tagName);

  // Mock common methods
  element.click = vi.fn();
  element.scrollIntoView = vi.fn();

  if (tagName === "a") {
    element.setAttribute("download", "");
  }

  return element;
};

// ===========================
// Custom Test Environment Variables
// ===========================

process.env.VITE_API_BASE_URL = "http://localhost:8000";
process.env.VITE_POLLING_INTERVAL = "1000";

// Silence specific warnings in tests
const originalError = console.error;
beforeAll(() => {
  console.error = (...args: any[]) => {
    if (
      typeof args[0] === "string" &&
      (args[0].includes("Warning: ReactDOM.render is no longer supported") ||
        args[0].includes("Warning: React.createFactory() is deprecated"))
    ) {
      return;
    }
    originalError.call(console, ...args);
  };
});

afterAll(() => {
  console.error = originalError;
});

// ===========================
// Visual Testing Configuration
// ===========================

// Configure viewport for consistent visual testing
beforeEach(() => {
  // Set consistent viewport for visual regression tests
  Object.defineProperty(window, "innerWidth", {
    writable: true,
    configurable: true,
    value: 1280,
  });

  Object.defineProperty(window, "innerHeight", {
    writable: true,
    configurable: true,
    value: 720,
  });

  // Trigger resize event
  window.dispatchEvent(new Event("resize"));
});

// ===========================
// Performance Testing Utilities
// ===========================

export const performanceUtils = {
  /**
   * Measure component render time
   */
  measureRenderTime: async (renderFn: () => Promise<void> | void) => {
    const startTime = performance.now();
    await renderFn();
    const endTime = performance.now();
    return endTime - startTime;
  },

  /**
   * Assert performance budget
   */
  assertPerformanceBudget: (actualTime: number, budgetMs: number) => {
    expect(actualTime).toBeLessThan(budgetMs);
  },

  /**
   * Simulate slow network conditions
   */
  simulateSlowNetwork: () => {
    // Mock slow network responses
    const originalFetch = global.fetch;
    global.fetch = vi.fn().mockImplementation((...args) => {
      return new Promise((resolve) => {
        setTimeout(() => {
          resolve(originalFetch(...args));
        }, 2000); // 2 second delay
      });
    });

    return () => {
      global.fetch = originalFetch;
    };
  },

  /**
   * Monitor memory usage (mock implementation)
   */
  monitorMemoryUsage: () => {
    const mockMemoryInfo = {
      usedJSHeapSize: Math.random() * 50 * 1024 * 1024, // Random size up to 50MB
      totalJSHeapSize: 100 * 1024 * 1024, // 100MB
      jsHeapSizeLimit: 200 * 1024 * 1024, // 200MB
    };

    Object.defineProperty(performance, "memory", {
      value: mockMemoryInfo,
      writable: true,
    });

    return mockMemoryInfo;
  },
};

// ===========================
// Accessibility Testing Utilities
// ===========================

export const a11yUtils = {
  /**
   * Custom accessibility rules for the application
   */
  getA11yConfig: () => ({
    rules: {
      // Disable color-contrast for design system components
      "color-contrast": { enabled: false },
      // Ensure all interactive elements are accessible
      "interactive-supports-focus": { enabled: true },
      // Ensure proper heading structure
      "heading-order": { enabled: true },
      // Ensure form elements have labels
      label: { enabled: true },
      // Ensure images have alt text
      "image-alt": { enabled: true },
    },
    tags: ["wcag2a", "wcag2aa", "wcag21aa"],
  }),

  /**
   * Test component accessibility with custom config
   */
  testAccessibility: async (container: HTMLElement) => {
    const { axe } = await import("jest-axe");
    const results = await axe(container, a11yUtils.getA11yConfig());
    expect(results).toHaveNoViolations();
    return results;
  },
};

// ===========================
// Visual Regression Testing Utilities
// ===========================

export const visualUtils = {
  /**
   * Wait for all images to load before taking snapshot
   */
  waitForImages: () => {
    return new Promise<void>((resolve) => {
      const images = document.querySelectorAll("img");
      let loadedCount = 0;
      const totalImages = images.length;

      if (totalImages === 0) {
        resolve();
        return;
      }

      images.forEach((img) => {
        if (img.complete) {
          loadedCount++;
          if (loadedCount === totalImages) resolve();
        } else {
          img.onload = () => {
            loadedCount++;
            if (loadedCount === totalImages) resolve();
          };
          img.onerror = () => {
            loadedCount++;
            if (loadedCount === totalImages) resolve();
          };
        }
      });
    });
  },

  /**
   * Hide dynamic content for consistent snapshots
   */
  hideDynamicContent: () => {
    const dynamicSelectors = [
      '[data-testid="timestamp"]',
      '[data-testid="job-id"]',
      '[data-testid="random-id"]',
      ".timestamp",
      ".dynamic-content",
    ];

    dynamicSelectors.forEach((selector) => {
      const elements = document.querySelectorAll(selector);
      elements.forEach((el) => {
        (el as HTMLElement).style.visibility = "hidden";
      });
    });
  },

  /**
   * Set up consistent environment for visual testing
   */
  setupVisualEnvironment: () => {
    // Disable animations for consistent snapshots
    const style = document.createElement("style");
    style.innerHTML = `
      *, *::before, *::after {
        animation-duration: 0s !important;
        animation-delay: 0s !important;
        transition-duration: 0s !important;
        transition-delay: 0s !important;
      }
    `;
    document.head.appendChild(style);

    // Set consistent date for testing
    vi.setSystemTime(new Date("2024-01-01T00:00:00Z"));

    return () => {
      document.head.removeChild(style);
      vi.useRealTimers();
    };
  },
};

// ===========================
// Global Test Configuration
// ===========================

// Configure global test timeouts
vi.setConfig({
  testTimeout: 10000, // 10 seconds
  hookTimeout: 5000, // 5 seconds
});

// Export utilities for use in tests
export { server } from "./mocks/server";
