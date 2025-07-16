import React, { useState, useCallback, useEffect, useMemo } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { Button } from "@/components/ui/button";
import { UrlInput } from "@/components/UrlInput";
import { VideoPlayer } from "@/components/VideoPlayer";
import { Timeline } from "@/components/Timeline";
import { ResolutionSelector } from "@/components/ResolutionSelector";
import { SharingOptions } from "@/components/SharingOptions";
import { LoadingAnimation } from "@/components/LoadingAnimation";
import { MetadataResponse, VideoMetadata } from "@/types/metadata";
import { useCreateJob } from "@/hooks/useApi";
import { useToast } from "@/components/ui/use-toast";
import { queryKeys } from "@/hooks/useApi";
import { JobResponse, JobStatus } from "@/types/job";
import logoUrl from "../../Logos/white.svg";
import { Link } from "react-router-dom";

// Application phases
type AppPhase = "input" | "editing" | "processing" | "completed" | "error";

interface CompletedState {
  downloadUrl: string;
  videoTitle: string;
}

const Index = () => {
  const { toast } = useToast();
  const [phase, setPhase] = useState<AppPhase>("input");
  const [error, setError] = useState<string | null>(null);

  // Video and metadata state
  const [videoUrl, setVideoUrl] = useState("");
  const [sourceUrl, setSourceUrl] = useState("");
  const [videoMetadata, setVideoMetadata] = useState<VideoMetadata | null>(
    null,
  );

  // Job processing state
  const [currentJobId, setCurrentJobId] = useState<string | null>(null);
  const [completedState, setCompletedState] = useState<CompletedState | null>(
    null,
  );

  // Clip selection state
  const [clipStart, setClipStart] = useState(0);
  const [clipEnd, setClipEnd] = useState<number>(0);

  // Format selection state
  const [selectedFormatId, setSelectedFormatId] = useState<string | null>(null);
  const [selectedResolution, setSelectedResolution] = useState<string | null>(
    null,
  );

  // Job creation mutation
  const createJobMutation = useCreateJob();

  // Get video duration from metadata or default
  const videoDuration = useMemo(() => {
    return videoMetadata?.duration || 300; // Default 5 minutes if no metadata
  }, [videoMetadata]);

  // Validate clip selection
  const clipValidation = useMemo(() => {
    const duration = clipEnd - clipStart;
    const maxDuration = 180; // 3 minutes in seconds

    return {
      isValid: clipEnd > clipStart && duration <= maxDuration && duration > 0,
      duration,
      exceedsMaxDuration: duration > maxDuration,
      invalidRange: clipEnd <= clipStart,
    };
  }, [clipStart, clipEnd]);

  // Overall form validation
  const canCreateClip = useMemo(() => {
    return (
      videoMetadata &&
      clipValidation.isValid &&
      selectedFormatId &&
      phase === "editing" &&
      !createJobMutation.isPending
    );
  }, [
    videoMetadata,
    clipValidation.isValid,
    selectedFormatId,
    phase,
    createJobMutation.isPending,
  ]);

  // Handle URL submission with metadata
  const handleUrlSubmit = useCallback(
    (url: string, metadata: VideoMetadata) => {
      setSourceUrl(url);
      setVideoMetadata(metadata);
      setPhase("editing");
      setError(null);

      // --- Robust URL Selection Logic ---
      const getPreviewUrl = (): string => {
        // 1. PRIORITY: Use manifest_url (DASH/HLS) if provided – this contains both audio and video.
        if (metadata?.manifest_url) {
          const apiBase = import.meta.env.DEV ? "http://localhost:8000" : "";
          const proxyUrl = `${apiBase}/api/v1/video/proxy?url=${encodeURIComponent(metadata.manifest_url)}`;
          console.log(
            "Using backend proxy for manifest URL:",
            metadata.manifest_url,
          );
          console.log("Proxy URL:", proxyUrl);
          return proxyUrl;
        }

        // 2. Fallback: Use the best available video format URL from metadata for proxy
        // The proxy is designed to stream direct video file URLs, not post URLs

        if (metadata?.formats && metadata.formats.length > 0) {
          // Find the best format for preview (prefer mp4, reasonable quality)
          const mp4Formats = metadata.formats.filter(
            (f) =>
              f.url &&
              (f.ext === "mp4" ||
                f.format_note?.toLowerCase().includes("mp4")) &&
              f.url.startsWith("https://"),
          );

          const selectedFormat =
            mp4Formats.find(
              (f) =>
                f.format_note?.toLowerCase().includes("720p") ||
                f.format_note?.toLowerCase().includes("medium"),
            ) ||
            mp4Formats[0] ||
            metadata.formats[0];

          if (selectedFormat?.url) {
            // Use direct FastAPI URL in development to bypass Vite proxy issues with video streams
            // This ensures audio playback works reliably (Vite proxy interferes with media streaming)
            const apiBase = import.meta.env.DEV ? "http://localhost:8000" : "";
            const proxyUrl = `${apiBase}/api/v1/video/proxy?url=${encodeURIComponent(selectedFormat.url)}`;
            console.log(
              "Using backend proxy for video file:",
              selectedFormat.url,
            );
            console.log("Proxy URL:", proxyUrl);
            return proxyUrl;
          }
        }

        // Fallback: if no formats available, return a placeholder
        console.warn("No suitable video format found for preview");
        return "";
      };

      const previewUrl = getPreviewUrl();
      setVideoUrl(previewUrl); // This state now holds the best URL for the player

      // Reset all other states
      setCurrentJobId(null);
      setCompletedState(null);
      setSelectedFormatId(null);
      setSelectedResolution(null);

      // Initialize clip selection based on video duration
      setClipStart(0);
      setClipEnd(Math.min(metadata.duration, 30)); // Default to 30 seconds or video length
    },
    [],
  );

  // Handle video duration change from player
  const handleVideoDurationChange = useCallback(
    (duration: number) => {
      // Update metadata if duration is different (sometimes player provides more accurate duration)
      if (videoMetadata && Math.abs(videoMetadata.duration - duration) > 1) {
        setVideoMetadata((prev) => (prev ? { ...prev, duration } : null));

        // Adjust clip end if it exceeds new duration
        if (clipEnd > duration) {
          setClipEnd(duration);
        }
      }
    },
    [videoMetadata, clipEnd],
  );

  // Handle clip start change with validation
  const handleClipStartChange = useCallback(
    (start: number) => {
      const clampedStart = Math.max(0, Math.min(start, videoDuration));
      setClipStart(clampedStart);

      // Ensure end is after start
      if (clipEnd <= clampedStart) {
        setClipEnd(Math.min(clampedStart + 1, videoDuration));
      }
    },
    [videoDuration, clipEnd],
  );

  // Handle clip end change with validation
  const handleClipEndChange = useCallback(
    (end: number) => {
      const clampedEnd = Math.max(
        clipStart + 0.1,
        Math.min(end, videoDuration),
      );
      setClipEnd(clampedEnd);
    },
    [clipStart, videoDuration],
  );

  // Handle format selection
  const handleFormatChange = useCallback(
    (formatId: string | null, resolution: string | null) => {
      setSelectedFormatId(formatId);
      setSelectedResolution(resolution);
    },
    [],
  );

  // Handle clip creation
  const handleClipCreate = useCallback(async () => {
    if (!canCreateClip || !videoMetadata) {
      console.warn("Invalid clip selection or missing data");
      return;
    }

    const jobData = {
      url: sourceUrl,
      in_ts: clipStart,
      out_ts: clipEnd,
      resolution: selectedResolution,
    };

    console.log("Creating job with data:", jobData);
    setPhase("processing");
    setError(null);

    try {
      const jobResponse = await createJobMutation.mutateAsync(jobData);
      setCurrentJobId(jobResponse.id);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to create processing job",
      );
      setPhase("error");
    }
  }, [
    canCreateClip,
    videoMetadata,
    sourceUrl,
    clipStart,
    clipEnd,
    selectedResolution,
    createJobMutation,
  ]);

  // Handle job completion
  const handleJobComplete = useCallback(
    (downloadUrl: string) => {
      setCompletedState({
        downloadUrl,
        videoTitle: videoMetadata?.title || "Video Clip",
      });
      setPhase("completed");
      setCurrentJobId(null);
    },
    [videoMetadata],
  );

  // Handle job error
  const handleJobError = useCallback((errorMessage: string) => {
    setError(errorMessage);
    setPhase("error");
    setCurrentJobId(null);
  }, []);

  // Handle job cancellation
  const handleJobCancel = useCallback(() => {
    setPhase("editing");
    setCurrentJobId(null);
  }, []);

  // Handle starting over
  const handleStartOver = useCallback(() => {
    setPhase("input");
    setVideoUrl("");
    setVideoMetadata(null);
    setCurrentJobId(null);
    setCompletedState(null);
    setError(null);
    setSelectedFormatId(null);
    setSelectedResolution(null);
    setClipStart(0);
    setClipEnd(30);
  }, []);

  useEffect(() => {
    if (createJobMutation.data?.id) {
      setCurrentJobId(createJobMutation.data.id);
    }
  }, [createJobMutation.data]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-orange-50 to-yellow-50">
      {/* Header */}
      <header className="bg-gradient-to-r from-orange-400 to-red-400 text-white p-4 shadow-lg">
        <div className="max-w-6xl mx-auto flex flex-col md:flex-row md:items-center md:justify-between">
          <h1 className="text-3xl tracking-wide md:text-4xl font-bold text-slate-50 mb-2 md:mb-0">
            <Link
              to="/"
              className="flex items-center hover:text-white focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-white"
            >
              <img
                src={logoUrl}
                alt="MemeIt logo"
                className="h-8 w-8 mr-2 flex-shrink-0"
              />
              MemeIt
            </Link>
          </h1>
          <p className="text-orange-100 text-sm md:text-base">
            Clip, Create, Share - Your video moments made viral
          </p>
        </div>
      </header>

      <div className="max-w-6xl mx-auto p-4 space-y-6">
        {/* URL Input Section - Always visible for starting over */}
        {(phase === "input" || phase === "error") && (
          <UrlInput onSubmit={handleUrlSubmit} />
        )}

        {/* Processing Section */}
        {phase === "processing" && (
          <LoadingAnimation
            jobId={currentJobId}
            onComplete={handleJobComplete}
            onError={handleJobError}
            onCancel={handleJobCancel}
          />
        )}

        {/* Completed Section */}
        {phase === "completed" && completedState && (
          <SharingOptions
            downloadUrl={completedState.downloadUrl}
            videoTitle={completedState.videoTitle}
            onStartOver={handleStartOver}
          />
        )}

        {/* Editing Section */}
        {phase === "editing" && videoMetadata && (
          <div className="animate-fade-in-up">
            <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
              {/* Left Column: Player and Timeline */}
              <div className="space-y-6">
                <div className="bg-white rounded-3xl shadow-xl overflow-hidden border border-orange-100">
                  <VideoPlayer
                    videoUrl={videoUrl}
                    metadata={videoMetadata}
                    onDurationChange={handleVideoDurationChange}
                  />
                </div>
                <div className="bg-white rounded-3xl shadow-xl p-6 border border-orange-100">
                  <Timeline
                    duration={videoDuration}
                    clipStart={clipStart}
                    clipEnd={clipEnd}
                    onClipStartChange={handleClipStartChange}
                    onClipEndChange={handleClipEndChange}
                  />
                </div>
              </div>

              {/* Right Column: Resolution and Actions */}
              <div className="space-y-6">
                <div className="bg-white rounded-3xl shadow-xl p-6 border border-orange-100">
                  <ResolutionSelector
                    formats={videoMetadata.formats}
                    onFormatChange={handleFormatChange}
                  />
                </div>
                <div className="bg-white rounded-3xl shadow-xl p-6 border border-orange-100">
                  <div className="flex flex-col space-y-4">
                    <Button
                      onClick={handleClipCreate}
                      disabled={!canCreateClip}
                      size="lg"
                      className="w-full bg-gradient-to-r from-green-400 to-blue-500 hover:from-green-500 hover:to-blue-600 text-white font-bold py-4 px-8 rounded-2xl shadow-lg hover:shadow-xl transform hover:scale-105 transition-all duration-200 text-lg disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none"
                    >
                      {createJobMutation.isPending
                        ? "Creating Clip..."
                        : "✅ Create Clip"}
                    </Button>
                    <Button
                      onClick={handleStartOver}
                      variant="outline"
                      size="lg"
                    >
                      Restart
                    </Button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default Index;
