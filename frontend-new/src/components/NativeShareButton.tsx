import React from "react";
import {
  Share2,
  Smartphone,
  Download,
  ExternalLink,
  Loader2,
} from "lucide-react";
import { useWebShare } from "../hooks/useWebShare";
import { Button } from "./ui/button";
import { Progress } from "./ui/progress";

interface NativeShareButtonProps {
  downloadUrl: string;
  videoTitle: string;
  className?: string;
  variant?: "default" | "outline" | "secondary";
  size?: "sm" | "md" | "lg";
  showCapabilities?: boolean;
}

export const NativeShareButton: React.FC<NativeShareButtonProps> = ({
  downloadUrl,
  videoTitle,
  className = "",
  variant = "default",
  size = "md",
  showCapabilities = true,
}) => {
  const {
    isSharing,
    progress,
    error,
    capabilities,
    shareVideoFile,
    shareAsLink,
    reset,
  } = useWebShare();

  const getSizeClasses = () => {
    switch (size) {
      case "sm":
        return "px-3 py-2 text-sm";
      case "lg":
        return "px-8 py-4 text-lg";
      default:
        return "px-6 py-3";
    }
  };

  const getButtonText = () => {
    if (isSharing) {
      return progress > 0 ? `Downloading ${progress}%` : "Preparing...";
    }

    if (capabilities.supportsFileShare) {
      return "Share Video File";
    } else if (capabilities.supportsWebShare) {
      return "Share Link";
    } else {
      return "Share to WhatsApp";
    }
  };

  const getButtonIcon = () => {
    if (isSharing) {
      return <Loader2 className="w-4 h-4 animate-spin" />;
    }

    if (capabilities.supportsFileShare) {
      return <Smartphone className="w-4 h-4" />;
    } else if (capabilities.supportsWebShare) {
      return <Share2 className="w-4 h-4" />;
    } else {
      return <ExternalLink className="w-4 h-4" />;
    }
  };

  const getButtonVariant = () => {
    if (capabilities.supportsFileShare) {
      return "default"; // Primary for best experience
    } else if (capabilities.supportsWebShare) {
      return "secondary"; // Secondary for good experience
    } else {
      return "outline"; // Outline for fallback
    }
  };

  const handleShare = async () => {
    if (isSharing) return;

    reset(); // Clear any previous errors

    if (capabilities.recommendedApproach === "web-share") {
      await shareVideoFile(downloadUrl, videoTitle);
    } else {
      await shareAsLink(downloadUrl, videoTitle);
    }
  };

  return (
    <div className="space-y-3">
      {/* Main Share Button */}
      <Button
        onClick={handleShare}
        disabled={isSharing}
        variant={getButtonVariant()}
        className={`${getSizeClasses()} ${className} relative overflow-hidden transition-all duration-300 hover:scale-105`}
      >
        <div className="flex items-center space-x-2">
          {getButtonIcon()}
          <span className="font-medium">{getButtonText()}</span>
        </div>
      </Button>

      {/* Progress Bar */}
      {isSharing && progress > 0 && (
        <div className="space-y-1">
          <Progress value={progress} className="h-2" />
          <p className="text-xs text-gray-500 text-center">
            Downloading video file... {progress}%
          </p>
        </div>
      )}

      {/* Platform Capabilities Info */}
      {showCapabilities && !isSharing && (
        <div className="text-xs text-gray-600 space-y-1">
          <div className="flex items-center justify-center space-x-4">
            <div className="flex items-center space-x-1">
              <div
                className={`w-2 h-2 rounded-full ${
                  capabilities.supportsFileShare
                    ? "bg-green-500"
                    : "bg-gray-300"
                }`}
              />
              <span>File sharing</span>
            </div>
            <div className="flex items-center space-x-1">
              <div
                className={`w-2 h-2 rounded-full ${
                  capabilities.supportsWebShare ? "bg-green-500" : "bg-gray-300"
                }`}
              />
              <span>Web Share API</span>
            </div>
            <div className="flex items-center space-x-1">
              <div
                className={`w-2 h-2 rounded-full ${
                  capabilities.isMobile ? "bg-blue-500" : "bg-gray-300"
                }`}
              />
              <span>Mobile</span>
            </div>
          </div>

          <p className="text-center text-gray-500">
            {capabilities.supportsFileShare &&
              "🎉 Best experience: Native file sharing available"}
            {!capabilities.supportsFileShare &&
              capabilities.supportsWebShare &&
              "📱 Good experience: Native link sharing available"}
            {!capabilities.supportsWebShare &&
              "🔗 Fallback: Will open platform-specific share"}
          </p>
        </div>
      )}

      {/* Error Display */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-3">
          <p className="text-sm text-red-700">{error}</p>
          <div className="mt-2 flex space-x-2">
            <Button
              onClick={() => shareAsLink(downloadUrl, videoTitle)}
              variant="outline"
              size="sm"
              className="text-xs"
            >
              <ExternalLink className="w-3 h-3 mr-1" />
              Share Link Instead
            </Button>
            <Button
              onClick={reset}
              variant="ghost"
              size="sm"
              className="text-xs"
            >
              Dismiss
            </Button>
          </div>
        </div>
      )}
    </div>
  );
};

// Alternative: Compact version for inline use
export const CompactNativeShareButton: React.FC<NativeShareButtonProps> = ({
  downloadUrl,
  videoTitle,
  className = "",
}) => {
  const { isSharing, capabilities, shareVideoFile, shareAsLink } =
    useWebShare();

  const handleShare = async () => {
    if (capabilities.recommendedApproach === "web-share") {
      await shareVideoFile(downloadUrl, videoTitle);
    } else {
      await shareAsLink(downloadUrl, videoTitle);
    }
  };

  return (
    <Button
      onClick={handleShare}
      disabled={isSharing}
      variant="ghost"
      size="sm"
      className={`${className} hover:bg-gray-100`}
    >
      {isSharing ? (
        <Loader2 className="w-4 h-4 animate-spin" />
      ) : (
        <Share2 className="w-4 h-4" />
      )}
    </Button>
  );
};
