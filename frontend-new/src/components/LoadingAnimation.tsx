import React, { useMemo } from "react";
import {
  Scissors,
  Zap,
  Download,
  X,
  AlertCircle,
  CheckCircle,
  Clock,
} from "lucide-react";
import { useJobStatusWithPolling, useCancelJob } from "@/hooks/useApi";
import { JobStatus } from "@/types/job";

interface LoadingAnimationProps {
  jobId: string | null;
  onComplete?: (downloadUrl: string) => void;
  onError?: (error: string) => void;
  onCancel?: () => void;
}

export const LoadingAnimation: React.FC<LoadingAnimationProps> = ({
  jobId,
  onComplete,
  onError,
  onCancel,
}) => {
  // Poll job status (always call hooks)
  const {
    data: jobData,
    error: jobError,
    isLoading,
  } = useJobStatusWithPolling(jobId, {
    enabled: !!jobId,
    pollingInterval: 2000,
  });

  // Cancel job mutation
  const cancelJobMutation = useCancelJob();

  // Process job data and determine current state
  const jobState = useMemo(() => {
    if (isLoading || !jobData) {
      return {
        status: JobStatus.QUEUED,
        progress: 0,
        stage: "Initializing...",
        canCancel: true,
      };
    }

    const progress = jobData.progress || 0;
    const status = jobData.status;
    const stage = jobData.stage || getDefaultStageText(status, progress);
    const canCancel =
      status === JobStatus.QUEUED || status === JobStatus.WORKING;

    return { status, progress, stage, canCancel };
  }, [jobData, isLoading]);

  // Handle job completion
  React.useEffect(() => {
    if (jobData?.status === JobStatus.DONE && jobData.download_url) {
      console.log("🎉 Job completed successfully:", jobData.download_url);
      onComplete?.(jobData.download_url);
    } else if (jobData?.status === JobStatus.ERROR) {
      const errorMessage =
        jobData.error_code === "QUEUE_FULL"
          ? "Server is too busy right now. Please try again in a few minutes."
          : `Processing failed: ${jobData.error_code || "Unknown error"}`;
      console.error("❌ Job failed:", errorMessage);
      onError?.(errorMessage);
    }
  }, [jobData, onComplete, onError]);

  // Handle job polling errors
  React.useEffect(() => {
    if (jobError) {
      console.error("❌ Job polling error:", jobError);
      onError?.("Failed to track job progress. Please refresh the page.");
    }
  }, [jobError, onError]);

  // Handle cancel button click
  const handleCancel = () => {
    if (jobState.canCancel) {
      console.log("🛑 User requested job cancellation");
      onCancel?.();
      // Note: Backend cancellation not implemented yet
      // cancelJobMutation.mutate(jobId);
    }
  };

  // Define processing steps with dynamic progress ranges
  const steps = useMemo(
    () => [
      {
        icon: Clock,
        text: "Queued for processing...",
        color: "text-blue-500",
        progressRange: [0, 5],
        status: [JobStatus.QUEUED],
      },
      {
        icon: Scissors,
        text: "Analyzing video content...",
        color: "text-orange-500",
        progressRange: [5, 35],
        status: [JobStatus.WORKING],
      },
      {
        icon: Zap,
        text: "Processing your clip...",
        color: "text-red-500",
        progressRange: [35, 85],
        status: [JobStatus.WORKING],
      },
      {
        icon: Download,
        text: "Preparing for download...",
        color: "text-green-500",
        progressRange: [85, 100],
        status: [JobStatus.WORKING, JobStatus.DONE],
      },
    ],
    [],
  );

  // Determine current step based on progress and status
  const currentStep = useMemo(() => {
    const progress = jobState.progress;
    const status = jobState.status;

    if (status === JobStatus.QUEUED) return 0;
    if (status === JobStatus.ERROR) return -1;
    if (status === JobStatus.DONE) return steps.length - 1;

    // Find step based on progress range
    for (let i = 0; i < steps.length; i++) {
      const [min, max] = steps[i].progressRange;
      if (progress >= min && progress <= max) {
        return i;
      }
    }

    return Math.min(
      Math.floor((progress / 100) * steps.length),
      steps.length - 1,
    );
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [jobState.progress, jobState.status]);

  // Handle null jobId case
  if (!jobId) {
    return (
      <div className="text-center space-y-6">
        <div className="flex items-center justify-center w-32 h-32 mx-auto">
          <div className="w-24 h-24 bg-gray-100 rounded-full flex items-center justify-center">
            <Clock className="w-12 h-12 text-gray-500" />
          </div>
        </div>
        <div>
          <h3 className="text-2xl font-bold text-gray-800 mb-2">
            Initializing...
          </h3>
          <p className="text-gray-600">Setting up your processing job</p>
        </div>
      </div>
    );
  }

  // Error state
  if (jobState.status === JobStatus.ERROR) {
    return (
      <div className="text-center space-y-6">
        <div className="flex items-center justify-center w-32 h-32 mx-auto">
          <div className="w-24 h-24 bg-red-100 rounded-full flex items-center justify-center">
            <AlertCircle className="w-12 h-12 text-red-500" />
          </div>
        </div>

        <div>
          <h3 className="text-2xl font-bold text-gray-800 mb-2">
            Processing Failed
          </h3>
          <p className="text-gray-600">{jobState.stage}</p>
        </div>

        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-600 text-sm">
            {jobData?.error_code === "QUEUE_FULL"
              ? "🚦 The server is experiencing high traffic. Please try again in a few minutes."
              : "⚠️ Something went wrong during processing. Please try again with a different video or contact support."}
          </p>
        </div>
      </div>
    );
  }

  // Success state
  if (jobState.status === JobStatus.DONE) {
    return (
      <div className="text-center space-y-6">
        <div className="flex items-center justify-center w-32 h-32 mx-auto">
          <div className="w-24 h-24 bg-green-100 rounded-full flex items-center justify-center">
            <CheckCircle className="w-12 h-12 text-green-500" />
          </div>
        </div>

        <div>
          <h3 className="text-2xl font-bold text-gray-800 mb-2">
            Your Clip is Ready! 🎉
          </h3>
          <p className="text-gray-600">Download will start automatically</p>
        </div>

        <div className="bg-green-50 border border-green-200 rounded-lg p-4">
          <p className="text-green-600 text-sm">
            ✅ Processing completed successfully! Your video clip has been
            generated and is ready for download.
          </p>
        </div>
      </div>
    );
  }

  // Processing state
  return (
    <div className="text-center space-y-8">
      <div>
        <h3 className="text-2xl font-bold text-gray-800 mb-2">
          Creating Your Masterpiece
        </h3>
        <p className="text-gray-600">
          Hang tight while we process your video ✨
        </p>
      </div>

      {/* Animated Progress Circle */}
      <div className="relative w-32 h-32 mx-auto">
        <svg className="w-32 h-32 transform -rotate-90" viewBox="0 0 120 120">
          {/* Background circle */}
          <circle
            cx="60"
            cy="60"
            r="50"
            fill="none"
            stroke="#f3f4f6"
            strokeWidth="8"
          />
          {/* Progress circle */}
          <circle
            cx="60"
            cy="60"
            r="50"
            fill="none"
            stroke="url(#gradient)"
            strokeWidth="8"
            strokeLinecap="round"
            strokeDasharray={`${2 * Math.PI * 50}`}
            strokeDashoffset={`${2 * Math.PI * 50 * (1 - jobState.progress / 100)}`}
            className="transition-all duration-500 ease-out"
          />
          <defs>
            <linearGradient id="gradient" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#fb923c" />
              <stop offset="100%" stopColor="#ef4444" />
            </linearGradient>
          </defs>
        </svg>

        {/* Percentage in center */}
        <div className="absolute inset-0 flex items-center justify-center">
          <span className="text-2xl font-bold text-gray-800">
            {Math.round(jobState.progress)}%
          </span>
        </div>
      </div>

      {/* Current Status */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <p className="text-blue-700 font-medium">{jobState.stage}</p>
        <p className="text-blue-600 text-sm mt-1">
          Job ID: {jobId ? jobId.slice(0, 8) : "Unknown"}...
        </p>
      </div>

      {/* Current Step Display */}
      <div className="space-y-4">
        {steps.map((step, index) => {
          const StepIcon = step.icon;
          const isActive = index === currentStep;
          const isCompleted = index < currentStep;
          const isPending = index > currentStep;

          return (
            <div
              key={index}
              className={`flex items-center justify-center space-x-3 p-4 rounded-2xl transition-all duration-500 ${
                isActive
                  ? "bg-gradient-to-r from-orange-50 to-red-50 border-2 border-orange-200 scale-105"
                  : isCompleted
                    ? "bg-green-50 border-2 border-green-200"
                    : "bg-gray-50 border-2 border-gray-200"
              }`}
            >
              <div
                className={`p-2 rounded-full transition-all duration-300 ${
                  isActive
                    ? "bg-gradient-to-r from-orange-400 to-red-400 text-white animate-pulse"
                    : isCompleted
                      ? "bg-green-400 text-white"
                      : "bg-gray-300 text-gray-500"
                }`}
              >
                <StepIcon className="w-5 h-5" />
              </div>
              <span
                className={`font-medium transition-colors duration-300 ${
                  isActive
                    ? "text-gray-800"
                    : isCompleted
                      ? "text-green-700"
                      : "text-gray-500"
                }`}
              >
                {step.text}
              </span>
              {isCompleted && (
                <div className="w-2 h-2 bg-green-400 rounded-full animate-ping" />
              )}
              {isPending && (
                <div className="w-2 h-2 bg-gray-300 rounded-full" />
              )}
            </div>
          );
        })}
      </div>

      {/* Cancel Button */}
      {jobState.canCancel && (
        <div className="flex justify-center">
          <button
            onClick={handleCancel}
            disabled={cancelJobMutation.isPending}
            className="flex items-center space-x-2 px-4 py-2 text-gray-600 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors duration-200 disabled:opacity-50"
          >
            <X className="w-4 h-4" />
            <span className="text-sm">
              {cancelJobMutation.isPending
                ? "Cancelling..."
                : "Cancel Processing"}
            </span>
          </button>
        </div>
      )}

      {/* Fun Facts */}
      <div className="text-sm text-gray-500">
        <p>💡 Pro tip: Shorter clips get more engagement on social media!</p>
      </div>

      {/* Geometric Pattern Animation */}
      <div className="flex justify-center space-x-2">
        {[...Array(5)].map((_, i) => (
          <div
            key={i}
            className="w-3 h-3 bg-gradient-to-r from-orange-400 to-red-400 rounded-full animate-bounce"
            style={{ animationDelay: `${i * 0.1}s` }}
          />
        ))}
      </div>
    </div>
  );
};

// Helper function to provide default stage text based on status and progress
function getDefaultStageText(status: JobStatus, progress: number): string {
  if (status === JobStatus.QUEUED) {
    return "Waiting in queue...";
  }

  if (status === JobStatus.WORKING) {
    if (progress < 10) return "Starting video analysis...";
    if (progress < 30) return "Extracting video metadata...";
    if (progress < 60) return "Processing video clip...";
    if (progress < 85) return "Encoding video...";
    if (progress < 95) return "Finalizing output...";
    return "Almost done...";
  }

  if (status === JobStatus.DONE) {
    return "Processing complete!";
  }

  if (status === JobStatus.ERROR) {
    return "Processing failed";
  }

  return "Processing...";
}
