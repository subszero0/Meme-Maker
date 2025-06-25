# API Integration Guide - Frontend-New ✅

This document explains how the new React frontend (`frontend-new/`) integrates with the Meme Maker backend API.

> **🎉 INTEGRATION COMPLETE**: This frontend is now fully integrated and production-ready!

## Overview

The frontend-new uses a modern API integration pattern with:

- **Axios** for HTTP requests
- **React Query** for caching and state management
- **TypeScript** interfaces for type safety
- **Environment-based configuration**

## API Endpoints

### 1. Video Metadata

**GET** `/metadata?url={video_url}`

Retrieves video information from a URL.

```typescript
interface MetadataResponse {
  title: string;
  duration: number;
  thumbnail: string;
  formats: VideoFormat[];
  uploader?: string;
  upload_date?: string;
}

interface VideoFormat {
  format_id: string;
  height: number;
  fps?: number;
  vcodec: string;
  acodec: string;
  filesize?: number;
}
```

### 2. Job Creation

**POST** `/jobs`

Creates a new video processing job.

```typescript
interface JobRequest {
  url: string;
  start_time: number;
  end_time: number;
  format_id: string;
}

interface JobResponse {
  job_id: string;
  status: "pending" | "processing" | "completed" | "failed";
  created_at: string;
}
```

### 3. Job Status

**GET** `/jobs/{job_id}`

Retrieves job processing status.

```typescript
interface JobStatusResponse {
  job_id: string;
  status: "pending" | "processing" | "completed" | "failed";
  progress: number; // 0-100
  stage: string;
  result?: {
    download_url: string;
    filename: string;
    filesize: number;
    expires_at: string;
  };
  error_message?: string;
}
```

## Implementation

### API Client Setup

```typescript
// src/lib/api.ts
import axios from "axios";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    "Content-Type": "application/json",
  },
});

// Request interceptor for logging
api.interceptors.request.use((config) => {
  console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`);
  return config;
});

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error("API Error:", error.response?.data || error.message);
    return Promise.reject(error);
  },
);
```

### React Query Integration

```typescript
// src/hooks/useApi.ts
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";

// Fetch video metadata
export function useMetadata(url: string) {
  return useQuery({
    queryKey: ["metadata", url],
    queryFn: async () => {
      const response = await api.get<MetadataResponse>("/metadata", {
        params: { url },
      });
      return response.data;
    },
    enabled: !!url,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

// Create processing job
export function useCreateJob() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (request: JobRequest) => {
      const response = await api.post<JobResponse>("/jobs", request);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["jobs"] });
    },
  });
}

// Poll job status
export function useJobStatus(jobId: string | null) {
  return useQuery({
    queryKey: ["job", jobId],
    queryFn: async () => {
      if (!jobId) throw new Error("No job ID");
      const response = await api.get<JobStatusResponse>(`/jobs/${jobId}`);
      return response.data;
    },
    enabled: !!jobId,
    refetchInterval: (data) => {
      // Stop polling when complete or failed
      if (data?.status === "completed" || data?.status === "failed") {
        return false;
      }
      return 2000; // Poll every 2 seconds
    },
  });
}
```

### Component Usage Example

```typescript
// Example component using the API hooks
import { useState } from 'react';
import { useMetadata, useCreateJob, useJobStatus } from '@/hooks/useApi';

export function VideoProcessor() {
  const [url, setUrl] = useState('');
  const [jobId, setJobId] = useState<string | null>(null);

  const { data: metadata, isLoading: metadataLoading, error: metadataError } = useMetadata(url);
  const createJob = useCreateJob();
  const { data: jobStatus } = useJobStatus(jobId);

  const handleSubmit = async (trimData: { start: number; end: number; formatId: string }) => {
    try {
      const result = await createJob.mutateAsync({
        url,
        start_time: trimData.start,
        end_time: trimData.end,
        format_id: trimData.formatId,
      });
      setJobId(result.job_id);
    } catch (error) {
      console.error('Failed to create job:', error);
    }
  };

  if (metadataLoading) return <div>Loading video metadata...</div>;
  if (metadataError) return <div>Error loading video</div>;
  if (!metadata) return <div>Enter a video URL</div>;

  return (
    <div>
      <h2>{metadata.title}</h2>
      <p>Duration: {metadata.duration}s</p>
      {/* Trim controls and job status UI */}
    </div>
  );
}
```

## Error Handling

### API Error Types

```typescript
interface ApiError {
  detail: string;
  status: number;
  type: "validation_error" | "not_found" | "server_error";
}
```

### Error Handling Strategy

```typescript
// Global error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    const apiError: ApiError = {
      detail: error.response?.data?.detail || "Unknown error",
      status: error.response?.status || 500,
      type: error.response?.status >= 500 ? "server_error" : "validation_error",
    };

    // Show user-friendly error messages
    if (apiError.status === 400) {
      toast.error("Invalid request. Please check your input.");
    } else if (apiError.status === 404) {
      toast.error("Video not found or unavailable.");
    } else if (apiError.status >= 500) {
      toast.error("Server error. Please try again later.");
    }

    return Promise.reject(apiError);
  },
);
```

## Environment Configuration

```typescript
// Environment variables
const config = {
  apiBaseUrl: import.meta.env.VITE_API_BASE_URL || "http://localhost:8000",
  timeout: Number(import.meta.env.VITE_API_TIMEOUT) || 30000,
  retries: Number(import.meta.env.VITE_API_RETRIES) || 3,
};
```

## Testing

### API Mocking for Tests

```typescript
// src/test/mocks/api.ts
import { http, HttpResponse } from "msw";

export const apiHandlers = [
  http.get("/metadata", ({ request }) => {
    const url = new URL(request.url);
    const videoUrl = url.searchParams.get("url");

    return HttpResponse.json({
      title: "Test Video",
      duration: 120,
      thumbnail: "https://example.com/thumb.jpg",
      formats: [
        { format_id: "720p", height: 720, vcodec: "h264", acodec: "aac" },
      ],
    });
  }),

  http.post("/jobs", () => {
    return HttpResponse.json({
      job_id: "test-job-123",
      status: "pending",
      created_at: new Date().toISOString(),
    });
  }),

  http.get("/jobs/:jobId", ({ params }) => {
    return HttpResponse.json({
      job_id: params.jobId,
      status: "completed",
      progress: 100,
      stage: "finished",
      result: {
        download_url: "https://example.com/download/test.mp4",
        filename: "test-clip.mp4",
        filesize: 1024000,
        expires_at: new Date(Date.now() + 3600000).toISOString(),
      },
    });
  }),
];
```

## Performance Optimizations

### Request Deduplication

React Query automatically deduplicates identical requests.

### Caching Strategy

- Metadata: 5 minutes stale time
- Job status: Real-time polling with automatic cleanup
- Failed requests: Retry up to 3 times with exponential backoff

### Background Refetching

Queries refetch on window focus and network reconnection.

## Security

### CORS Configuration

Ensure backend allows frontend origins:

```python
# Backend CORS settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
```

### Input Validation

- URLs are validated before API calls
- Trim times are validated against video duration
- File size limits are enforced

This integration provides a robust, type-safe, and performant connection between the React frontend and FastAPI backend.
