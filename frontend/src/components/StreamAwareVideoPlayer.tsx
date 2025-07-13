"use client";

import { useState, useCallback, useRef, useEffect } from "react";
import ReactPlayer from "react-player";
import { VolumeX, Volume2, Play, Pause } from "lucide-react";

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

interface StreamAwareVideoPlayerProps {
  originalUrl: string;
  onProgress?: (state: {
    played: number;
    loaded: number;
    playedSeconds: number;
    loadedSeconds: number;
  }) => void;
  className?: string;
  autoPlay?: boolean;
  showControls?: boolean;
  preferredQuality?: string;
}

export default function StreamAwareVideoPlayer({
  originalUrl,
  onProgress,
  className = "w-full h-64",
  autoPlay = false,
  showControls = true,
  preferredQuality = "720p",
}: StreamAwareVideoPlayerProps) {
  const [playing, setPlaying] = useState(false);
  const [muted, setMuted] = useState(false);
  const [volume, setVolume] = useState(0.8);
  const [hasUserInteracted, setHasUserInteracted] = useState(false);
  const [streamUrl, setStreamUrl] = useState<string>(originalUrl);
  const [formats, setFormats] = useState<VideoFormat[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const playerRef = useRef<ReactPlayer>(null);

  // Fetch available stream formats
  useEffect(() => {
    const fetchStreamFormats = async () => {
      try {
        setLoading(true);
        setError(null);

        const apiUrl = `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/v1/metadata/extract`;
        
        const response = await fetch(apiUrl, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ url: originalUrl }),
        });

        if (!response.ok) {
          throw new Error(`Failed to fetch formats: ${response.status}`);
        }

        const data = await response.json();
        const availableFormats = data.formats || [];
        
        setFormats(availableFormats);

        // Select the best stream URL for playback
        const bestStreamUrl = selectBestStreamUrl(availableFormats, preferredQuality);
        setStreamUrl(bestStreamUrl);

        console.log("🎬 StreamAwareVideoPlayer: Available formats:", availableFormats.length);
        console.log("🎬 StreamAwareVideoPlayer: Selected stream URL:", bestStreamUrl);

      } catch (err) {
        console.error("🎬 StreamAwareVideoPlayer: Failed to fetch formats:", err);
        setError(err instanceof Error ? err.message : "Failed to load video formats");
        // Fallback to original URL
        setStreamUrl(originalUrl);
      } finally {
        setLoading(false);
      }
    };

    if (originalUrl) {
      fetchStreamFormats();
    }
  }, [originalUrl, preferredQuality]);

  const selectBestStreamUrl = (formats: VideoFormat[], preferredQuality: string): string => {
    if (!formats.length) {
      return originalUrl;
    }

    // Filter formats that have both video and audio
    const audioVideoFormats = formats.filter(f => 
      f.vcodec && f.vcodec !== 'none' && 
      f.acodec && f.acodec !== 'none' &&
      f.url && f.url.trim() !== ''
    );

    console.log("🎬 StreamAwareVideoPlayer: Audio+Video formats:", audioVideoFormats.length);

    if (audioVideoFormats.length === 0) {
      console.warn("🎬 StreamAwareVideoPlayer: No combined audio+video formats found, using original URL");
      return originalUrl;
    }

    // Try to find preferred quality
    const preferredFormat = audioVideoFormats.find(f => 
      f.resolution && f.resolution.includes(preferredQuality.replace('p', ''))
    );

    if (preferredFormat) {
      console.log("🎬 StreamAwareVideoPlayer: Using preferred quality:", preferredFormat.resolution);
      return preferredFormat.url;
    }

    // Fallback to best available quality
    const bestFormat = audioVideoFormats.reduce((best, current) => {
      const bestHeight = parseInt(best.resolution?.split('x')[1] || '0') || 0;
      const currentHeight = parseInt(current.resolution?.split('x')[1] || '0') || 0;
      return currentHeight > bestHeight ? current : best;
    });

    console.log("🎬 StreamAwareVideoPlayer: Using best available quality:", bestFormat.resolution);
    return bestFormat.url;
  };

  const handlePlayPause = useCallback(() => {
    if (!hasUserInteracted) {
      setHasUserInteracted(true);
    }
    setPlaying(!playing);
  }, [playing, hasUserInteracted]);

  const handleMuteToggle = useCallback(() => {
    if (!hasUserInteracted) {
      setHasUserInteracted(true);
    }
    setMuted(!muted);
  }, [muted, hasUserInteracted]);

  const handleVolumeChange = useCallback((newVolume: number) => {
    if (!hasUserInteracted) {
      setHasUserInteracted(true);
    }
    setVolume(newVolume);
    if (newVolume === 0) {
      setMuted(true);
    } else if (muted) {
      setMuted(false);
    }
  }, [muted, hasUserInteracted]);

  const handleReady = useCallback(() => {
    console.log("🎬 StreamAwareVideoPlayer: Video ready");
    if (autoPlay && hasUserInteracted) {
      setPlaying(true);
    }
  }, [autoPlay, hasUserInteracted]);

  const handleError = useCallback((error: any) => {
    console.error("🎬 StreamAwareVideoPlayer: Video player error:", error);
    setError("Video playback failed");
  }, []);

  if (loading) {
    return (
      <div className={`${className} bg-black rounded-lg overflow-hidden flex items-center justify-center`}>
        <div className="text-white text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-white mx-auto mb-2"></div>
          <p>Loading video...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`${className} bg-black rounded-lg overflow-hidden flex items-center justify-center`}>
        <div className="text-white text-center">
          <p className="text-red-400 mb-2">⚠️ {error}</p>
          <p className="text-sm opacity-75">Falling back to original URL</p>
        </div>
      </div>
    );
  }

  return (
    <div className={`relative ${className} bg-black rounded-lg overflow-hidden`}>
      <ReactPlayer
        ref={playerRef}
        url={streamUrl}
        width="100%"
        height="100%"
        playing={playing}
        muted={muted}
        volume={volume}
        controls={false}
        onProgress={onProgress}
        onReady={handleReady}
        onError={handleError}
        config={{
          file: {
            attributes: {
              preload: 'metadata',
              controlsList: 'nodownload',
              crossOrigin: 'anonymous',
            },
            forceAudio: true,
          },
        }}
      />
      
      {showControls && (
        <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/80 to-transparent p-4">
          <div className="flex items-center justify-between text-white">
            <div className="flex items-center space-x-3">
              {/* Play/Pause Button */}
              <button
                onClick={handlePlayPause}
                className="p-2 rounded-full bg-white/20 hover:bg-white/30 transition-colors"
                aria-label={playing ? "Pause" : "Play"}
              >
                {playing ? (
                  <Pause className="w-5 h-5" />
                ) : (
                  <Play className="w-5 h-5" />
                )}
              </button>

              {/* Mute/Unmute Button */}
              <button
                onClick={handleMuteToggle}
                className="p-2 rounded-full bg-white/20 hover:bg-white/30 transition-colors"
                aria-label={muted ? "Unmute" : "Mute"}
              >
                {muted ? (
                  <VolumeX className="w-5 h-5" />
                ) : (
                  <Volume2 className="w-5 h-5" />
                )}
              </button>

              {/* Volume Slider */}
              <div className="flex items-center space-x-2">
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.1"
                  value={volume}
                  onChange={(e) => handleVolumeChange(parseFloat(e.target.value))}
                  className="w-20 h-2 bg-white/20 rounded-lg appearance-none cursor-pointer"
                  style={{
                    background: `linear-gradient(to right, #3b82f6 0%, #3b82f6 ${volume * 100}%, rgba(255,255,255,0.2) ${volume * 100}%, rgba(255,255,255,0.2) 100%)`,
                  }}
                />
                <span className="text-sm font-mono w-8">
                  {Math.round(volume * 100)}
                </span>
              </div>
            </div>

            {/* Stream Info */}
            <div className="text-sm text-white/75">
              {formats.length > 0 && (
                <span>
                  {formats.filter(f => f.vcodec !== 'none' && f.acodec !== 'none').length} A+V streams
                </span>
              )}
            </div>

            {/* User Interaction Indicator */}
            {!hasUserInteracted && (
              <div className="text-sm text-yellow-300">
                Click to enable audio
              </div>
            )}
          </div>
        </div>
      )}

      {/* Click overlay for first interaction */}
      {!hasUserInteracted && (
        <div 
          className="absolute inset-0 flex items-center justify-center bg-black/50 cursor-pointer"
          onClick={() => {
            setHasUserInteracted(true);
            setPlaying(true);
          }}
        >
          <div className="text-center text-white">
            <Play className="w-16 h-16 mx-auto mb-2" />
            <p className="text-lg font-semibold">Click to play with audio</p>
            <p className="text-sm opacity-75">Using direct stream URL</p>
          </div>
        </div>
      )}
    </div>
  );
} 