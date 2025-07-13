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
 * Get a proxied video URL that routes through our backend to bypass CORS restrictions
 * 
 * @param originalUrl The original video URL from Instagram/Facebook
 * @returns Proxied URL that can be played in the browser
 */
export function getProxiedVideoUrl(originalUrl: string): string {
  const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
  const encodedUrl = encodeURIComponent(originalUrl);
  return `${baseUrl}/api/v1/video/proxy?url=${encodedUrl}`;
}

/**
 * Get the best video URL for playback, prioritizing formats with audio
 * Uses video proxy to bypass CORS restrictions for Instagram/Facebook videos
 * 
 * @param metadata Video metadata containing available formats
 * @returns Best video URL for playback with audio (proxied if needed)
 */
export function getBestVideoUrl(metadata: VideoMetadata): string {
  const { formats, url: originalUrl } = metadata;

  // If no formats available, fall back to original URL
  if (!formats || formats.length === 0) {
    console.warn('⚠️ No formats available, using original URL');
    return originalUrl;
  }

  console.log('🔍 All available formats:', formats.map(f => ({
    id: f.format_id,
    resolution: f.resolution,
    vcodec: f.vcodec,
    acodec: f.acodec,
    hasVideo: f.vcodec && f.vcodec !== 'none',
    hasAudio: f.acodec && f.acodec !== 'none',
    url: f.url ? 'present' : 'missing'
  })));

  // Filter formats that have both video and audio
  const audioVideoFormats = formats.filter(
    format => 
      format.vcodec && format.vcodec !== 'none' &&
      format.acodec && format.acodec !== 'none' &&
      format.url && format.url.trim() !== ''
  );

  console.log('🎵 Audio+Video formats found:', audioVideoFormats.length, audioVideoFormats.map(f => ({
    id: f.format_id,
    resolution: f.resolution,
    vcodec: f.vcodec,
    acodec: f.acodec
  })));

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

    const proxiedUrl = getProxiedVideoUrl(bestFormat.url);
    console.log(`🎵 ✅ SELECTED audio+video format: ${bestFormat.format_id} (${bestFormat.resolution}) with audio codec: ${bestFormat.acodec}`);
    console.log(`🎵 🔄 Using proxied URL: ${proxiedUrl}`);
    return proxiedUrl;
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

    const proxiedUrl = getProxiedVideoUrl(bestVideoFormat.url);
    console.warn(`⚠️ Using video-only format: ${bestVideoFormat.format_id} (${bestVideoFormat.resolution}) - may not have audio`);
    console.log(`🔄 Using proxied URL: ${proxiedUrl}`);
    return proxiedUrl;
  }

  // Final fallback to original URL (also proxied for Instagram/Facebook)
  const shouldProxy = originalUrl.includes('instagram.') || originalUrl.includes('facebook.') || originalUrl.includes('fbcdn.net');
  if (shouldProxy) {
    const proxiedUrl = getProxiedVideoUrl(originalUrl);
    console.warn(`⚠️ No suitable formats found, falling back to proxied original URL: ${proxiedUrl}`);
    return proxiedUrl;
  }

  console.warn(`⚠️ No suitable formats found, falling back to original URL: ${originalUrl}`);
  return originalUrl;
} 