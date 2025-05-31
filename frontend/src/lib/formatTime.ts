/**
 * Formats seconds to hh:mm:ss.mmm format
 * @param seconds - Time in seconds (can include fractional seconds)
 * @returns Formatted time string
 */
export function formatTime(seconds: number): string {
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = Math.floor(seconds % 60);
  const ms = Math.floor((seconds % 1) * 1000);
  
  if (h > 0) {
    return `${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}.${ms.toString().padStart(3, '0')}`;
  }
  return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}.${ms.toString().padStart(3, '0')}`;
}

/**
 * Formats seconds to hh:mm:ss format for API requests
 * @param seconds - Time in seconds
 * @returns Formatted time string without milliseconds
 */
export function formatTimeForAPI(seconds: number): string {
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = Math.floor(seconds % 60);
  
  return `${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
}

/**
 * Parses a time string in hh:mm:ss.mmm or mm:ss.mmm format to seconds
 * @param timeString - Time string to parse
 * @returns Time in seconds or null if invalid format
 */
export function parseTime(timeString: string): number | null {
  const pattern = /^(?:(\d{1,2}):)?(\d{1,2}):(\d{1,2})\.(\d{3})$/;
  const match = timeString.match(pattern);
  
  if (!match) return null;
  
  const hours = match[1] ? parseInt(match[1], 10) : 0;
  const minutes = parseInt(match[2], 10);
  const seconds = parseInt(match[3], 10);
  const milliseconds = parseInt(match[4], 10);
  
  if (minutes >= 60 || seconds >= 60 || milliseconds >= 1000) return null;
  
  return hours * 3600 + minutes * 60 + seconds + milliseconds / 1000;
} 