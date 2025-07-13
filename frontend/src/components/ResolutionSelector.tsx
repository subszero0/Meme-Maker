"use client";

import { useState, useEffect } from "react";

interface VideoFormat {
  format_id: string;
  ext: string;
  resolution: string;
  url: string;
  filesize?: number;
  fps?: number;
  vcodec: string;
  acodec: string;
  format_note: string;
}

interface ResolutionSelectorProps {
  url: string;
  selectedFormatId?: string;
  onFormatChange: (formatId: string | undefined) => void;
}

export default function ResolutionSelector({
  url,
  selectedFormatId,
  onFormatChange,
}: ResolutionSelectorProps) {
  const [formats, setFormats] = useState<VideoFormat[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isOpen, setIsOpen] = useState(false);

  useEffect(() => {
    const fetchFormats = async () => {
      console.log("🎬 ResolutionSelector: Starting format fetch for URL:", url);
      console.log(
        "🎬 ResolutionSelector: Current selectedFormatId:",
        selectedFormatId,
      );

      setLoading(true);
      setError(null);

      try {
        const apiUrl = `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/v1/metadata/extract`;
        console.log("🎬 ResolutionSelector: Making API request to:", apiUrl);
        console.log("🎬 ResolutionSelector: Request payload:", { url });

        const response = await fetch(apiUrl, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ url }),
        });

        if (!response.ok) {
          throw new Error(
            `Failed to fetch video formats: ${response.status} ${response.statusText}`,
          );
        }

        const data = await response.json();
        console.log("🎬 ResolutionSelector: API response received:", data);
        console.log(
          "🎬 ResolutionSelector: Number of formats found:",
          data.formats?.length || 0,
        );

        setFormats(data.formats || []);

        // Auto-select best quality if no format selected
        if (!selectedFormatId && data.formats && data.formats.length > 0) {
          const bestFormat = data.formats[0];
          console.log(
            "🎬 ResolutionSelector: Auto-selecting best format:",
            bestFormat.format_id,
            bestFormat.resolution,
          );
          onFormatChange(bestFormat.format_id);
        } else {
          console.log(
            "🎬 ResolutionSelector: Format already selected or no formats available",
          );
        }
      } catch (err) {
        console.error(
          "🎬 ResolutionSelector: Failed to fetch video formats:",
          err,
        );
        console.log(
          "🎬 ResolutionSelector: Falling back to default format selection",
        );

        // Fallback to default formats when API fails
        const defaultFormats = [
          {
            format_id: "18",
            ext: "mp4",
            resolution: "640x360",
            fps: 25,
            vcodec: "avc1.42001E",
            acodec: "mp4a.40.2",
            format_note: "360p",
          },
          {
            format_id: "22",
            ext: "mp4",
            resolution: "1280x720",
            fps: 25,
            vcodec: "avc1.64001F",
            acodec: "mp4a.40.2",
            format_note: "720p",
          },
        ];

        setFormats(defaultFormats);

        // Auto-select 720p if available, otherwise first format
        const preferredFormat =
          defaultFormats.find((f) => f.resolution === "1280x720") ||
          defaultFormats[0];
        if (preferredFormat && !selectedFormatId) {
          console.log(
            "🎬 ResolutionSelector: Auto-selecting fallback format:",
            preferredFormat.format_id,
          );
          onFormatChange(preferredFormat.format_id);
        }

        setError(null); // Clear error since we have fallback
      } finally {
        setLoading(false);
        console.log("🎬 ResolutionSelector: Format fetch completed");
      }
    };

    if (url) {
      fetchFormats();
    }
  }, [url, selectedFormatId, onFormatChange]);

  const selectedFormat = formats.find((f) => f.format_id === selectedFormatId);
  console.log(
    "🎬 ResolutionSelector: Currently selected format:",
    selectedFormat,
  );

  const formatFileSize = (bytes?: number) => {
    if (!bytes) return "";
    const mb = bytes / (1024 * 1024);
    return mb < 1 ? "< 1 MB" : `~${Math.round(mb)} MB`;
  };

  const getQualityLabel = (resolution: string) => {
    const height = parseInt(resolution.split("x")[1]);
    if (height >= 2160) return "4K";
    if (height >= 1440) return "1440p";
    if (height >= 1080) return "1080p";
    if (height >= 720) return "720p";
    if (height >= 480) return "480p";
    if (height >= 360) return "360p";
    return `${height}p`;
  };

  if (loading) {
    return (
      <div>
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
          Resolution
        </label>
        <div className="w-full p-3 border border-gray-300 rounded-md bg-gray-50 dark:bg-gray-800 dark:border-gray-600">
          <div className="flex items-center space-x-2">
            <div className="animate-spin h-4 w-4 border-2 border-indigo-600 border-t-transparent rounded-full"></div>
            <span className="text-sm text-gray-600 dark:text-gray-400">
              Loading resolutions...
            </span>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div>
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
          Resolution
        </label>
        <div className="w-full p-3 border border-red-300 rounded-md bg-red-50 dark:bg-red-900/20 dark:border-red-600">
          <span className="text-sm text-red-600 dark:text-red-400">
            {error}
          </span>
        </div>
      </div>
    );
  }

  if (formats.length === 0) {
    return (
      <div>
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
          Resolution
        </label>
        <div className="w-full p-3 border border-gray-300 rounded-md bg-gray-50 dark:bg-gray-800 dark:border-gray-600">
          <span className="text-sm text-gray-600 dark:text-gray-400">
            No resolutions available
          </span>
        </div>
      </div>
    );
  }

  return (
    <div className="relative">
      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
        Resolution
      </label>
      <div className="relative">
        <button
          type="button"
          className="w-full bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-md pl-3 pr-10 py-2 text-left cursor-default focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 dark:focus:border-indigo-400 sm:text-sm text-gray-900 dark:text-white"
          onClick={() => setIsOpen(!isOpen)}
        >
          <span className="block truncate">
            {selectedFormat ? (
              <span className="flex items-center justify-between">
                <span className="text-gray-900 dark:text-white">
                  <strong>{getQualityLabel(selectedFormat.resolution)}</strong>{" "}
                  ({selectedFormat.resolution})
                </span>
                <span className="text-gray-500 dark:text-gray-400 text-xs ml-2">
                  {formatFileSize(selectedFormat.filesize)}
                </span>
              </span>
            ) : (
              <span className="text-gray-500 dark:text-gray-400">
                Select resolution
              </span>
            )}
          </span>
          <span className="absolute inset-y-0 right-0 flex items-center pr-2 pointer-events-none">
            <svg
              className="h-5 w-5 text-gray-400 dark:text-gray-500"
              viewBox="0 0 20 20"
              fill="currentColor"
            >
              <path
                fillRule="evenodd"
                d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z"
                clipRule="evenodd"
              />
            </svg>
          </span>
        </button>

        {isOpen && (
          <div className="absolute z-10 mt-1 w-full bg-white dark:bg-gray-800 shadow-lg max-h-60 rounded-md py-1 text-base ring-1 ring-black ring-opacity-5 dark:ring-gray-700 overflow-auto focus:outline-none sm:text-sm border border-gray-200 dark:border-gray-600">
            {formats.map((format) => (
              <div
                key={format.format_id}
                className={`cursor-pointer select-none relative py-2 pl-3 pr-9 hover:bg-indigo-50 dark:hover:bg-indigo-900/20 ${
                  selectedFormatId === format.format_id
                    ? "bg-indigo-100 dark:bg-indigo-900/30 text-indigo-900 dark:text-indigo-100"
                    : "text-gray-900 dark:text-gray-100"
                }`}
                onClick={() => {
                  console.log(
                    "🎬 ResolutionSelector: User selected format:",
                    format.format_id,
                    format.resolution,
                  );
                  onFormatChange(format.format_id);
                  setIsOpen(false);
                }}
              >
                <div className="flex items-center justify-between">
                  <div className="flex flex-col">
                    <span
                      className={`font-medium ${
                        selectedFormatId === format.format_id
                          ? "text-indigo-900 dark:text-indigo-100"
                          : "text-gray-900 dark:text-gray-100"
                      }`}
                    >
                      {getQualityLabel(format.resolution)} ({format.resolution})
                    </span>
                    <span className="text-xs text-gray-500 dark:text-gray-400">
                      {format.vcodec} •{" "}
                      {format.fps ? `${format.fps}fps` : "Variable fps"}
                    </span>
                  </div>
                  <span className="text-xs text-gray-500 dark:text-gray-400">
                    {formatFileSize(format.filesize)}
                  </span>
                </div>
                {selectedFormatId === format.format_id && (
                  <span className="absolute inset-y-0 right-0 flex items-center pr-4">
                    <svg
                      className="h-5 w-5 text-indigo-600 dark:text-indigo-400"
                      viewBox="0 0 20 20"
                      fill="currentColor"
                    >
                      <path
                        fillRule="evenodd"
                        d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                        clipRule="evenodd"
                      />
                    </svg>
                  </span>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
      <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
        Higher resolutions may take longer to process
      </p>
    </div>
  );
}
