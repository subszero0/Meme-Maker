import { describe, it, expect, beforeEach, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import React from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

// Import components to test
import { UrlInput } from "../components/UrlInput";
import { LoadingAnimation } from "../components/LoadingAnimation";

// Mock all the hooks and external dependencies
vi.mock("../hooks/useApi", () => ({
  useVideoMetadata: vi.fn(() => ({
    data: null,
    isLoading: false,
    error: null,
    isError: false,
  })),
  useJobStatusWithPolling: vi.fn(() => ({
    data: null,
    error: null,
    isLoading: true,
  })),
  useCancelJob: vi.fn(() => ({
    mutate: vi.fn(),
  })),
}));

vi.mock("use-debounce", () => ({
  useDebounce: vi.fn((value) => [value]),
}));

// Mock the API constants
vi.mock("../lib/api", () => ({
  JobStatus: {
    QUEUED: "queued",
    WORKING: "working",
    DONE: "completed",
    ERROR: "error",
  },
}));

// Minimal Test Provider
const TestProvider: React.FC<{ children: React.ReactNode }> = ({
  children,
}) => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false, staleTime: Infinity },
      mutations: { retry: false },
    },
  });

  return (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
};

describe("Component Fixed Tests", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  const renderWithProviders = (component: React.ReactElement) => {
    return render(<TestProvider>{component}</TestProvider>);
  };

  describe("UrlInput Component", () => {
    it("should render input field and submit button", () => {
      const mockOnSubmit = vi.fn();
      renderWithProviders(<UrlInput onSubmit={mockOnSubmit} />);

      // Use the actual placeholder text from the component
      expect(
        screen.getByPlaceholderText(
          "https://facebook.com/watch?v=... or any video URL",
        ),
      ).toBeInTheDocument();
      expect(
        screen.getByRole("button", { name: /let's go/i }),
      ).toBeInTheDocument();
    });

    it("should display the correct heading", () => {
      const mockOnSubmit = vi.fn();
      renderWithProviders(<UrlInput onSubmit={mockOnSubmit} />);

      expect(
        screen.getByText("Start Your Creative Journey"),
      ).toBeInTheDocument();
      expect(screen.getByText(/paste any video link/i)).toBeInTheDocument();
    });

    it("should mention supported platforms in description", () => {
      const mockOnSubmit = vi.fn();
      renderWithProviders(<UrlInput onSubmit={mockOnSubmit} />);

      // Check that the component mentions the supported platforms in the description text
      expect(screen.getByText(/Paste any video link from Facebook/i)).toBeInTheDocument();
    });
  });

  describe("LoadingAnimation Component", () => {
    it("should render without crashing when jobId is provided", () => {
      // The hook is already mocked at the module level - just render
      renderWithProviders(<LoadingAnimation jobId="test-job-123" />);

      // Should render the main heading
      expect(
        screen.getByText(/creating your masterpiece/i),
      ).toBeInTheDocument();
    });

    it("should handle basic rendering with required props", () => {
      const mockOnComplete = vi.fn();
      renderWithProviders(
        <LoadingAnimation jobId="test-job-123" onComplete={mockOnComplete} />,
      );

      // Should render without errors - the component should be visible
      expect(
        screen.getByText(/hang tight while we process/i),
      ).toBeInTheDocument();
    });

    it("should render progress elements", () => {
      renderWithProviders(<LoadingAnimation jobId="test-job-123" />);

      // Should have a circular progress indicator (SVG)
      const svgElements = document.querySelectorAll("svg");
      expect(svgElements.length).toBeGreaterThan(0);
    });
  });
});
