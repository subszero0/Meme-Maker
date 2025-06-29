export * from "./api/metadata";
export * from "./api/jobs";
export * from "./api/misc";

// ===========================
// Utility Functions
// ===========================

export function formatDuration(seconds: number): string {
  if (isNaN(seconds) || seconds < 0) {
    return "00:00";
  }
  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = Math.floor(seconds % 60);
  return `${minutes.toString().padStart(2, "0")}:${remainingSeconds
    .toString()
    .padStart(2, "0")}`;
}

export function parseResolutionHeight(resolution: string): number {
  if (!resolution || typeof resolution !== "string") {
    return 0;
  }
  const parts = resolution.split("x");
  return parts.length > 1 ? parseInt(parts[1], 10) : 0;
}

export function formatFileSize(bytes?: number): string {
  if (bytes === undefined || bytes === null || isNaN(bytes)) {
    return "N/A";
  }
  if (bytes === 0) {
    return "0 B";
  }
  const k = 1024;
  const sizes = ["B", "KB", "MB", "GB", "TB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
}