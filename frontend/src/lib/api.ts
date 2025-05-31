const BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface VideoMetadata {
  url: string;
  title: string;
  duration: number; // in seconds
}

export interface JobRequest {
  url: string;
  start: string; // Time in hh:mm:ss format
  end: string;   // Time in hh:mm:ss format  
  accepted_terms: boolean;
}

export interface JobResponse {
  jobId: string;
}

export interface JobStatus {
  status: 'queued' | 'working' | 'done' | 'error';
  progress?: number;
  url?: string;
  errorCode?: string;
  errorMessage?: string;
}

export interface RateLimitError extends Error {
  retryAfter: number;
  limitType: 'global' | 'job_creation';
  isRateLimitError: true;
}

export class RateLimitError extends Error implements RateLimitError {
  retryAfter: number;
  limitType: 'global' | 'job_creation';
  isRateLimitError: true = true;

  constructor(message: string, retryAfter: number, limitType: 'global' | 'job_creation') {
    super(message);
    this.name = 'RateLimitError';
    this.retryAfter = retryAfter;
    this.limitType = limitType;
  }
}

/**
 * Handle API errors, specifically rate limiting
 */
async function handleApiError(response: Response): Promise<never> {
  if (response.status === 429) {
    const data = await response.json().catch(() => ({}));
    throw new RateLimitError(
      data.detail || 'Rate limit exceeded',
      data.retry_after || 60,
      data.limit_type || 'global'
    );
  }
  
  // For other errors, throw a generic error
  const errorText = await response.text().catch(() => 'Unknown error');
  throw new Error(`API Error ${response.status}: ${errorText}`);
}

export async function fetchVideoMetadata(url: string): Promise<VideoMetadata> {
  const response = await fetch(`${BASE_URL}/api/v1/metadata`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ url }),
  });

  if (!response.ok) {
    return handleApiError(response);
  }

  return response.json();
}

export async function createJob(request: JobRequest): Promise<JobResponse> {
  const response = await fetch(`${BASE_URL}/api/v1/jobs`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    return handleApiError(response);
  }

  return response.json();
}

export async function getJobStatus(jobId: string): Promise<JobStatus> {
  const response = await fetch(`${BASE_URL}/api/v1/jobs/${jobId}`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
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
export function isRateLimitError(error: any): error is RateLimitError {
  return error && error.isRateLimitError === true;
}

/**
 * Format retry time as human-readable string
 */
export function formatRetryTime(seconds: number): string {
  if (seconds < 60) {
    return `${seconds} second${seconds !== 1 ? 's' : ''}`;
  }
  
  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = seconds % 60;
  
  if (remainingSeconds === 0) {
    return `${minutes} minute${minutes !== 1 ? 's' : ''}`;
  }
  
  return `${minutes}m ${remainingSeconds}s`;
} 