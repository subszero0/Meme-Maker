import axios from "axios";

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface VideoMetadata {
  url: string;
  title: string;
  duration: number; // in seconds
}

export interface JobRequest {
  url: string;
  in_ts: number;
  out_ts: number;
  format_id?: string;
}

export interface JobResponse {
  id: string;
  status: string;
  created_at: string;
}

export interface JobStatus {
  status: "queued" | "working" | "done" | "error";
  progress?: number;
  url?: string;
  errorCode?: string;
  errorMessage?: string;
}

export async function fetchVideoMetadata(url: string): Promise<VideoMetadata> {
  console.log("API: Making request to:", `${BASE_URL}/api/v1/metadata`);
  console.log("API: Request payload:", { url });
  console.log("API: BASE_URL from env:", process.env.NEXT_PUBLIC_API_URL);

  try {
    const response = await axios.post(
      `${BASE_URL}/api/v1/metadata`,
      { url },
      {
        timeout: 30000, // 30 second timeout
        headers: {
          "Content-Type": "application/json",
        },
      },
    );
    console.log("API: Response received:", response.data);
    console.log("API: Response status:", response.status);
    console.log("API: Response headers:", response.headers);

    // Backend response: {title, duration, thumbnail_url, resolutions}
    // Frontend expects: {url, title, duration}
    // Add the original URL to the response
    return {
      url: url, // Add the original URL
      title: response.data.title,
      duration: response.data.duration,
    };
  } catch (error) {
    console.error("API: Request failed with error:", error);
    if (axios.isAxiosError(error)) {
      console.error("API: Axios error details:", {
        message: error.message,
        code: error.code,
        status: error.response?.status,
        statusText: error.response?.statusText,
        data: error.response?.data,
        headers: error.response?.headers,
      });
    }
    throw error;
  }
}

export async function createJob(request: {
  url: string;
  in: number;
  out: number;
  rights: boolean;
  formatId?: string;
}): Promise<{ jobId: string }> {
  console.log("🔌 API: Creating job with frontend request:", request);

  // Transform frontend format to backend format
  const backendRequest: JobRequest = {
    url: request.url,
    in_ts: request.in, // Map 'in' to 'in_ts'
    out_ts: request.out, // Map 'out' to 'out_ts'
    format_id: request.formatId, // Include format_id if provided
    // Don't send 'rights' field to backend
  };

  console.log("🔌 API: Transformed backend request:", backendRequest);
  console.log("🔌 API: format_id value being sent:", backendRequest.format_id);

  try {
    const response = await axios.post(
      `${BASE_URL}/api/v1/jobs`,
      backendRequest,
      {
        timeout: 30000,
        headers: {
          "Content-Type": "application/json",
        },
      },
    );

    console.log("🔌 API: Job creation response:", response.data);
    console.log("🔌 API: Response format_id:", response.data.format_id);

    // Transform backend response to frontend format
    return {
      jobId: response.data.id, // Map 'id' to 'jobId'
    };
  } catch (error) {
    console.error("🔌 API: Job creation failed:", error);
    if (axios.isAxiosError(error)) {
      console.error("🔌 API: Job creation error details:", {
        message: error.message,
        status: error.response?.status,
        data: error.response?.data,
      });
    }
    throw error;
  }
}

export async function getJobStatus(jobId: string): Promise<JobStatus> {
  const response = await axios.get(`${BASE_URL}/api/v1/jobs/${jobId}`);
  return response.data;
}
