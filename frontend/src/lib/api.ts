import axios from 'axios';

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface VideoMetadata {
  url: string;
  title: string;
  duration: number; // in seconds
}

export interface JobRequest {
  url: string;
  in: number;
  out: number;
  rights: boolean;
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

export async function fetchVideoMetadata(url: string): Promise<VideoMetadata> {
  const response = await axios.post(`${BASE_URL}/api/v1/metadata`, { url });
  return response.data;
}

export async function createJob(request: JobRequest): Promise<JobResponse> {
  const response = await axios.post(`${BASE_URL}/api/v1/jobs`, request);
  return response.data;
}

export async function getJobStatus(jobId: string): Promise<JobStatus> {
  const response = await axios.get(`${BASE_URL}/api/v1/jobs/${jobId}`);
  return response.data;
} 