import axios from "axios";

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface VideoFormat {
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

export interface VideoMetadata {
  url: string;
  title: string;
  duration: number; // in seconds
  thumbnail: string;
  uploader: string;
  upload_date: string;
  view_count: number;
  formats: VideoFormat[];
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
  console.log("API: Making request to:", `${BASE_URL}/api/v1/metadata/extract`);
  console.log("API: Request payload:", { url });
  console.log("API: BASE_URL from env:", process.env.NEXT_PUBLIC_API_URL);

  try {
    const response = await axios.post(
      `${BASE_URL}/api/v1/metadata/extract`,
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

    // The backend returns the full VideoMetadata with formats
    // Add the original URL to the response since backend doesn't include it
    return {
      ...response.data,
      url: url, // Add the original URL
    };
  } catch (error) {
    console.error("API: Request failed:", error);
    if (axios.isAxiosError(error)) {
      console.error("API: Error response:", error.response?.data);
      console.error("API: Error status:", error.response?.status);
      console.error("API: Error headers:", error.response?.headers);
      
      if (error.response?.status === 422) {
        throw new Error(`Invalid request: ${error.response.data?.detail || 'Validation failed'}`);
      } else if (error.response?.status === 429) {
        throw new Error("Too many requests. Please try again in a few minutes.");
      } else if (error.response?.status && error.response.status >= 500) {
        throw new Error("Server error. Please try again later.");
      } else if (error.code === "ECONNREFUSED") {
        throw new Error("Cannot connect to server. Please ensure the backend is running.");
      }
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
