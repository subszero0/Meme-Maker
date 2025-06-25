import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  metadataApi,
  jobsApi,
  healthApi,
  clipsApi,
  JobStatus,
} from "../lib/api";
import type {
  MetadataResponse,
  VideoMetadata,
  JobCreate,
  JobResponse,
  HealthResponse,
} from "../lib/api";

// ===========================
// Query Keys Factory
// ===========================

export const queryKeys = {
  // Metadata queries
  basicMetadata: (url: string) => ["metadata", "basic", url] as const,
  detailedMetadata: (url: string) => ["metadata", "detailed", url] as const,

  // Job queries
  job: (jobId: string) => ["jobs", jobId] as const,
  allJobs: () => ["jobs"] as const,

  // Health queries
  health: () => ["health"] as const,
} as const;

// ===========================
// Metadata Hooks
// ===========================

/**
 * Hook to fetch basic video metadata (title, duration, thumbnail, resolutions)
 */
export function useBasicVideoMetadata(url: string, enabled = true) {
  return useQuery({
    queryKey: queryKeys.basicMetadata(url),
    queryFn: () => metadataApi.getBasicMetadata(url),
    enabled: enabled && !!url,
    staleTime: 5 * 60 * 1000, // 5 minutes - metadata rarely changes
    retry: 2,
  });
}

/**
 * Hook to fetch detailed video metadata with available formats
 */
export function useDetailedVideoMetadata(url: string, enabled = true) {
  return useQuery({
    queryKey: queryKeys.detailedMetadata(url),
    queryFn: () => metadataApi.getDetailedMetadata(url),
    enabled: enabled && !!url,
    staleTime: 10 * 60 * 1000, // 10 minutes - metadata rarely changes
    retry: 2,
  });
}

/**
 * Alias for useBasicVideoMetadata for backward compatibility
 */
export const useVideoMetadata = useBasicVideoMetadata;

// ===========================
// Job Management Hooks
// ===========================

/**
 * Hook to create a new video clipping job
 */
export function useCreateJob() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (jobData: JobCreate): Promise<JobResponse> => {
      console.log("🎬 useCreateJob: Creating job with data:", jobData);
      const response = await jobsApi.createJob(jobData);
      console.log("🎬 useCreateJob: Job created with ID:", response.id);
      return response;
    },
    onSuccess: (jobResponse) => {
      // Cache the job data immediately
      queryClient.setQueryData(queryKeys.job(jobResponse.id), jobResponse);

      // Invalidate all jobs query if it exists
      queryClient.invalidateQueries({ queryKey: queryKeys.allJobs() });
    },
    onError: (error) => {
      console.error("🎬 useCreateJob: Failed to create job:", error);
    },
  });
}

/**
 * Hook to get job status with manual refresh
 */
export function useJobStatus(
  jobId: string,
  options?: {
    enabled?: boolean;
  },
) {
  const { enabled = true } = options || {};

  return useQuery({
    queryKey: queryKeys.job(jobId),
    queryFn: () => jobsApi.getJob(jobId),
    enabled: enabled && !!jobId,
    staleTime: 0, // Always consider job data stale for real-time updates
    refetchOnWindowFocus: false, // Prevent unnecessary refetches
  });
}

/**
 * Hook for polling job status with automatic updates
 */
export function useJobStatusWithPolling(
  jobId: string,
  options?: {
    enabled?: boolean;
    pollingInterval?: number;
  },
) {
  const {
    enabled = true,
    pollingInterval = parseInt(import.meta.env.VITE_POLLING_INTERVAL || "2000"),
  } = options || {};

  return useQuery({
    queryKey: queryKeys.job(jobId),
    queryFn: async () => {
      console.log("🔄 Polling job status for:", jobId);
      const response = await jobsApi.getJob(jobId);
      console.log(
        "🔄 Job status:",
        response.status,
        "Progress:",
        response.progress,
      );
      return response;
    },
    enabled: enabled && !!jobId,
    refetchInterval: (query) => {
      // Only poll if job is still in progress
      const data = query.state.data;
      if (
        data?.status === JobStatus.QUEUED ||
        data?.status === JobStatus.WORKING
      ) {
        return pollingInterval;
      }
      // Stop polling when job is done or errored
      return false;
    },
    refetchIntervalInBackground: false, // Stop polling when tab is not active
    staleTime: 0, // Always consider job data stale for real-time updates
    refetchOnWindowFocus: false,
  });
}

/**
 * Hook for manual job status refresh
 */
export function useRefreshJobStatus() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (jobId: string) => {
      const data = await jobsApi.getJob(jobId);
      queryClient.setQueryData(queryKeys.job(jobId), data);
      return data;
    },
  });
}

/**
 * Hook to cancel a job (if the backend supports it)
 */
export function useCancelJob() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (jobId: string) => {
      // TODO: Implement cancel endpoint when backend supports it
      // For now, just simulate cancellation
      console.log("🛑 Cancel requested for job:", jobId);
      throw new Error("Job cancellation not implemented in backend");
    },
    onSuccess: (data, jobId) => {
      // Update job status to indicate cancellation
      queryClient.setQueryData(
        queryKeys.job(jobId),
        (oldData: JobResponse | undefined) => {
          if (oldData) {
            return {
              ...oldData,
              status: JobStatus.ERROR,
              error_code: "CANCELLED",
            };
          }
          return oldData;
        },
      );
    },
  });
}

// ===========================
// Clips Hooks
// ===========================

/**
 * Hook to delete a clip after download
 */
export function useDeleteClip() {
  return useMutation({
    mutationFn: (jobId: string) => clipsApi.deleteClip(jobId),
  });
}

// ===========================
// Health Check Hook
// ===========================

/**
 * Hook to check API health status
 */
export function useHealthCheck(enabled = true) {
  return useQuery({
    queryKey: queryKeys.health(),
    queryFn: () => healthApi.checkHealth(),
    enabled,
    staleTime: 30 * 1000, // 30 seconds
    refetchInterval: 60 * 1000, // Check every minute
  });
}

// ===========================
// Utility Hooks
// ===========================

/**
 * Hook to invalidate specific queries
 */
export function useInvalidateQueries() {
  const queryClient = useQueryClient();

  return {
    invalidateMetadata: (url: string) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.basicMetadata(url) });
      queryClient.invalidateQueries({
        queryKey: queryKeys.detailedMetadata(url),
      });
    },
    invalidateJob: (jobId: string) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.job(jobId) });
    },
    invalidateAllJobs: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.allJobs() });
    },
    invalidateHealth: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.health() });
    },
  };
}

/**
 * Hook to clear all cached data
 */
export function useClearCache() {
  const queryClient = useQueryClient();

  return () => {
    queryClient.clear();
  };
}
