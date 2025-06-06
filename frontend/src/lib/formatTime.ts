/**
 * Formats seconds to mm:ss.mmm format (no hours needed for videos under 60 minutes)
 * @param seconds - Time in seconds (can include fractional seconds)
 * @returns Formatted time string
 */
export function formatTime(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  const ms = Math.floor((seconds % 1) * 1000);

  return `${m.toString().padStart(2, "0")}:${s.toString().padStart(2, "0")}.${ms.toString().padStart(3, "0")}`;
}

/**
 * Formats seconds to mm:ss format for API requests
 * @param seconds - Time in seconds
 * @returns Formatted time string without milliseconds
 */
export function formatTimeForAPI(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);

  return `${m.toString().padStart(2, "0")}:${s.toString().padStart(2, "0")}`;
}

/**
 * Parses a time string in mm:ss.mmm or mm:ss format to seconds
 * @param timeString - Time string to parse
 * @returns Time in seconds or null if invalid format
 */
export function parseTime(timeString: string): number | null {
  if (!timeString || timeString.trim() === '') return null;
  
  const trimmed = timeString.trim();
  
  // Pattern for mm:ss.mmm or mm:ss format only (no hours)
  const pattern = /^(\d{1,2}):(\d{1,2})(?:\.(\d{1,3}))?$/;
  const match = trimmed.match(pattern);
  
  if (!match) return null;
  
  const minutes = parseInt(match[1], 10);
  const seconds = parseInt(match[2], 10);
  const milliseconds = match[3] ? parseInt(match[3].padEnd(3, '0'), 10) : 0;

  if (minutes >= 60 || seconds >= 60 || milliseconds >= 1000) return null;

  return minutes * 60 + seconds + milliseconds / 1000;
}
