import { describe, it, expect, beforeEach, vi } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import React from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { NativeShareButton } from "../components/NativeShareButton";
import { Toaster } from "../components/ui/toaster";

// Mock the Web Share Service
vi.mock("../lib/webShareService", () => ({
  WebShareService: {
    isSupported: vi.fn(() => true),
    canShareFiles: vi.fn(() => true),
    shareVideoFile: vi.fn(() => Promise.resolve()),
    getErrorMessage: vi.fn(() => "Test error message"),
  },
  WebShareError: class WebShareError extends Error {
    constructor(
      message: string,
      public code: string,
    ) {
      super(message);
    }
  },
  detectPlatformCapabilities: vi.fn(() => ({
    isMobile: true,
    isIOS: false,
    isAndroid: true,
    supportsWebShare: true,
    supportsFileShare: true,
    recommendedApproach: "web-share",
  })),
}));

// Mock the toast hook
vi.mock("../hooks/use-toast", () => ({
  useToast: vi.fn(() => ({
    toast: vi.fn(),
  })),
}));

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
    <QueryClientProvider client={queryClient}>
      {children}
      <Toaster />
    </QueryClientProvider>
  );
};

describe("Web Share Integration Tests", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  const renderWithProviders = (component: React.ReactElement) => {
    return render(<TestProvider>{component}</TestProvider>);
  };

  describe("NativeShareButton Component", () => {
    it("should render with file sharing capabilities detected", () => {
      renderWithProviders(
        <NativeShareButton
          downloadUrl="https://example.com/video.mp4"
          videoTitle="Test Video"
        />,
      );

      expect(screen.getByText("Share Video File")).toBeInTheDocument();
      expect(
        screen.getByText("🎉 Best experience: Native file sharing available"),
      ).toBeInTheDocument();
    });

    it("should show platform capabilities indicators", () => {
      renderWithProviders(
        <NativeShareButton
          downloadUrl="https://example.com/video.mp4"
          videoTitle="Test Video"
          showCapabilities={true}
        />,
      );

      expect(screen.getByText("File sharing")).toBeInTheDocument();
      expect(screen.getByText("Web Share API")).toBeInTheDocument();
      expect(screen.getByText("Mobile")).toBeInTheDocument();
    });

    it("should trigger share functionality when clicked", async () => {
      const { WebShareService } = await import("../lib/webShareService");

      renderWithProviders(
        <NativeShareButton
          downloadUrl="https://example.com/video.mp4"
          videoTitle="Test Video"
        />,
      );

      const shareButton = screen.getByRole("button", {
        name: /share video file/i,
      });
      fireEvent.click(shareButton);

      await waitFor(() => {
        expect(WebShareService.shareVideoFile).toHaveBeenCalledWith(
          "https://example.com/video.mp4",
          "Test Video",
          expect.objectContaining({
            fallbackToLink: true,
            showProgress: true,
          }),
        );
      });
    });

    it("should handle different platform capabilities gracefully", async () => {
      // Mock different capabilities
      const webShareModule = await import("../lib/webShareService");
      vi.mocked(webShareModule.detectPlatformCapabilities).mockReturnValue({
        isMobile: false,
        isIOS: false,
        isAndroid: false,
        supportsWebShare: false,
        supportsFileShare: false,
        recommendedApproach: "download-then-share",
      });

      renderWithProviders(
        <NativeShareButton
          downloadUrl="https://example.com/video.mp4"
          videoTitle="Test Video"
        />,
      );

      expect(screen.getByText("Share to WhatsApp")).toBeInTheDocument();
      expect(
        screen.getByText("🔗 Fallback: Will open platform-specific share"),
      ).toBeInTheDocument();
    });

    it("should show compact version without capabilities info", () => {
      renderWithProviders(
        <NativeShareButton
          downloadUrl="https://example.com/video.mp4"
          videoTitle="Test Video"
          showCapabilities={false}
        />,
      );

      expect(screen.queryByText("File sharing")).not.toBeInTheDocument();
      expect(screen.queryByText("Web Share API")).not.toBeInTheDocument();
    });

    it("should handle different button sizes", () => {
      const { rerender } = renderWithProviders(
        <NativeShareButton
          downloadUrl="https://example.com/video.mp4"
          videoTitle="Test Video"
          size="sm"
        />,
      );

      let shareButton = screen.getByRole("button", {
        name: /share video file/i,
      });
      expect(shareButton).toHaveClass("px-3", "py-2", "text-sm");

      rerender(
        <TestProvider>
          <NativeShareButton
            downloadUrl="https://example.com/video.mp4"
            videoTitle="Test Video"
            size="lg"
          />
        </TestProvider>,
      );

      shareButton = screen.getByRole("button", { name: /share video file/i });
      expect(shareButton).toHaveClass("px-8", "py-4", "text-lg");
    });

    it("should disable button while sharing is in progress", async () => {
      // Mock sharing in progress
      const webShareModule = await import("../lib/webShareService");
      vi.mocked(
        webShareModule.WebShareService.shareVideoFile,
      ).mockImplementation(
        () => new Promise((resolve) => setTimeout(resolve, 1000)),
      );

      renderWithProviders(
        <NativeShareButton
          downloadUrl="https://example.com/video.mp4"
          videoTitle="Test Video"
        />,
      );

      const shareButton = screen.getByRole("button", {
        name: /share video file/i,
      });
      fireEvent.click(shareButton);

      await waitFor(() => {
        expect(shareButton).toBeDisabled();
      });
    });
  });

  describe("Platform Detection Integration", () => {
    it("should correctly adapt UI based on platform capabilities", async () => {
      const mockCapabilities = {
        isMobile: true,
        isIOS: true,
        isAndroid: false,
        supportsWebShare: true,
        supportsFileShare: true,
        recommendedApproach: "web-share" as const,
      };

      const webShareModule = await import("../lib/webShareService");
      vi.mocked(webShareModule.detectPlatformCapabilities).mockReturnValue(
        mockCapabilities,
      );

      renderWithProviders(
        <NativeShareButton
          downloadUrl="https://example.com/video.mp4"
          videoTitle="Test Video"
        />,
      );

      // Should show the best experience message for file sharing
      expect(
        screen.getByText("🎉 Best experience: Native file sharing available"),
      ).toBeInTheDocument();

      // Should use primary button variant for best experience
      const shareButton = screen.getByRole("button", {
        name: /share video file/i,
      });
      expect(shareButton).toHaveClass("bg-primary");
    });
  });
});

describe("Web Share Service Functionality", () => {
  it("should export all required functions and classes", async () => {
    const webShareModule = await import("../lib/webShareService");

    expect(webShareModule.WebShareService).toBeDefined();
    expect(webShareModule.WebShareError).toBeDefined();
    expect(webShareModule.detectPlatformCapabilities).toBeDefined();

    expect(typeof webShareModule.WebShareService.isSupported).toBe("function");
    expect(typeof webShareModule.WebShareService.canShareFiles).toBe(
      "function",
    );
    expect(typeof webShareModule.WebShareService.shareVideoFile).toBe(
      "function",
    );
    expect(typeof webShareModule.WebShareService.getErrorMessage).toBe(
      "function",
    );
  });

  it("should have proper error codes defined", async () => {
    const { WebShareError } = await import("../lib/webShareService");

    const error = new WebShareError("test", "NOT_SUPPORTED");
    expect(error.code).toBe("NOT_SUPPORTED");
    expect(error.message).toBe("test");
    expect(error.name).toBe("WebShareError");
  });
});
