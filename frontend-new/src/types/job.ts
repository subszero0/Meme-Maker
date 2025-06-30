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
  resolution?: string;
}

export interface JobResponse {
  id: string;
  status: JobStatus;
  progress: number;
  download_url?: string;
  source_url?: string;
  error_message?: string;
  error_code?: string | null;
  stage?: string;
  created_at?: string;
  updated_at?: string;
}
