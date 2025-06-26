import { describe, it, expect, beforeEach, vi } from "vitest";
import {
  WebShareService,
  WebShareError,
  detectPlatformCapabilities,
} from "../lib/webShareService";

// Mock fetch
global.fetch = vi.fn();

// Mock navigator
const mockNavigator = {
  share: vi.fn(),
  canShare: vi.fn(),
  userAgent:
    "Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15",
};

Object.defineProperty(window, "navigator", {
  value: mockNavigator,
  writable: true,
});

// Mock window.open
global.open = vi.fn();

describe("WebShareService", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe("isSupported", () => {
    it("should return true when navigator.share is available", () => {
      expect(WebShareService.isSupported()).toBe(true);
    });

    it("should return false when navigator.share is not available", () => {
      const originalShare = mockNavigator.share;
      delete (mockNavigator as any).share;

      expect(WebShareService.isSupported()).toBe(false);

      mockNavigator.share = originalShare;
    });
  });

  describe("canShareFiles", () => {
    it("should return true when file sharing is supported", () => {
      mockNavigator.canShare.mockReturnValue(true);
      const files = [new File(["test"], "test.mp4", { type: "video/mp4" })];

      expect(WebShareService.canShareFiles(files)).toBe(true);
      expect(mockNavigator.canShare).toHaveBeenCalledWith({ files });
    });

    it("should return false when file sharing is not supported", () => {
      mockNavigator.canShare.mockReturnValue(false);
      const files = [new File(["test"], "test.mp4", { type: "video/mp4" })];

      expect(WebShareService.canShareFiles(files)).toBe(false);
    });

    it("should return false when navigator.canShare is not available", () => {
      const originalCanShare = mockNavigator.canShare;
      delete (mockNavigator as any).canShare;

      expect(WebShareService.canShareFiles()).toBe(false);

      mockNavigator.canShare = originalCanShare;
    });
  });

  describe("shareVideoFile", () => {
    const mockBlob = new Blob(["video data"], { type: "video/mp4" });

    beforeEach(() => {
      const mockResponse = {
        ok: true,
        headers: {
          get: vi.fn().mockReturnValue("1000"), // Content-Length
        },
        body: {
          getReader: vi.fn().mockReturnValue({
            read: vi
              .fn()
              .mockResolvedValueOnce({
                done: false,
                value: new Uint8Array([1, 2, 3]),
              })
              .mockResolvedValueOnce({ done: true, value: undefined }),
          }),
        },
      };
      (fetch as any).mockResolvedValue(mockResponse);
      mockNavigator.share.mockResolvedValue(undefined);
      mockNavigator.canShare.mockReturnValue(true);
    });

    it("should successfully share a video file", async () => {
      const onProgress = vi.fn();
      const onSuccess = vi.fn();

      await WebShareService.shareVideoFile(
        "https://example.com/video.mp4",
        "Test Video",
        { onProgress, onSuccess },
      );

      expect(fetch).toHaveBeenCalledWith("https://example.com/video.mp4");
      expect(onProgress).toHaveBeenCalled();
      expect(mockNavigator.share).toHaveBeenCalledWith({
        files: expect.arrayContaining([expect.any(File)]),
        title: "Test Video",
        text: "Check out this video clip!",
      });
      expect(onSuccess).toHaveBeenCalled();
    });

    it("should track download progress correctly", async () => {
      const onProgress = vi.fn();

      await WebShareService.shareVideoFile(
        "https://example.com/video.mp4",
        "Test Video",
        { onProgress },
      );

      expect(onProgress).toHaveBeenCalledWith(3, 1000);
    });

    it("should fallback to link sharing when Web Share API is not supported", async () => {
      const originalShare = mockNavigator.share;
      delete (mockNavigator as any).share;

      await WebShareService.shareVideoFile(
        "https://example.com/video.mp4",
        "Test Video",
        { fallbackToLink: true },
      );

      expect(global.open).toHaveBeenCalledWith(
        expect.stringContaining("wa.me"),
        "_blank",
        "width=600,height=400",
      );

      mockNavigator.share = originalShare;
    });

    it("should fallback to link sharing when file sharing is not supported", async () => {
      mockNavigator.canShare.mockReturnValue(false);

      await WebShareService.shareVideoFile(
        "https://example.com/video.mp4",
        "Test Video",
        { fallbackToLink: true },
      );

      expect(mockNavigator.share).toHaveBeenCalledWith({
        title: "Test Video",
        text: "Check out this video clip!",
        url: "https://example.com/video.mp4",
      });
    });

    it("should throw error when not supported and fallback disabled", async () => {
      const originalShare = mockNavigator.share;
      delete (mockNavigator as any).share;

      await expect(
        WebShareService.shareVideoFile(
          "https://example.com/video.mp4",
          "Test Video",
          { fallbackToLink: false },
        ),
      ).rejects.toThrow(WebShareError);

      mockNavigator.share = originalShare;
    });

    it("should handle download errors", async () => {
      (fetch as any).mockRejectedValue(new Error("Network error"));
      const onError = vi.fn();

      await expect(
        WebShareService.shareVideoFile(
          "https://example.com/video.mp4",
          "Test Video",
          { onError, fallbackToLink: false },
        ),
      ).rejects.toThrow(WebShareError);

      expect(onError).toHaveBeenCalled();
    });

    it("should handle share cancellation", async () => {
      mockNavigator.share.mockRejectedValue(new Error("AbortError"));

      await expect(
        WebShareService.shareVideoFile(
          "https://example.com/video.mp4",
          "Test Video",
        ),
      ).rejects.toThrow(WebShareError);
    });
  });

  describe("getErrorMessage", () => {
    it("should return appropriate error messages for different error codes", () => {
      const notSupportedError = new WebShareError("test", "NOT_SUPPORTED");
      const userCancelledError = new WebShareError("test", "USER_CANCELLED");
      const downloadFailedError = new WebShareError("test", "DOWNLOAD_FAILED");
      const shareFailedError = new WebShareError("test", "SHARE_FAILED");

      expect(WebShareService.getErrorMessage(notSupportedError)).toContain(
        "browser doesn't support",
      );
      expect(WebShareService.getErrorMessage(userCancelledError)).toContain(
        "cancelled",
      );
      expect(WebShareService.getErrorMessage(downloadFailedError)).toContain(
        "Failed to prepare",
      );
      expect(WebShareService.getErrorMessage(shareFailedError)).toContain(
        "Failed to open",
      );
    });
  });
});

