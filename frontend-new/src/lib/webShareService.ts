export interface ShareData {
  title?: string;
  text?: string;
  url?: string;
  files?: File[];
}

export interface WebShareOptions {
  fallbackToLink?: boolean;
  showProgress?: boolean;
  onProgress?: (loaded: number, total: number) => void;
  onError?: (error: Error) => void;
  onSuccess?: () => void;
}

export class WebShareError extends Error {
  constructor(
    message: string,
    public code:
      | "NOT_SUPPORTED"
      | "USER_CANCELLED"
      | "DOWNLOAD_FAILED"
      | "SHARE_FAILED",
    public originalError?: Error,
  ) {
    super(message);
    this.name = "WebShareError";
    Object.setPrototypeOf(this, WebShareError.prototype);
  }
}

export class WebShareService {
  /**
   * Check if Web Share API is supported and can share specific data
   */
  static isSupported(): boolean {
    return typeof navigator !== "undefined" && "share" in navigator;
  }

  /**
   * Check if file sharing is supported
   */
  static canShareFiles(files?: File[]): boolean {
    if (!this.isSupported()) return false;

    try {
      return navigator.canShare && files
        ? navigator.canShare({ files })
        : false;
    } catch {
      return false;
    }
  }

  /**
   * Download video file as blob and share it natively
   */
  static async shareVideoFile(
    downloadUrl: string,
    videoTitle: string,
    options: WebShareOptions = {},
  ): Promise<void> {
    const {
      fallbackToLink = true,
      showProgress = true,
      onProgress,
      onError,
      onSuccess,
    } = options;

    try {
      // Step 1: Check Web Share API support
      if (!this.isSupported()) {
        if (fallbackToLink) {
          return this.shareAsLink(downloadUrl, videoTitle);
        }
        throw new WebShareError(
          "Web Share API not supported in this browser",
          "NOT_SUPPORTED",
        );
      }

      // Step 2: Download video file as blob
      const file = await this.downloadAsFile(
        downloadUrl,
        "shared-video.mp4",
        onProgress,
      );

      // Step 3: Check if file sharing is supported
      if (!this.canShareFiles([file])) {
        if (fallbackToLink) {
          return this.shareAsLink(downloadUrl, videoTitle);
        }
        throw new WebShareError(
          "File sharing not supported on this device",
          "NOT_SUPPORTED",
        );
      }

      // Step 4: Share the file natively
      await navigator.share({
        files: [file],
        title: videoTitle,
        text: "Check out this video clip!",
      });

      onSuccess?.();
    } catch (error) {
      const webShareError =
        error instanceof WebShareError
          ? error
          : new WebShareError(
              "Failed to share video file",
              "SHARE_FAILED",
              error as Error,
            );

      onError?.(webShareError);
      throw webShareError;
    }
  }

  /**
   * Download video from URL and convert to File blob
   */
  private static async downloadAsFile(
    downloadUrl: string,
    fileName: string = "video.mp4",
    onProgress?: (loaded: number, total: number) => void,
  ): Promise<File> {
    try {
      const response = await fetch(downloadUrl);

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const contentLength = response.headers.get("content-length");
      const total = contentLength ? parseInt(contentLength, 10) : 0;

      let loaded = 0;
      const reader = response.body?.getReader();
      const chunks: Uint8Array[] = [];

      if (!reader) {
        throw new Error("Failed to read response body");
      }

      // Read response in chunks with progress tracking
      while (true) {
        const { done, value } = await reader.read();

        if (done) break;

        chunks.push(value);
        loaded += value.length;

        if (total > 0 && onProgress) {
          onProgress(loaded, total);
        }
      }

      // Combine chunks into blob
      const blob = new Blob(chunks, { type: "video/mp4" });

      // Create File object
      return new File([blob], fileName, { type: "video/mp4" });
    } catch (error) {
      throw new WebShareError(
        "Failed to download video file",
        "DOWNLOAD_FAILED",
        error as Error,
      );
    }
  }

  /**
   * Fallback: Share as link using Web Share API or platform-specific URLs
   */
  private static async shareAsLink(
    downloadUrl: string,
    videoTitle: string,
  ): Promise<void> {
    const shareData: ShareData = {
      title: videoTitle,
      text: "Check out this video clip!",
      url: downloadUrl,
    };

    if (this.isSupported() && navigator.share) {
      await navigator.share(shareData);
    } else {
      // Platform-specific fallback
      this.openPlatformShare("whatsapp", downloadUrl, videoTitle);
    }
  }

  /**
   * Open platform-specific share URL
   */
  private static openPlatformShare(
    platform: string,
    downloadUrl: string,
    videoTitle: string,
  ): void {
    const shareUrls: Record<string, string> = {
      whatsapp: `https://wa.me/?text=${encodeURIComponent(`${videoTitle}\n${downloadUrl}`)}`,
      telegram: `https://t.me/share/url?url=${encodeURIComponent(downloadUrl)}&text=${encodeURIComponent(videoTitle)}`,
      twitter: `https://twitter.com/intent/tweet?text=${encodeURIComponent(videoTitle)}&url=${encodeURIComponent(downloadUrl)}`,
    };

    const url = shareUrls[platform] || shareUrls.whatsapp;
    window.open(url, "_blank", "width=600,height=400");
  }

  /**
   * Sanitize filename for file sharing
   */
  private static sanitizeFileName(title: string): string {
    return title
      .trim()
      .replace(/[^a-z0-9\-_]+/gi, "_") // Replace any sequence of invalid chars with a single underscore
      .replace(/_+/g, "_") // Collapse multiple underscores
      .replace(/_$/, "") // Remove trailing underscore
      .toLowerCase()
      .substring(0, 50); // Limit length
  }

  /**
   * Get user-friendly error message
   */
  static getErrorMessage(error: WebShareError): string {
    switch (error.code) {
      case "NOT_SUPPORTED":
        return "Your browser doesn't support native file sharing. We'll share a download link instead.";
      case "USER_CANCELLED":
        return "Share cancelled by user.";
      case "DOWNLOAD_FAILED":
        return "Failed to prepare video for sharing. Please try downloading directly.";
      case "SHARE_FAILED":
        return "Failed to open share dialog. Please try copying the download link.";
      default:
        return "Something went wrong while sharing. Please try again.";
    }
  }
}

// Utility functions for detecting platform capabilities
export const detectPlatformCapabilities = () => {
  const userAgent = navigator.userAgent.toLowerCase();
  const isMobile =
    /android|iphone|ipad|ipod|blackberry|iemobile|opera mini/i.test(userAgent);
  const isIOS = /ipad|iphone|ipod/.test(userAgent);
  const isAndroid = /android/.test(userAgent);

  return {
    isMobile,
    isIOS,
    isAndroid,
    supportsWebShare: WebShareService.isSupported(),
    supportsFileShare: WebShareService.canShareFiles(),
    recommendedApproach:
      isMobile && WebShareService.isSupported()
        ? "web-share"
        : "download-then-share",
  };
};
