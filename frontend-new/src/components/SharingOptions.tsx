import React, { useState, useCallback, useMemo } from "react";
import {
  Download,
  Share2,
  ExternalLink,
  RefreshCw,
  CheckCircle,
  X,
} from "lucide-react";
import { useDeleteClip } from "@/hooks/useApi";

interface SharingOptionsProps {
  downloadUrl: string;
  videoTitle: string;
  onStartOver: () => void;
}

interface DownloadModalProps {
  isOpen: boolean;
  onClose: () => void;
  downloadUrl: string;
  videoTitle: string;
  fileSize?: string;
}

const DownloadModal: React.FC<DownloadModalProps> = ({
  isOpen,
  onClose,
  downloadUrl,
  videoTitle,
  fileSize,
}) => {
  const [isDownloading, setIsDownloading] = useState(false);
  const [downloadComplete, setDownloadComplete] = useState(false);

  const handleDownload = useCallback(async () => {
    setIsDownloading(true);

    try {
      // Create a link element and trigger download
      const link = document.createElement("a");
      link.href = downloadUrl;
      link.download = `${videoTitle.replace(/[^a-z0-9]/gi, "_").toLowerCase()}_clip.mp4`;
      link.target = "_blank";

      // Append to body, click, and remove
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);

      // Show completion state
      setTimeout(() => {
        setIsDownloading(false);
        setDownloadComplete(true);

        // Auto close after showing success
        setTimeout(() => {
          setDownloadComplete(false);
          onClose();
        }, 2000);
      }, 1000);
    } catch (error) {
      console.error("Download failed:", error);
      setIsDownloading(false);
      // Could show error state here
    }
  }, [downloadUrl, videoTitle, onClose]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl max-w-md w-full p-6 space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-bold text-gray-800">
            Download Your Clip
          </h3>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
            disabled={isDownloading}
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="space-y-3">
          <div className="bg-gray-50 rounded-lg p-3">
            <p className="font-medium text-gray-800 truncate">{videoTitle}</p>
            {fileSize && (
              <p className="text-sm text-gray-600">File size: {fileSize}</p>
            )}
          </div>

          {downloadComplete ? (
            <div className="text-center py-4">
              <CheckCircle className="w-12 h-12 text-green-500 mx-auto mb-2" />
              <p className="text-green-600 font-medium">Download Started!</p>
              <p className="text-sm text-gray-600">
                Check your downloads folder
              </p>
            </div>
          ) : (
            <button
              onClick={handleDownload}
              disabled={isDownloading}
              className={`w-full font-bold py-3 px-6 rounded-xl transition-all duration-200 flex items-center justify-center space-x-2 ${
                isDownloading
                  ? "bg-gray-300 text-gray-500 cursor-not-allowed"
                  : "bg-gradient-to-r from-orange-400 to-red-400 text-white hover:shadow-lg"
              }`}
            >
              {isDownloading ? (
                <>
                  <div className="w-4 h-4 border-2 border-gray-400 border-t-transparent rounded-full animate-spin" />
                  <span>Downloading...</span>
                </>
              ) : (
                <>
                  <Download className="w-4 h-4" />
                  <span>Download MP4</span>
                </>
              )}
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export const SharingOptions: React.FC<SharingOptionsProps> = ({
  downloadUrl,
  videoTitle,
  onStartOver,
}) => {
  const [showDownloadModal, setShowDownloadModal] = useState(false);
  const [sharingPlatform, setSharingPlatform] = useState<string | null>(null);

  const deleteClipMutation = useDeleteClip();

  // Generate sharing URL based on current domain
  const sharingUrl = useMemo(() => {
    // In production, this would be the actual app domain
    const baseUrl = window.location.origin;
    return `${baseUrl}/clip/${encodeURIComponent(downloadUrl)}`;
  }, [downloadUrl]);

  // Platform configurations with real sharing URLs
  const platforms = [
    {
      id: "whatsapp",
      name: "WhatsApp",
      icon: "💬",
      color: "from-green-500 to-green-600",
      description: "Send to contacts",
      bgColor: "bg-green-50",
      borderColor: "border-green-200",
      shareUrl: `https://wa.me/?text=${encodeURIComponent(`Check out this video clip: ${videoTitle}\n${sharingUrl}`)}`,
    },
    {
      id: "twitter",
      name: "Twitter / X",
      icon: "🐦",
      color: "from-blue-500 to-blue-600",
      description: "Share as tweet",
      bgColor: "bg-blue-50",
      borderColor: "border-blue-200",
      shareUrl: `https://twitter.com/intent/tweet?text=${encodeURIComponent(`Check out this clip: ${videoTitle}`)}&url=${encodeURIComponent(sharingUrl)}`,
    },
    {
      id: "facebook",
      name: "Facebook",
      icon: "📘",
      color: "from-blue-600 to-blue-700",
      description: "Post to timeline",
      bgColor: "bg-blue-50",
      borderColor: "border-blue-200",
      shareUrl: `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(sharingUrl)}`,
    },
    {
      id: "reddit",
      name: "Reddit",
      icon: "🤖",
      color: "from-orange-500 to-red-500",
      description: "Post to subreddit",
      bgColor: "bg-orange-50",
      borderColor: "border-orange-200",
      shareUrl: `https://reddit.com/submit?url=${encodeURIComponent(sharingUrl)}&title=${encodeURIComponent(videoTitle)}`,
    },
    {
      id: "telegram",
      name: "Telegram",
      icon: "✈️",
      color: "from-blue-400 to-blue-500",
      description: "Share in chat",
      bgColor: "bg-blue-50",
      borderColor: "border-blue-200",
      shareUrl: `https://t.me/share/url?url=${encodeURIComponent(sharingUrl)}&text=${encodeURIComponent(videoTitle)}`,
    },
    {
      id: "copy",
      name: "Copy Link",
      icon: "🔗",
      color: "from-gray-500 to-gray-600",
      description: "Copy to clipboard",
      bgColor: "bg-gray-50",
      borderColor: "border-gray-200",
      shareUrl: sharingUrl,
    },
  ];

  const handlePlatformClick = useCallback(
    async (platform: { id: string; name: string; shareUrl: string }) => {
      setSharingPlatform(platform.id);

      try {
        if (platform.id === "copy") {
          // Copy to clipboard
          await navigator.clipboard.writeText(platform.shareUrl);
          console.log("🔗 Link copied to clipboard");
        } else {
          // Open sharing URL in new window
          window.open(platform.shareUrl, "_blank", "width=600,height=400");
          console.log(`🔗 Sharing to ${platform.name}`);
        }

        // Reset sharing state after animation
        setTimeout(() => setSharingPlatform(null), 2000);
      } catch (error) {
        console.error(`Failed to share to ${platform.name}:`, error);
        setSharingPlatform(null);
      }
    },
    [],
  );

  const handleDownloadClick = useCallback(() => {
    setShowDownloadModal(true);
  }, []);

  const handleCleanup = useCallback(async () => {
    try {
      // Extract job ID from download URL if possible
      const urlParts = downloadUrl.split("/");
      const potentialJobId = urlParts[urlParts.length - 1]?.split(".")[0];

      if (potentialJobId) {
        console.log("🗑️ Cleaning up clip file:", potentialJobId);
        await deleteClipMutation.mutateAsync(potentialJobId);
      }
    } catch (error) {
      console.warn("Failed to clean up clip file:", error);
      // Non-critical error, continue with start over
    }

    onStartOver();
  }, [downloadUrl, deleteClipMutation, onStartOver]);

  return (
    <>
      <div className="space-y-6">
        <div className="text-center">
          <h3 className="text-2xl font-bold text-gray-800 mb-2 flex items-center justify-center">
            <CheckCircle className="w-6 h-6 mr-2 text-green-500" />
            Your Clip is Ready!
          </h3>
          <p className="text-gray-600">Download or share your video creation</p>
          <p className="text-sm text-gray-500 mt-1 truncate max-w-md mx-auto">
            {videoTitle}
          </p>
        </div>

        {/* Download Section */}
        <div className="bg-gradient-to-r from-green-50 to-emerald-50 p-6 rounded-2xl border border-green-200">
          <div className="text-center space-y-3">
            <h4 className="font-semibold text-gray-800 text-lg">
              Download Your Video
            </h4>
            <p className="text-gray-600 text-sm">
              Save the clip to your device
            </p>

            <button
              onClick={handleDownloadClick}
              className="w-full bg-gradient-to-r from-green-500 to-emerald-500 text-white font-bold py-4 px-6 rounded-2xl shadow-lg hover:shadow-xl transition-all duration-300 flex items-center justify-center space-x-3 hover:scale-105"
            >
              <Download className="w-5 h-5" />
              <span className="text-lg">Download MP4</span>
            </button>
          </div>
        </div>

        {/* Sharing Section */}
        <div className="space-y-4">
          <div className="text-center">
            <h4 className="font-semibold text-gray-800 text-lg flex items-center justify-center">
              <Share2 className="w-5 h-5 mr-2 text-orange-500" />
              Share Your Creation
            </h4>
            <p className="text-gray-600 text-sm">
              Share directly to social platforms
            </p>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
            {platforms.map((platform) => (
              <button
                key={platform.id}
                onClick={() => handlePlatformClick(platform)}
                disabled={sharingPlatform === platform.id}
                className={`${platform.bgColor} ${platform.borderColor} border-2 p-4 rounded-xl transition-all duration-300 hover:shadow-lg ${
                  sharingPlatform === platform.id
                    ? "scale-95 animate-pulse"
                    : "hover:scale-105"
                }`}
              >
                <div className="text-center space-y-2">
                  <div className="text-2xl">{platform.icon}</div>
                  <div>
                    <h5 className="font-medium text-gray-800 text-sm">
                      {platform.name}
                    </h5>
                    <p className="text-xs text-gray-600">
                      {platform.description}
                    </p>
                  </div>

                  {sharingPlatform === platform.id ? (
                    <div className="flex items-center justify-center space-x-1 text-gray-600">
                      <div className="w-3 h-3 border-2 border-gray-400 border-t-transparent rounded-full animate-spin" />
                      <span className="text-xs">
                        {platform.id === "copy" ? "Copied!" : "Sharing..."}
                      </span>
                    </div>
                  ) : (
                    <div
                      className={`bg-gradient-to-r ${platform.color} text-white py-1 px-3 rounded-lg text-xs font-medium flex items-center justify-center space-x-1`}
                    >
                      <ExternalLink className="w-3 h-3" />
                      <span>Share</span>
                    </div>
                  )}
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* Actions */}
        <div className="flex flex-col sm:flex-row gap-3 pt-4 border-t border-gray-200">
          <button
            onClick={handleCleanup}
            disabled={deleteClipMutation.isPending}
            className="flex-1 bg-gradient-to-r from-orange-400 to-red-400 text-white font-bold py-3 px-6 rounded-xl shadow-lg hover:shadow-xl transition-all duration-300 flex items-center justify-center space-x-2 hover:scale-105"
          >
            <RefreshCw
              className={`w-4 h-4 ${deleteClipMutation.isPending ? "animate-spin" : ""}`}
            />
            <span>Create Another Clip</span>
          </button>
        </div>

        <div className="text-center text-sm text-gray-500 space-y-1">
          <p>🔒 Your videos are processed securely</p>
          <p>🗑️ Files are automatically cleaned up after download</p>
        </div>
      </div>

      {/* Download Modal */}
      <DownloadModal
        isOpen={showDownloadModal}
        onClose={() => setShowDownloadModal(false)}
        downloadUrl={downloadUrl}
        videoTitle={videoTitle}
      />
    </>
  );
};