describe("detectPlatformCapabilities", () => {
  it("should correctly detect mobile iOS device", () => {
    Object.defineProperty(window.navigator, "userAgent", {
      value: "Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X)",
      writable: true,
    });

    const capabilities = detectPlatformCapabilities();

    expect(capabilities.isMobile).toBe(true);
    expect(capabilities.isIOS).toBe(true);
    expect(capabilities.isAndroid).toBe(false);
    expect(capabilities.recommendedApproach).toBe("web-share");
  });

  it("should correctly detect mobile Android device", () => {
    Object.defineProperty(window.navigator, "userAgent", {
      value: "Mozilla/5.0 (Linux; Android 10; SM-G975F)",
      writable: true,
    });

    const capabilities = detectPlatformCapabilities();

    expect(capabilities.isMobile).toBe(true);
    expect(capabilities.isIOS).toBe(false);
    expect(capabilities.isAndroid).toBe(true);
  });

  it("should correctly detect desktop device", () => {
    Object.defineProperty(window.navigator, "userAgent", {
      value: "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
      writable: true,
    });

    const capabilities = detectPlatformCapabilities();

    expect(capabilities.isMobile).toBe(false);
    expect(capabilities.isIOS).toBe(false);
    expect(capabilities.isAndroid).toBe(false);
    expect(capabilities.recommendedApproach).toBe("download-then-share");
  });
});
