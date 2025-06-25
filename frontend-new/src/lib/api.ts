import axios, { AxiosResponse, AxiosError } from "axios";
import { config } from "../config/environment";

// ===========================
// Configuration
// ===========================

const API_BASE_URL = config.API_BASE_URL;
const API_TIMEOUT = parseInt(import.meta.env.VITE_API_TIMEOUT || "30000");

// Create axios instance with default configuration
export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: API_TIMEOUT,
  headers: {
    "Content-Type": "application/json",
    Accept: "application/json",
  },
});

// Add request interceptor for mobile compatibility
apiClient.interceptors.request.use(
  (config) => {
    // Add mobile-specific headers if on mobile device
    const isMobile =
      /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(
        navigator.userAgent,
      );

    if (isMobile) {
      // Increase timeout for mobile networks
      config.timeout = Math.max(config.timeout || 30000, 45000);
    }

    return config;
  },
  (error) => {
    return Promise.reject(error);
  },
);

// Add response interceptor for better error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.code === "ECONNABORTED") {
      console.error(
        "Request timeout - this may be due to slow network connection",
      );
    }
    return Promise.reject(error);
  },
);

// ===========================
// TypeScript Interfaces
// ===========================

// Job Status Enum
export enum JobStatus {
  QUEUED = "queued",
  WORKING = "working",
  DONE = "done",
  ERROR = "error",
}

// Video Format Interface
export interface VideoFormat {
  format_id: string;
  ext: string;
  resolution: string;
  filesize?: number;
  fps?: number;
  vcodec: string;
  acodec: string;
  format_note: string;
}

// Metadata Interfaces
export interface MetadataRequest {
  url: string;
}

export interface MetadataResponse {
  title: string;
  duration: number;
  thumbnail_url?: string;
  resolutions: string[];
}

export interface VideoMetadata {
  title: string;
  duration: number;
  thumbnail: string;
  uploader: string;
  upload_date: string;
  view_count: number;
  formats: VideoFormat[];
}

// Job Interfaces
export interface JobCreate {
  url: string;
  in_ts: number;
  out_ts: number;
  format_id?: string;
}

export interface JobResponse {
  id: string;
  status: JobStatus;
  created_at: string;
  progress?: number;
  download_url?: string;
  error_code?: string;
  stage?: string;
  format_id?: string;
  video_title?: string;
}

// Health Check Interface
export interface HealthResponse {
  status: string;
}

// ===========================
// Error Handling
// ===========================

export interface ApiError {
  message: string;
  status?: number;
  code?: string;
}

export class ApiException extends Error {
  status?: number;
  code?: string;

  constructor(message: string, status?: number, code?: string) {
    super(message);
    this.name = "ApiException";
    this.status = status;
    this.code = code;
  }
}

// Global error handler for axios responses
function handleApiError(error: AxiosError): never {
  if (error.response) {
    // Server responded with error status
    const status = error.response.status;
    const data = error.response.data as {
      detail?: string;
      message?: string;
      code?: string;
    };
    const message = data?.detail || data?.message || error.message;

    throw new ApiException(message, status, data?.code);
  } else if (error.request) {
    // Request was made but no response received
    throw new ApiException(
      "Network error: Unable to connect to server",
      0,
      "NETWORK_ERROR",
    );
  } else {
    // Something else happened
    throw new ApiException(error.message, 0, "UNKNOWN_ERROR");
  }
}

// ===========================
// API Functions
// ===========================

// Metadata API
export const metadataApi = {
  /**
   * Get basic video metadata (title, duration, thumbnail, resolutions)
   */
  async getBasicMetadata(url: string): Promise<MetadataResponse> {
    try {
      console.log("🔍 Fetching basic metadata for:", url);
      const response: AxiosResponse<MetadataResponse> = await apiClient.post(
        "/api/v1/metadata",
        {
          url,
        },
      );
      console.log("✅ Basic metadata received:", response.data);
      return response.data;
    } catch (error) {
      console.error("❌ Basic metadata failed:", error);
      handleApiError(error as AxiosError);
    }
  },

  /**
   * Get detailed video metadata with available formats
   */
  async getDetailedMetadata(url: string): Promise<VideoMetadata> {
    try {
      console.log("🔍 Fetching detailed metadata for:", url);
      const response: AxiosResponse<VideoMetadata> = await apiClient.post(
        "/api/v1/metadata/extract",
        {
          url,
        },
      );
      console.log(
        `✅ Detailed metadata received: ${response.data.formats.length} formats`,
      );
      return response.data;
    } catch (error) {
      console.error("❌ Detailed metadata failed:", error);
      handleApiError(error as AxiosError);
    }
  },
};

// Jobs API
export const jobsApi = {
  /**
   * Create a new video clipping job
   */
  async createJob(jobData: JobCreate): Promise<JobResponse> {
    try {
      const response: AxiosResponse<JobResponse> = await apiClient.post(
        "/api/v1/jobs",
        jobData,
      );
      return response.data;
    } catch (error) {
      handleApiError(error as AxiosError);
    }
  },

  /**
   * Get job status and details
   */
  async getJob(jobId: string): Promise<JobResponse> {
    try {
      const response: AxiosResponse<JobResponse> = await apiClient.get(
        `/api/v1/jobs/${jobId}`,
      );
      return response.data;
    } catch (error) {
      handleApiError(error as AxiosError);
    }
  },
};

// Clips API
export const clipsApi = {
  /**
   * Download a processed clip
   */
  getDownloadUrl(filename: string): string {
    return `${API_BASE_URL}/api/clips/${filename}`;
  },

  /**
   * Clean up a processed clip
   */
  async deleteClip(jobId: string): Promise<{ message: string }> {
    try {
      const response: AxiosResponse<{ message: string }> =
        await apiClient.delete(`/api/clips/${jobId}.mp4`);
      return response.data;
    } catch (error) {
      handleApiError(error as AxiosError);
    }
  },
};

// Health API
export const healthApi = {
  /**
   * Check API health status
   */
  async checkHealth(): Promise<HealthResponse> {
    try {
      const response: AxiosResponse<HealthResponse> =
        await apiClient.get("/health");
      return response.data;
    } catch (error) {
      handleApiError(error as AxiosError);
    }
  },
};

// ===========================
// Utility Functions
// ===========================

/**
 * Format duration from seconds to HH:MM:SS
 */
export function formatDuration(seconds: number): string {
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const secs = Math.floor(seconds % 60);

  if (hours > 0) {
    return `${hours}:${minutes.toString().padStart(2, "0")}:${secs.toString().padStart(2, "0")}`;
  }
  return `${minutes}:${secs.toString().padStart(2, "0")}`;
}

/**
 * Parse resolution string to get height for sorting
 */
export function parseResolutionHeight(resolution: string): number {
  const match = resolution.match(/(\d+)x(\d+)/);
  return match ? parseInt(match[2]) : 0;
}

/**
 * Format file size from bytes to human readable
 */
export function formatFileSize(bytes?: number): string {
  if (!bytes) return "Unknown size";

  const units = ["B", "KB", "MB", "GB"];
  let size = bytes;
  let unitIndex = 0;

  while (size >= 1024 && unitIndex < units.length - 1) {
    size /= 1024;
    unitIndex++;
  }

  return `${size.toFixed(1)} ${units[unitIndex]}`;
}
