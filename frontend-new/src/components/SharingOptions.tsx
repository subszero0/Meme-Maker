import React, { useState, useCallback, useMemo } from "react";
import {
  Download,
  Copy,
  Share2,
  ExternalLink,
  RefreshCw,
  CheckCircle,
  X,
  Smartphone,
  Check,
} from "lucide-react";
import { useDeleteClip } from "@/hooks/useApi";
import { useSmartShare } from "@/hooks/useSmartShare";
import { NativeShareButton } from "./NativeShareButton";
import { config } from "@/config/environment";

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
  const [linkCopied, setLinkCopied] = useState(false);

  const { share, isSharing, error } = useSmartShare();
  const deleteClipMutation = useDeleteClip();

  // FIXED: Use correct API base URL instead of window.location.origin
  const absoluteDownloadUrl = useMemo(() => {
    // If the URL is already absolute, use it directly.
    if (downloadUrl.startsWith("http")) {
      return downloadUrl;
    }
    // FIXED: Use API_BASE_URL from config instead of window.location.origin
    // This ensures downloads go to the backend API server, not the frontend static server
    const apiBaseUrl = config.API_BASE_URL || window.location.origin;
    return `${apiBaseUrl}${downloadUrl}`;
  }, [downloadUrl]);

  const handleSmartShare = useCallback(() => {
    share({
      title: videoTitle,
      text: "Check out this video clip I made with memeit.pro!",
      url: absoluteDownloadUrl,
    });
  }, [share, videoTitle, absoluteDownloadUrl]);

  const handleCopyLink = useCallback(async () => {
    try {
      await navigator.clipboard.writeText(absoluteDownloadUrl);
      setLinkCopied(true);
      setTimeout(() => setLinkCopied(false), 2000);
    } catch (err) {
      console.error("Failed to copy link:", err);
      alert("Failed to copy link.");
    }
  }, [absoluteDownloadUrl]);

  const handleDownloadClick = useCallback(() => {
    setShowDownloadModal(true);
  }, []);

  const handleCleanup = useCallback(async () => {
    try {
      const urlParts = downloadUrl.split("/");
      const jobID = urlParts.find((part) => part.includes("-"))?.split(".")[0];

      if (jobID) {
        await deleteClipMutation.mutateAsync(jobID);
        console.log(`🗑️ Clip ${jobID} marked for deletion.`);
      }
    } catch (error) {
      console.error("Failed to delete clip:", error);
    } finally {
      onStartOver();
    }
  }, [downloadUrl, deleteClipMutation, onStartOver]);

  return (
    <>
      <div className="bg-white rounded-t-3xl p-6 space-y-6 w-full max-w-lg mx-auto shadow-2xl">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-gray-800">
            Your Clip is Ready!
          </h2>
          <p className="text-gray-600 mt-1 truncate">{videoTitle}</p>
        </div>

        {/* Main Actions */}
        <div className="space-y-4">
          {/* Smart Share Button */}
          <button
            onClick={handleSmartShare}
            disabled={isSharing}
            className="w-full bg-gradient-to-r from-blue-500 to-purple-500 text-white font-bold py-4 px-6 rounded-2xl transition-all duration-300 hover:shadow-xl hover:scale-105 flex items-center justify-center space-x-3 text-lg"
          >
            {isSharing ? (
              <>
                <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                <span>Sharing...</span>
              </>
            ) : (
              <>
                <Share2 className="w-5 h-5" />
                <span>Share Video</span>
              </>
            )}
          </button>
          {error && <p className="text-xs text-red-500 text-center">{error}</p>}
          <p className="text-xs text-gray-500 text-center">
            Tries to share the video file, falls back to a link.
          </p>
        </div>

        {/* Secondary Actions */}
        <div className="grid grid-cols-2 gap-4">
          <button
            onClick={handleCopyLink}
            className="bg-gray-100 text-gray-800 font-medium py-3 px-4 rounded-xl transition-all duration-200 hover:bg-gray-200 flex items-center justify-center space-x-2"
          >
            {linkCopied ? (
              <>
                <Check className="w-5 h-5 text-green-500" />
                <span>Copied!</span>
              </>
            ) : (
              <>
                <Copy className="w-5 h-5" />
                <span>Copy Link</span>
              </>
            )}
          </button>
          <button
            onClick={handleDownloadClick}
            className="bg-gray-100 text-gray-800 font-medium py-3 px-4 rounded-xl transition-all duration-200 hover:bg-gray-200 flex items-center justify-center space-x-2"
          >
            <Download className="w-5 h-5" />
            <span>Download MP4</span>
          </button>
        </div>

        {/* Start Over */}
        <div className="pt-4 border-t border-gray-200 text-center">
          <button
            onClick={handleCleanup}
            className="text-gray-500 hover:text-red-500 font-medium transition-colors duration-200 flex items-center justify-center w-full space-x-2"
          >
            <RefreshCw className="w-4 h-4" />
            <span>Create Another Clip</span>
          </button>
        </div>
      </div>
      <DownloadModal
        isOpen={showDownloadModal}
        onClose={() => setShowDownloadModal(false)}
        downloadUrl={absoluteDownloadUrl}
        videoTitle={videoTitle}
      />
    </>
  );
};
