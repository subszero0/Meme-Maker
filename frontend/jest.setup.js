import "@testing-library/jest-dom";

// Suppress JSdom navigation warnings, React act() warnings, and excessive component logging in tests
const originalConsoleError = console.error;
const originalConsoleLog = console.log;

console.error = (...args) => {
  if (
    typeof args[0] === "string" &&
    (args[0].includes("Not implemented: navigation (except hash changes)") ||
      args[0].includes("An update to") ||
      args[0].includes("inside a test was not wrapped in act(...)"))
  ) {
    return;
  }
  originalConsoleError.apply(console, args);
};

// Suppress excessive component debug logging in test environment
console.log = (...args) => {
  if (
    typeof args[0] === "string" &&
    (args[0].includes("🎬 ResolutionSelector:") ||
      args[0].includes("🎭 TrimPanel:") ||
      args[0].includes("🏠 HomePage:") ||
      args[0].includes("📊 JobPoller:") ||
      args[0].includes("Making API request to:") ||
      args[0].includes("API response received:"))
  ) {
    return;
  }
  originalConsoleLog.apply(console, args);
};

// Comprehensive fetch mock for tests
global.fetch = jest.fn(() =>
  Promise.resolve({
    ok: true,
    status: 200,
    json: () =>
      Promise.resolve({
        url: "https://youtube.com/watch?v=test",
        title: "Test Video",
        duration: 120,
        formats: [
          { 
            format_id: "22", 
            ext: "mp4", 
            resolution: "720p", 
            url: "https://example.com/stream720p.mp4",
            vcodec: "h264",
            acodec: "aac",
            format_note: "720p"
          },
          { 
            format_id: "18", 
            ext: "mp4", 
            resolution: "480p",
            url: "https://example.com/stream480p.mp4", 
            vcodec: "h264",
            acodec: "aac",
            format_note: "480p"
          },
          { 
            format_id: "36", 
            ext: "mp4", 
            resolution: "360p",
            url: "https://example.com/stream360p.mp4",
            vcodec: "h264", 
            acodec: "aac",
            format_note: "360p"
          },
        ],
      }),
  }),
);

// Reset fetch mock before each test
beforeEach(() => {
  global.fetch.mockClear();
});
