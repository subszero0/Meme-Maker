// Dynamic API base URL with proper environment detection
const getApiBaseUrl = (): string => {
  // In browser environment
  if (typeof window !== "undefined") {
    // Production: Use relative URLs (same domain as frontend)
    if (window.location.hostname !== "localhost") {
      console.log(
        `[API] Production environment detected. Using relative URLs for domain: ${window.location.hostname}`,
      );
      return ""; // Empty string means relative URLs
    }
    // Development: Use localhost with port
    console.log("[API] Development environment detected. Using localhost:8000");
    return "http://localhost:8000";
  }

  // Server-side rendering fallback
  const envUrl = process.env.NEXT_PUBLIC_API_URL;
  if (envUrl) {
    console.log(`[API] Using environment variable API URL: ${envUrl}`);
    return envUrl;
  }

  // Default fallback for SSR
  console.log("[API] Using default localhost URL for SSR");
  return "http://localhost:8000";
};

const BASE_URL = getApiBaseUrl();

export interface VideoMetadata {
  url: string;
  title: string;
  duration: number; // in seconds
}

export interface JobRequest {
  url: string;
  start: string; // Time in mm:ss format
  end: string; // Time in mm:ss format
  accepted_terms: boolean;
}

export interface JobResponse {
  jobId: string;
}

export interface JobStatus {
  status: "queued" | "working" | "done" | "error";
  progress?: number;
  url?: string;
  errorCode?: string;
  errorMessage?: string;
}

export interface RateLimitError extends Error {
  isRateLimitError: true;
  limitType: "global" | "job_creation";
  retryAfter: number;
}

export class RateLimitErrorClass extends Error implements RateLimitError {
  isRateLimitError = true as const;
  limitType: "global" | "job_creation";
  retryAfter: number;

  constructor(
    message: string,
    limitType: "global" | "job_creation",
    retryAfter: number,
  ) {
    super(message);
    this.name = "RateLimitError";
    this.limitType = limitType;
    this.retryAfter = retryAfter;
  }
}

/**
 * Handle API errors, specifically rate limiting
 */
async function handleApiError(response: Response): Promise<never> {
  if (response.status === 429) {
    const data = await response.json().catch(() => ({}));
    throw new RateLimitErrorClass(
      data.detail || "Rate limit exceeded",
      data.limit_type || "global",
      data.retry_after || 60,
    );
  }

  // For other errors, throw a generic error
  const errorText = await response.text().catch(() => "Unknown error");
  throw new Error(`API Error ${response.status}: ${errorText}`);
}

export async function fetchVideoMetadata(url: string): Promise<VideoMetadata> {
  const apiUrl = `${BASE_URL}/api/v1/metadata`;
  console.log(`[API] Fetching metadata from: ${apiUrl}`);
  console.log(`[API] Request payload:`, { url });

  try {
    const response = await fetch(apiUrl, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ url }),
    });

    console.log(
      `[API] Response status: ${response.status} ${response.statusText}`,
    );
    console.log(
      `[API] Response headers:`,
      Object.fromEntries(response.headers.entries()),
    );

    if (!response.ok) {
      return handleApiError(response);
    }

    const data = await response.json();
    console.log(`[API] Metadata response:`, data);
    return data;
  } catch (error) {
    console.error(`[API] Network error fetching metadata:`, error);
    console.error(`[API] Request URL was: ${apiUrl}`);
    throw error;
  }
}

export async function createJob(request: JobRequest): Promise<JobResponse> {
  const apiUrl = `${BASE_URL}/api/v1/jobs`;
  console.log(`[API] Creating job at: ${apiUrl}`);
  console.log(`[API] Job request:`, request);

  try {
    const response = await fetch(apiUrl, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(request),
    });

    console.log(
      `[API] Job creation response status: ${response.status} ${response.statusText}`,
    );

    if (!response.ok) {
      return handleApiError(response);
    }

    const data = await response.json();
    console.log(`[API] Job created:`, data);
    return data;
  } catch (error) {
    console.error(`[API] Network error creating job:`, error);
    console.error(`[API] Request URL was: ${apiUrl}`);
    throw error;
  }
}

export async function getJobStatus(jobId: string): Promise<JobStatus> {
  const response = await fetch(`${BASE_URL}/api/v1/jobs/${jobId}`, {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
    },
  });

  if (!response.ok) {
    return handleApiError(response);
  }

  return response.json();
}

/**
 * Check if an error is a rate limit error
 */
export function isRateLimitError(error: unknown): error is RateLimitErrorClass {
  return (
    error !== null &&
    typeof error === "object" &&
    "isRateLimitError" in error &&
    error.isRateLimitError === true
  );
}

/**
 * Format retry time as human-readable string
 */
export function formatRetryTime(seconds: number): string {
  if (seconds < 60) {
    return `${seconds} second${seconds !== 1 ? "s" : ""}`;
  }

  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = seconds % 60;

  if (remainingSeconds === 0) {
    return `${minutes} minute${minutes !== 1 ? "s" : ""}`;
  }

  return `${minutes}m ${remainingSeconds}s`;
}
