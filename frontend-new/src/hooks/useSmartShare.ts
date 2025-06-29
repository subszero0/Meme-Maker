import { useState, useCallback } from "react";

interface SmartShareProps {
  title: string;
  text: string;
  url: string;
  downloadUrl: string;
}

export const useSmartShare = () => {
  const [isSharing, setIsSharing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const share = useCallback(async (shareData: SmartShareProps) => {
    setIsSharing(true);
    setError(null);

    const { title, text, url, downloadUrl } = shareData;

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
      const response = await fetch(downloadUrl);
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

      // --- Fallback to sharing the URL ---
      if (navigator.canShare({ url })) {
        await navigator.share({
          url,
          title,
          text,
        });
      } else {
        // If neither file nor URL can be shared (unlikely if navigator.share exists)
        throw new Error("This content cannot be shared on your device.");
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
  }, []);

  return { share, isSharing, error };
};
