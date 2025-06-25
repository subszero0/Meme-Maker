import { setupServer } from "msw/node";
import { http, HttpResponse } from "msw";

// Mock data
const mockVideoMetadata = {
  title: "Test Video Title",
  duration: 120,
  thumbnail: "https://example.com/thumbnail.jpg",
  upload_date: "2024-01-01",
  uploader: "Test Uploader",
  formats: [
    {
      format_id: "18",
      ext: "mp4",
      resolution: "360p",
      filesize: 10485760,
      url: "https://example.com/video.mp4",
      vcodec: "avc1.42001E",
      acodec: "mp4a.40.2",
      fps: 30,
      width: 640,
      height: 360,
    },
    {
      format_id: "22",
      ext: "mp4",
      resolution: "720p",
      filesize: 52428800,
      url: "https://example.com/video_hd.mp4",
      vcodec: "avc1.64001F",
      acodec: "mp4a.40.2",
      fps: 30,
      width: 1280,
      height: 720,
    },
  ],
};

const mockJobResponse = {
  id: "test-job-123",
  status: "queued",
  progress: 0,
  created_at: "2024-01-01T00:00:00Z",
  url: "https://youtube.com/watch?v=test",
  in_ts: 10,
  out_ts: 40,
  format_id: "18",
};

// API request handlers
export const handlers = [
  // Health check endpoint
  http.get("http://localhost:8000/health", () => {
    return HttpResponse.json({ status: "ok" });
  }),

  // Metadata endpoint
  http.get("http://localhost:8000/api/metadata", ({ request }) => {
    const url = new URL(request.url);
    const videoUrl = url.searchParams.get("url");

    if (!videoUrl) {
      return HttpResponse.json(
        { error: "URL parameter is required" },
        { status: 400 },
      );
    }

    if (videoUrl.includes("invalid")) {
      return HttpResponse.json({ error: "Invalid video URL" }, { status: 400 });
    }

    return HttpResponse.json(mockVideoMetadata);
  }),

  // Create clip job endpoint
  http.post("http://localhost:8000/api/clips", async ({ request }) => {
    const body = (await request.json()) as any;

    if (!body.url || !body.in_ts || !body.out_ts || !body.format_id) {
      return HttpResponse.json(
        { error: "Missing required parameters" },
        { status: 400 },
      );
    }

    return HttpResponse.json({
      ...mockJobResponse,
      url: body.url,
      in_ts: body.in_ts,
      out_ts: body.out_ts,
      format_id: body.format_id,
    });
  }),

  // Get job status endpoint
  http.get("http://localhost:8000/api/jobs/:jobId", ({ params }) => {
    const { jobId } = params;

    if (jobId === "not-found") {
      return HttpResponse.json({ error: "Job not found" }, { status: 404 });
    }

    // Simulate different job statuses based on jobId
    let status = "completed";
    let progress = 100;
    let download_url = null;

    if (jobId === "queued-job") {
      status = "queued";
      progress = 0;
    } else if (jobId === "processing-job") {
      status = "processing";
      progress = 50;
    } else if (jobId === "error-job") {
      status = "error";
      progress = 0;
    } else if (jobId === "completed-job") {
      status = "completed";
      progress = 100;
      download_url = "https://example.com/download/test-clip.mp4";
    }

    return HttpResponse.json({
      ...mockJobResponse,
      id: jobId,
      status,
      progress,
      download_url,
    });
  }),

  // Cancel job endpoint
  http.post("http://localhost:8000/api/jobs/:jobId/cancel", ({ params }) => {
    const { jobId } = params;

    return HttpResponse.json({
      ...mockJobResponse,
      id: jobId,
      status: "cancelled",
      progress: 0,
    });
  }),

  // Download cleanup endpoint
  http.delete("http://localhost:8000/api/clips/:filename", ({ params }) => {
    const { filename } = params;

    if (filename === "not-found.mp4") {
      return HttpResponse.json({ error: "File not found" }, { status: 404 });
    }

    return HttpResponse.json({
      message: "File deleted successfully",
    });
  }),
];

// Create MSW server
export const server = setupServer(...handlers);
