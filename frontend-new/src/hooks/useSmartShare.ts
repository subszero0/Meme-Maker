import { useCallback, useState } from "react";
import { config } from "../config/environment";

interface SmartShareProps {
  title: string;
  text: string;
  url: string;
}

export const useSmartShare = () => {
  const [isSharing, setIsSharing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const share = useCallback(
    async (shareData: SmartShareProps) => {
      if (isSharing) return;

      setIsSharing(true);
      setError(null);

      // FIXED: Ensure URL is absolute using correct API base URL
      let { url } = shareData;
      const { title, text } = shareData;
      if (!url.startsWith("http")) {
        const apiBaseUrl = config.API_BASE_URL || window.location.origin;
        url = `${apiBaseUrl}${url}`;
      }

      // Check for Web Share API support first
      if (!navigator.share) {
        setError("Web Share API is not supported in this browser.");
        setIsSharing(false);
        // Fallback for non-supporting browsers (e.g., copy link or show modal)
        try {
          await navigator.clipboard.writeText(url);
          alert(
            "Link copied to clipboard! Sharing is not supported on this device.",
          );
        } catch (err) {
          alert("Sharing is not supported and link could not be copied.");
        }
        return;
      }

      try {
        // --- Attempt to share the FILE first ---
        const response = await fetch(url);
        if (!response.ok) {
          throw new Error("Failed to fetch video file for sharing.");
        }
        const blob = await response.blob();
        const file = new File(
          [blob],
          `${title.replace(/[^a-z0-9]/gi, "_")}.mp4`,
          {
            type: "video/mp4",
          },
        );

        if (navigator.canShare && navigator.canShare({ files: [file] })) {
          await navigator.share({
            files: [file],
            title: title,
            text: text,
          });
          setIsSharing(false);
          return; // Success, exit
        }

        // If file sharing is not possible, inform the user.
        if (!navigator.canShare || !navigator.canShare({ files: [file] })) {
          throw new Error(
            "Direct file sharing is not supported on this device.",
          );
        }
      } catch (err: unknown) {
        // Ignore abort errors from user cancelling the share sheet
        if (err instanceof Error && err.name !== "AbortError") {
          console.error("Share failed:", err);
          setError(`Sharing failed: ${err.message}`);
        }
      } finally {
        setIsSharing(false);
      }
    },
    [isSharing],
  );

  return { share, isSharing, error };
};
