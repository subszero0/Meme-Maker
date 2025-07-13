interface VideoFormat {
  format_id: string;
  ext: string;
  resolution: string;
  url: string;
  filesize?: number;
  fps?: number;
  vcodec: string;
  acodec: string;
  format_note: string;
}

interface VideoMetadata {
  title: string;
  duration: number;
  thumbnail: string;
  uploader: string;
  upload_date: string;
  view_count: number;
  formats: VideoFormat[];
  url: string; // Original platform URL
}

/**
 * Get the best video URL for playback, prioritizing formats with audio
 * 
 * @param metadata Video metadata containing available formats
 * @returns Best video URL for playback with audio
 */
export function getBestVideoUrl(metadata: VideoMetadata): string {
  const { formats, url: originalUrl } = metadata;

  // If no formats available, fall back to original URL
  if (!formats || formats.length === 0) {
    return originalUrl;
  }

  // Filter formats that have both video and audio
  const audioVideoFormats = formats.filter(
    format => 
      format.vcodec && format.vcodec !== 'none' &&
      format.acodec && format.acodec !== 'none' &&
      format.url && format.url.trim() !== ''
  );

  // If we have audio+video combined formats, use the best one
  if (audioVideoFormats.length > 0) {
    // Sort by resolution (width * height) descending, then by filesize
    const bestFormat = audioVideoFormats.sort((a, b) => {
      const getResolutionScore = (resolution: string): number => {
        try {
          const [width, height] = resolution.split('x').map(Number);
          return width * height;
        } catch {
          return 0;
        }
      };

      const aScore = getResolutionScore(a.resolution);
      const bScore = getResolutionScore(b.resolution);
      
      if (aScore !== bScore) {
        return bScore - aScore; // Higher resolution first
      }
      
      // If resolutions are equal, prefer larger file size (better quality)
      return (b.filesize || 0) - (a.filesize || 0);
    })[0];

    console.log(`🎵 Using audio+video format: ${bestFormat.format_id} (${bestFormat.resolution}) with audio codec: ${bestFormat.acodec}`);
    return bestFormat.url;
  }

  // If no combined formats, look for the best video-only format
  // (This is a fallback - might not have audio)
  const videoOnlyFormats = formats.filter(
    format => 
      format.vcodec && format.vcodec !== 'none' &&
      format.url && format.url.trim() !== ''
  );

  if (videoOnlyFormats.length > 0) {
    const bestVideoFormat = videoOnlyFormats.sort((a, b) => {
      const getResolutionScore = (resolution: string): number => {
        try {
          const [width, height] = resolution.split('x').map(Number);
          return width * height;
        } catch {
          return 0;
        }
      };

      return getResolutionScore(b.resolution) - getResolutionScore(a.resolution);
    })[0];

    console.warn(`⚠️ Using video-only format: ${bestVideoFormat.format_id} (${bestVideoFormat.resolution}) - may not have audio`);
    return bestVideoFormat.url;
  }

  // Final fallback to original URL
  console.warn(`⚠️ No suitable formats found, falling back to original URL: ${originalUrl}`);
  return originalUrl;
} 