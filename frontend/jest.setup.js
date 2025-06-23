import "@testing-library/jest-dom";

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
        resolutions: ["720p", "480p", "360p"],
      }),
  }),
);

// Reset fetch mock before each test
beforeEach(() => {
  global.fetch.mockClear();
});
