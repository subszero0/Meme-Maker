import React, { useState, useEffect, useCallback, useMemo } from "react";
import {
  Settings,
  Zap,
  Monitor,
  Smartphone,
  Download,
  AlertCircle,
  Loader,
  Clock,
} from "lucide-react";
import { VideoFormat } from "@/lib/api";
import { useDetailedVideoMetadata } from "@/hooks/useApi";

interface ResolutionSelectorProps {
  videoUrl: string;
  selectedFormatId?: string;
  onFormatChange: (formatId: string | undefined) => void;
}

export const ResolutionSelector: React.FC<ResolutionSelectorProps> = ({
  videoUrl,
  selectedFormatId,
  onFormatChange,
}) => {
  // Use React Query hook instead of direct API calls
  const {
    data: metadata,
    isLoading: loading,
    error: queryError,
    refetch,
  } = useDetailedVideoMetadata(videoUrl, !!videoUrl);

  const [loadingStartTime, setLoadingStartTime] = useState<number | null>(null);

  // Track loading start time for duration calculation
  useEffect(() => {
    if (loading && !loadingStartTime) {
      setLoadingStartTime(Date.now());
    } else if (!loading && loadingStartTime) {
      const duration = (Date.now() - loadingStartTime) / 1000;
      console.log(
        `🎬 ResolutionSelector: Loaded formats in ${duration.toFixed(2)}s`,
      );
      setLoadingStartTime(null);
    }
  }, [loading, loadingStartTime]);

  // Extract formats from metadata
  const formats = useMemo(() => {
    return metadata?.formats || [];
  }, [metadata]);

  // Convert error to string for display
  const error = useMemo(() => {
    if (!queryError) return null;
    return queryError instanceof Error
      ? queryError.message
      : "Failed to load resolutions";
  }, [queryError]);

  // Helper functions
  const formatFileSize = useCallback((bytes?: number) => {
    if (!bytes) return "Unknown size";
    const mb = bytes / (1024 * 1024);
    if (mb < 1) return "< 1 MB";
    if (mb < 1000) return `~${Math.round(mb)} MB`;
    const gb = mb / 1024;
    return `~${gb.toFixed(1)} GB`;
  }, []);

  const getQualityLabel = useCallback((resolution: string) => {
    // Parse resolution string (e.g., "1920x1080" or "1280x720")
    const [width, height] = resolution.split("x").map(Number);
    if (height >= 2160) return "4K";
    if (height >= 1440) return "1440p";
    if (height >= 1080) return "1080p";
    if (height >= 720) return "720p";
    if (height >= 480) return "480p";
    if (height >= 360) return "360p";
    if (height >= 240) return "240p";
    return `${height}p`;
  }, []);

  const getQualityIcon = useCallback((resolution: string) => {
    const [, height] = resolution.split("x").map(Number);
    if (height >= 1080) return <Monitor className="w-4 h-4" />;
    if (height >= 720) return <Monitor className="w-4 h-4" />;
    return <Smartphone className="w-4 h-4" />;
  }, []);

  const getQualityDescription = useCallback((resolution: string) => {
    const [, height] = resolution.split("x").map(Number);
    if (height >= 2160) return "Ultra HD - Best quality";
    if (height >= 1440) return "2K - Excellent quality";
    if (height >= 1080) return "Full HD - Great quality";
    if (height >= 720) return "HD - Good quality";
    if (height >= 480) return "SD - Standard quality";
    if (height >= 360) return "Low - Small file";
    return "Basic quality";
  }, []);

  // Auto-select best format when formats are loaded
  useEffect(() => {
    if (formats.length > 0 && !selectedFormatId) {
      // Prefer 1080p, then 720p, then highest available
      const preferredFormat =
        formats.find((f) => f.resolution.includes("1920x1080")) ||
        formats.find((f) => f.resolution.includes("1280x720")) ||
        formats[0];

      if (preferredFormat) {
        console.log(
          "🎬 ResolutionSelector: Auto-selecting format:",
          preferredFormat.format_id,
        );
        onFormatChange(preferredFormat.format_id);
      }
    }
  }, [formats, selectedFormatId, onFormatChange]);

  // Group formats by quality for better organization
  const groupedFormats = useMemo(() => {
    const groups: { [key: string]: VideoFormat[] } = {};

    formats.forEach((format) => {
      const quality = getQualityLabel(format.resolution);
      if (!groups[quality]) {
        groups[quality] = [];
      }
      groups[quality].push(format);
    });

    // Sort groups by quality (descending)
    const sortedGroups = Object.entries(groups).sort(([a], [b]) => {
      const getHeight = (label: string) => {
        if (label === "4K") return 2160;
        return parseInt(label.replace("p", "")) || 0;
      };
      return getHeight(b) - getHeight(a);
    });

    return sortedGroups;
  }, [formats, getQualityLabel]);

  const selectedFormat = formats.find((f) => f.format_id === selectedFormatId);

  // Retry handler for failed requests
  const handleRetry = useCallback(() => {
    console.log("🔄 ResolutionSelector: Retrying format fetch...");
    refetch();
  }, [refetch]);

  // Loading state with progress indication
  if (loading) {
    const elapsed = loadingStartTime
      ? (Date.now() - loadingStartTime) / 1000
      : 0;

    return (
      <div className="space-y-4">
        <div className="text-center">
          <h3 className="text-xl font-bold text-gray-800 mb-2 flex items-center justify-center">
            <Settings className="w-5 h-5 mr-2 text-orange-500" />
            Output Quality
          </h3>
          <p className="text-gray-600">Loading available resolutions...</p>
        </div>

        <div className="flex flex-col items-center justify-center p-8 space-y-4">
          <div className="flex items-center space-x-3">
            <Loader className="w-6 h-6 animate-spin text-orange-500" />
            <span className="text-gray-600">Analyzing video formats...</span>
          </div>

          {elapsed > 2 && (
            <div className="flex items-center space-x-2 text-sm text-gray-500">
              <Clock className="w-4 h-4" />
              <span>{Math.floor(elapsed)}s elapsed</span>
            </div>
          )}

          {elapsed > 10 && (
            <div className="text-center text-sm text-gray-500 max-w-md">
              <p>
                This is taking longer than usual. The video might be large or
                the source might be slow.
              </p>
            </div>
          )}
        </div>
      </div>
    );
  }

  // Error state with retry option
  if (error) {
    return (
      <div className="space-y-4">
        <div className="text-center">
          <h3 className="text-xl font-bold text-gray-800 mb-2 flex items-center justify-center">
            <Settings className="w-5 h-5 mr-2 text-orange-500" />
            Output Quality
          </h3>
        </div>

        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-start space-x-3">
            <AlertCircle className="w-5 h-5 text-red-500 mt-0.5 flex-shrink-0" />
            <div className="flex-1">
              <h4 className="font-medium text-red-800 mb-1">
                Failed to Load Video Formats
              </h4>
              <p className="text-sm text-red-600 mb-3">{error}</p>
              <button
                onClick={handleRetry}
                className="px-3 py-1 bg-red-100 hover:bg-red-200 text-red-700 text-sm rounded-md transition-colors"
              >
                Try Again
              </button>
            </div>
          </div>
        </div>

        {/* Provide fallback options */}
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <h4 className="font-medium text-yellow-800 mb-2">
            Using Fallback Options
          </h4>
          <div className="space-y-2">
            <button
              onClick={() => onFormatChange("22")}
              className={`w-full p-3 border rounded-lg text-left transition-colors ${
                selectedFormatId === "22"
                  ? "border-orange-500 bg-orange-50"
                  : "border-gray-300 hover:border-gray-400"
              }`}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <Monitor className="w-4 h-4 text-gray-600" />
                  <div>
                    <div className="font-medium">720p HD</div>
                    <div className="text-sm text-gray-600">
                      Standard quality fallback
                    </div>
                  </div>
                </div>
              </div>
            </button>

            <button
              onClick={() => onFormatChange("18")}
              className={`w-full p-3 border rounded-lg text-left transition-colors ${
                selectedFormatId === "18"
                  ? "border-orange-500 bg-orange-50"
                  : "border-gray-300 hover:border-gray-400"
              }`}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <Smartphone className="w-4 h-4 text-gray-600" />
                  <div>
                    <div className="font-medium">360p SD</div>
                    <div className="text-sm text-gray-600">
                      Lower quality, smaller file
                    </div>
                  </div>
                </div>
              </div>
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="text-center">
        <h3 className="text-xl font-bold text-gray-800 mb-2 flex items-center justify-center">
          <Settings className="w-5 h-5 mr-2 text-orange-500" />
          Output Quality
        </h3>
        <p className="text-gray-600">Choose your preferred resolution</p>
        {error && (
          <p className="text-sm text-yellow-600 mt-1">Using fallback formats</p>
        )}
        {!loading && formats.length > 0 && (
          <p className="text-xs text-gray-500 mt-1">
            {formats.length} formats available
          </p>
        )}
      </div>

      {/* Selected Format Display */}
      {selectedFormat && (
        <div className="bg-gradient-to-r from-orange-50 to-red-50 border border-orange-200 rounded-2xl p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              {getQualityIcon(selectedFormat.resolution)}
              <div>
                <p className="font-bold text-gray-800">
                  {getQualityLabel(selectedFormat.resolution)}
                </p>
                <p className="text-sm text-gray-600">
                  {selectedFormat.resolution} •{" "}
                  {selectedFormat.ext.toUpperCase()}
                </p>
              </div>
            </div>
            <div className="text-right">
              <p className="text-sm font-medium text-gray-700">
                {formatFileSize(selectedFormat.filesize)}
              </p>
              <p className="text-xs text-gray-500">
                {selectedFormat.fps
                  ? `${selectedFormat.fps}fps`
                  : "Variable fps"}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Format Selection */}
      <div className="space-y-3 max-h-80 overflow-y-auto">
        {groupedFormats.map(([quality, qualityFormats]) => (
          <div key={quality} className="space-y-2">
            {/* Quality Group Header */}
            <div className="flex items-center space-x-2 px-2">
              <div className="text-sm font-medium text-gray-700">{quality}</div>
              <div className="flex-1 border-t border-gray-200"></div>
            </div>

            {/* Format Options */}
            <div className="space-y-1">
              {qualityFormats.map((format) => (
                <button
                  key={format.format_id}
                  onClick={() => {
                    console.log("🎬 Format selected:", format.format_id);
                    onFormatChange(format.format_id);
                  }}
                  className={`w-full p-3 rounded-xl border transition-all duration-200 text-left ${
                    selectedFormatId === format.format_id
                      ? "border-orange-300 bg-orange-50 ring-2 ring-orange-200"
                      : "border-gray-200 bg-white hover:border-orange-200 hover:bg-orange-25"
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      {getQualityIcon(format.resolution)}
                      <div>
                        <p className="font-medium text-gray-800">
                          {format.resolution}
                        </p>
                        <p className="text-sm text-gray-500">
                          {format.vcodec} / {format.acodec}
                        </p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="text-sm font-medium text-gray-600">
                        {formatFileSize(format.filesize)}
                      </p>
                      <p className="text-xs text-gray-400">
                        {format.fps ? `${format.fps}fps` : ""} {format.ext}
                      </p>
                    </div>
                  </div>
                </button>
              ))}
            </div>
          </div>
        ))}
      </div>

      {formats.length > 0 && (
        <div className="text-center">
          <p className="text-xs text-gray-500">
            Found {formats.length} available format
            {formats.length !== 1 ? "s" : ""}
          </p>
        </div>
      )}
    </div>
  );
};
