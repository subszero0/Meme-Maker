export enum JobStatus {
  QUEUED = "queued",
  WORKING = "working",
  DONE = "done",
  ERROR = "error",
}

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