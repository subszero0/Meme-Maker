// Test script to verify getBestVideoUrl function
const testMetadata = {
  "title": "Video by sigmapolitics",
  "duration": 63.088,
  "url": "https://www.instagram.com/reel/DHAwk1mS_5I/?igsh=dW1wdTQydzF6d2F3",
  "formats": [
    {
      "format_id": "1365708264846800v-0",
      "ext": "mp4",
      "resolution": "360x640",
      "url": "https://instagram.fdel8-2.fna.fbcdn.net/test0.mp4",
      "filesize": null,
      "fps": null,
      "vcodec": "none",
      "acodec": "none",
      "format_note": ""
    },
    {
      "format_id": "1365708264846800v-1",
      "ext": "mp4",
      "resolution": "360x640",
      "url": "https://instagram.fdel8-2.fna.fbcdn.net/test1.mp4",
      "filesize": null,
      "fps": null,
      "vcodec": "none",
      "acodec": "none",
      "format_note": ""
    },
    {
      "format_id": "1365708264846800v-2",
      "ext": "mp4",
      "resolution": "360x640",
      "url": "https://instagram.fdel8-2.fna.fbcdn.net/test2.mp4",
      "filesize": null,
      "fps": null,
      "vcodec": "none",
      "acodec": "none",
      "format_note": ""
    },
    {
      "format_id": "dash-1365708264846800vd",
      "ext": "mp4",
      "resolution": "360x640",
      "url": "https://instagram.fdel8-2.fna.fbcdn.net/audio-video.mp4",
      "filesize": null,
      "fps": null,
      "vcodec": "avc1.4d001e",
      "acodec": "aac",
      "format_note": "DASH video (audio will be merged)"
    }
  ]
};

// Simulate the getBestVideoUrl function
function getBestVideoUrl(metadata) {
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
    const bestFormat = audioVideoFormats[0]; // For simplicity, just take the first one
    console.log(`🎵 ✅ SELECTED audio+video format: ${bestFormat.format_id} (${bestFormat.resolution}) with audio codec: ${bestFormat.acodec}`);
    return bestFormat.url;
  }

  console.warn('⚠️ No audio+video formats found, falling back to video-only');
  return originalUrl;
}

// Test the function
console.log('=== Testing getBestVideoUrl function ===');
const result = getBestVideoUrl(testMetadata);
console.log('🎯 Final result:', result);
console.log('✅ Expected: https://instagram.fdel8-2.fna.fbcdn.net/audio-video.mp4');
console.log('✅ Match:', result === 'https://instagram.fdel8-2.fna.fbcdn.net/audio-video.mp4'); 