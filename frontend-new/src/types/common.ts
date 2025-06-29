export interface HealthResponse {
  status: string;
}

export interface ApiError {
  message: string;
  status?: number;
  code?: string;
} 