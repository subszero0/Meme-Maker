import { useState, useCallback } from "react";
import {
  WebShareService,
  WebShareError,
  detectPlatformCapabilities,
} from "../lib/webShareService";
import { useToast } from "./use-toast";

export interface UseWebShareState {
  isSharing: boolean;
  progress: number;
  error: string | null;
  capabilities: ReturnType<typeof detectPlatformCapabilities>;
}

export interface UseWebShareActions {
  shareVideoFile: (downloadUrl: string, videoTitle: string) => Promise<void>;
  shareAsLink: (downloadUrl: string, videoTitle: string) => Promise<void>;
  reset: () => void;
}

export const useWebShare = (): UseWebShareState & UseWebShareActions => {
  const [isSharing, setIsSharing] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [capabilities] = useState(() => detectPlatformCapabilities());

  const { toast } = useToast();

  const reset = useCallback(() => {
    setIsSharing(false);
    setProgress(0);
    setError(null);
  }, []);

  const shareVideoFile = useCallback(
    async (downloadUrl: string, videoTitle: string) => {
      let absoluteUrl = new URL(downloadUrl, window.location.origin).href;
      if (window.location.protocol === "https:" && absoluteUrl.startsWith("http://")) {
        absoluteUrl = absoluteUrl.replace("http://", "https://");
      }

      try {
        setIsSharing(true);
        setProgress(0);
        setError(null);

        // Show initial toast based on platform capabilities
        if (capabilities.supportsFileShare) {
          toast({
            title: "Preparing to share",
            description: "Downloading video file for native sharing...",
          });
        } else if (capabilities.supportsWebShare) {
          toast({
            title: "Preparing to share",
            description: "Preparing share link...",
          });
        }

        await WebShareService.shareVideoFile(absoluteUrl, videoTitle, {
          fallbackToLink: true,
          showProgress: true,
          onProgress: (loaded, total) => {
            const progressPercent = Math.round((loaded / total) * 100);
            setProgress(progressPercent);
          },
          onSuccess: () => {
            toast({
              title: "Shared successfully!",
              description: capabilities.supportsFileShare
                ? "Video file shared to your chosen app."
                : "Share link opened successfully.",
            });
          },
          onError: (error: Error) => {
            const message =
              error instanceof WebShareError
                ? WebShareService.getErrorMessage(error)
                : "Failed to share video";

            setError(message);
            toast({
              title: "Share failed",
              description: message,
              variant: "destructive",
            });
          },
        });
      } catch (error) {
        const message =
          error instanceof WebShareError
            ? WebShareService.getErrorMessage(error)
            : "Failed to share video";

        setError(message);
        toast({
          title: "Share failed",
          description: message,
          variant: "destructive",
        });
      } finally {
        setIsSharing(false);
        setProgress(0);
      }
    },
    [capabilities, toast],
  );

  const shareAsLink = useCallback(
    async (downloadUrl: string, videoTitle: string) => {
      let absoluteUrl = new URL(downloadUrl, window.location.origin).href;
      if (window.location.protocol === "https:" && absoluteUrl.startsWith("http://")) {
        absoluteUrl = absoluteUrl.replace("http://", "https://");
      }

      try {
        setIsSharing(true);
        setError(null);

        if (WebShareService.isSupported()) {
          await navigator.share({
            title: videoTitle,
            text: "Check out this video clip!",
            url: absoluteUrl,
          });

          toast({
            title: "Shared successfully!",
            description: "Share link opened successfully.",
          });
        } else {
          // Fallback to WhatsApp
          const whatsappUrl = `https://wa.me/?text=${encodeURIComponent(
            `${videoTitle}\n${absoluteUrl}`,
          )}`;
          window.open(whatsappUrl, "_blank", "width=600,height=400");

          toast({
            title: "Opening WhatsApp",
            description: "Share link prepared for WhatsApp.",
          });
        }
      } catch (error) {
        const message = "Failed to open share dialog";
        setError(message);
        toast({
          title: "Share failed",
          description: message,
          variant: "destructive",
        });
      } finally {
        setIsSharing(false);
      }
    },
    [toast],
  );

  return {
    // State
    isSharing,
    progress,
    error,
    capabilities,

    // Actions
    shareVideoFile,
    shareAsLink,
    reset,
  };
};
