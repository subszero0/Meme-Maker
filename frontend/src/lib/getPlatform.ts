/**
 * Platform detection utility for video URLs
 */
export type Platform =
  | "youtube"
  | "instagram"
  | "facebook"
  | "threads"
  | "reddit"
  | "unknown";

/**
 * Detects the platform from a video URL
 * @param url - The URL to check
 * @returns The detected platform or 'unknown' if not recognized or invalid
 */
export default function getPlatform(url: string): Platform {
  try {
    const hostname = new URL(url).hostname.toLowerCase().replace(/^www\./, "");

    if (
      hostname === "youtube.com" ||
      hostname === "youtu.be" ||
      hostname === "m.youtube.com"
    ) {
      return "youtube";
    }
    if (hostname === "instagram.com") {
      return "instagram";
    }
    if (
      hostname === "facebook.com" ||
      hostname === "fb.watch" ||
      hostname === "m.facebook.com"
    ) {
      return "facebook";
    }
    if (hostname === "threads.net") {
      return "threads";
    }
    if (
      hostname === "reddit.com" ||
      hostname === "redd.it" ||
      hostname === "v.redd.it"
    ) {
      return "reddit";
    }

    return "unknown";
  } catch {
    return "unknown";
  }
}
