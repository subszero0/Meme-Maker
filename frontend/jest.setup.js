import "@testing-library/jest-dom";

// Suppress JSdom navigation warnings and React act() warnings that are harmless in tests
const originalConsoleError = console.error;
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
          { format_id: "22", ext: "mp4", resolution: "720p" },
          { format_id: "18", ext: "mp4", resolution: "480p" },
          { format_id: "36", ext: "mp4", resolution: "360p" },
        ],
      }),
  }),
);

// Reset fetch mock before each test
beforeEach(() => {
  global.fetch.mockClear();
});
