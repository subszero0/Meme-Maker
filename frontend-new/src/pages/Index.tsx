import React, { useState, useCallback, useMemo } from "react";
import { UrlInput } from "@/components/UrlInput";
import { VideoPlayer } from "@/components/VideoPlayer";
import { Timeline } from "@/components/Timeline";
import { ResolutionSelector } from "@/components/ResolutionSelector";
import { SharingOptions } from "@/components/SharingOptions";
import { LoadingAnimation } from "@/components/LoadingAnimation";
import { MetadataResponse } from "@/lib/api";
import { useCreateJob } from "@/hooks/useApi";

// Application phases
type AppPhase = "input" | "editing" | "processing" | "completed" | "error";

interface CompletedState {
  downloadUrl: string;
  videoTitle: string;
}

const Index = () => {
  // Application state
  const [phase, setPhase] = useState<AppPhase>("input");
  const [error, setError] = useState<string | null>(null);

  // Video and metadata state
  const [videoUrl, setVideoUrl] = useState("");
  const [videoMetadata, setVideoMetadata] = useState<MetadataResponse | null>(
    null,
  );

  // Job processing state
  const [currentJobId, setCurrentJobId] = useState<string | null>(null);
  const [completedState, setCompletedState] = useState<CompletedState | null>(
    null,
  );

  // Clip selection state
  const [clipStart, setClipStart] = useState(0);
  const [clipEnd, setClipEnd] = useState(30);

  // Format selection state
  const [selectedFormatId, setSelectedFormatId] = useState<string | undefined>(
    undefined,
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
    (url: string, metadata: MetadataResponse) => {
      console.log("🎬 New video loaded:", metadata.title);
      setVideoUrl(url);
      setVideoMetadata(metadata);
      setPhase("editing");
      setError(null);

      // Reset all other states
      setCurrentJobId(null);
      setCompletedState(null);
      setSelectedFormatId(undefined);

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
  const handleFormatChange = useCallback((formatId: string | undefined) => {
    console.log("🎬 Format changed to:", formatId);
    setSelectedFormatId(formatId);
  }, []);

  // Handle clip creation
  const handleClipCreate = useCallback(async () => {
    if (!canCreateClip || !videoMetadata) {
      console.warn("Invalid clip selection or missing data");
      return;
    }

    const jobData = {
      url: videoUrl,
      in_ts: clipStart,
      out_ts: clipEnd,
      format_id: selectedFormatId!,
    };

    console.log("🎬 Creating job with data:", jobData);
    setPhase("processing");
    setError(null);

    try {
      const jobResponse = await createJobMutation.mutateAsync(jobData);
      setCurrentJobId(jobResponse.id);
      console.log("🎬 Job created successfully:", jobResponse.id);
    } catch (err) {
      console.error("🎬 Failed to create job:", err);
      setError(
        err instanceof Error ? err.message : "Failed to create processing job",
      );
      setPhase("error");
    }
  }, [
    canCreateClip,
    videoMetadata,
    videoUrl,
    clipStart,
    clipEnd,
    selectedFormatId,
    createJobMutation,
  ]);

  // Handle job completion
  const handleJobComplete = useCallback(
    (downloadUrl: string) => {
      console.log("🎉 Job completed with download URL:", downloadUrl);
      setCompletedState({
        downloadUrl,
        videoTitle: videoMetadata?.title || "Video Clip",
      });
      setPhase("completed");
      setCurrentJobId(null);
    },
    [videoMetadata?.title],
  );

  // Handle job error
  const handleJobError = useCallback((errorMessage: string) => {
    console.error("❌ Job failed:", errorMessage);
    setError(errorMessage);
    setPhase("error");
    setCurrentJobId(null);
  }, []);

  // Handle job cancellation
  const handleJobCancel = useCallback(() => {
    console.log("🛑 Job cancelled by user");
    setPhase("editing");
    setCurrentJobId(null);
  }, []);

  // Handle starting over
  const handleStartOver = useCallback(() => {
    console.log("🔄 Starting over");
    setPhase("input");
    setVideoUrl("");
    setVideoMetadata(null);
    setCurrentJobId(null);
    setCompletedState(null);
    setError(null);
    setSelectedFormatId(undefined);
    setClipStart(0);
    setClipEnd(30);
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-br from-orange-50 to-yellow-50">
      {/* Header */}
      <header className="bg-gradient-to-r from-orange-400 to-red-400 text-white p-4 shadow-lg">
        <div className="max-w-6xl mx-auto flex flex-col md:flex-row md:items-center md:justify-between">
          <h1 className="text-3xl tracking-wide md:text-4xl font-bold text-slate-50 mb-2 md:mb-0">
            MemeIT
          </h1>
          <p className="text-orange-100 text-sm md:text-base">
            Clip, Create, Share - Your video moments made viral
          </p>
        </div>
      </header>

      <div className="max-w-6xl mx-auto p-4 space-y-6">
        {/* URL Input Section - Always visible for starting over */}
        {(phase === "input" || phase === "error") && (
          <div className="bg-white rounded-3xl shadow-xl p-6 border border-orange-100">
            <UrlInput onSubmit={handleUrlSubmit} />

            {/* Error Display */}
            {phase === "error" && error && (
              <div className="mt-6 p-4 bg-red-50 border border-red-200 rounded-2xl">
                <div className="flex items-start space-x-3">
                  <div className="w-5 h-5 text-red-500 mt-0.5">⚠️</div>
                  <div>
                    <h4 className="font-medium text-red-800">
                      Processing Failed
                    </h4>
                    <p className="text-red-600 text-sm mt-1">{error}</p>
                    <button
                      onClick={handleStartOver}
                      className="mt-3 text-red-600 hover:text-red-800 text-sm underline"
                    >
                      Try again with a different video
                    </button>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Video Editing Interface */}
        {phase === "editing" && videoMetadata && (
          <>
            {/* Start Over Button */}
            <div className="flex justify-between items-center">
              <button
                onClick={handleStartOver}
                className="text-gray-600 hover:text-gray-800 text-sm flex items-center space-x-1"
              >
                <span>←</span>
                <span>Load different video</span>
              </button>
            </div>

            {/* Video Player Section */}
            <div className="bg-white rounded-3xl shadow-xl overflow-hidden border border-orange-100">
              <VideoPlayer
                videoUrl={videoUrl}
                metadata={videoMetadata}
                onDurationChange={handleVideoDurationChange}
              />
            </div>

            {/* Timeline Section */}
            <div className="bg-white rounded-3xl shadow-xl p-6 border border-orange-100">
              <Timeline
                duration={videoDuration}
                clipStart={clipStart}
                clipEnd={clipEnd}
                onClipStartChange={handleClipStartChange}
                onClipEndChange={handleClipEndChange}
              />
            </div>

            {/* Controls Section */}
            <div className="grid md:grid-cols-2 gap-6">
              {/* Resolution Selector */}
              <div className="bg-white rounded-3xl shadow-xl p-6 border border-orange-100">
                <ResolutionSelector
                  videoUrl={videoUrl}
                  selectedFormatId={selectedFormatId}
                  onFormatChange={handleFormatChange}
                />
              </div>

              {/* Create Clip Button */}
              <div className="bg-white rounded-3xl shadow-xl p-6 border border-orange-100 flex flex-col items-center justify-center space-y-3">
                <button
                  onClick={handleClipCreate}
                  disabled={!canCreateClip}
                  className={`w-full font-bold py-4 px-8 rounded-2xl shadow-lg transition-all duration-200 text-lg ${
                    canCreateClip
                      ? "bg-gradient-to-r from-orange-400 to-red-400 text-white hover:shadow-xl transform hover:scale-105"
                      : "bg-gray-300 text-gray-500 cursor-not-allowed"
                  }`}
                >
                  {createJobMutation.isPending
                    ? "🎬 Creating Job..."
                    : "🎬 Create Clip"}
                </button>

                {/* Validation feedback */}
                {!canCreateClip && (
                  <div className="text-center text-sm space-y-1">
                    {!videoMetadata && (
                      <p className="text-gray-600">Load a video to start</p>
                    )}
                    {videoMetadata && !clipValidation.isValid && (
                      <>
                        {clipValidation.invalidRange && (
                          <p className="text-red-600">
                            End time must be after start time
                          </p>
                        )}
                        {clipValidation.exceedsMaxDuration && (
                          <p className="text-red-600">
                            Clip duration cannot exceed 3 minutes
                          </p>
                        )}
                      </>
                    )}
                    {videoMetadata &&
                      clipValidation.isValid &&
                      !selectedFormatId && (
                        <p className="text-yellow-600">
                          Select a video quality
                        </p>
                      )}
                  </div>
                )}

                {canCreateClip && (
                  <div className="text-center text-sm space-y-1">
                    <p className="text-green-600 font-medium">
                      ✓ Ready to create clip
                    </p>
                    <p className="text-xs text-gray-500">
                      {clipValidation.duration.toFixed(1)}s clip • Format:{" "}
                      {selectedFormatId}
                    </p>
                  </div>
                )}
              </div>
            </div>
          </>
        )}

        {/* Processing Animation */}
        {phase === "processing" && currentJobId && (
          <div className="bg-white rounded-3xl shadow-xl p-6 border border-orange-100">
            <LoadingAnimation
              jobId={currentJobId}
              onComplete={handleJobComplete}
              onError={handleJobError}
              onCancel={handleJobCancel}
            />
          </div>
        )}

        {/* Completion and Download */}
        {phase === "completed" && completedState && (
          <div className="bg-white rounded-3xl shadow-xl p-6 border border-orange-100">
            <SharingOptions
              downloadUrl={completedState.downloadUrl}
              videoTitle={completedState.videoTitle}
              onStartOver={handleStartOver}
            />
          </div>
        )}
      </div>
    </div>
  );
};

export default Index;
