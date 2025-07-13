"use client";

import { useState, useCallback, useRef } from "react";
import ReactPlayer from "react-player";
import { VolumeX, Volume2, Play, Pause } from "lucide-react";

interface AudioAwareVideoPlayerProps {
  url: string;
  onProgress?: (state: {
    played: number;
    loaded: number;
    playedSeconds: number;
    loadedSeconds: number;
  }) => void;
  className?: string;
  autoPlay?: boolean;
  showControls?: boolean;
}

export default function AudioAwareVideoPlayer({
  url,
  onProgress,
  className = "w-full h-64",
  autoPlay = false,
  showControls = true,
}: AudioAwareVideoPlayerProps) {
  const [playing, setPlaying] = useState(false);
  const [muted, setMuted] = useState(false);
  const [volume, setVolume] = useState(0.8);
  const [hasUserInteracted, setHasUserInteracted] = useState(false);
  const playerRef = useRef<ReactPlayer>(null);

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
    // Auto-play only if user has interacted and autoPlay is enabled
    if (autoPlay && hasUserInteracted) {
      setPlaying(true);
    }
  }, [autoPlay, hasUserInteracted]);

  const handleError = useCallback((error: any) => {
    console.error("Video player error:", error);
  }, []);

  return (
    <div className={`relative ${className} bg-black rounded-lg overflow-hidden`}>
      <ReactPlayer
        ref={playerRef}
        url={url}
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
            },
            forceAudio: true,
          },
          youtube: {
            playerVars: { 
              showinfo: 1,
              rel: 0,
              modestbranding: 1,
            },
          },
          facebook: {
            appId: 'your-app-id', // You may need to configure this
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
            <p className="text-sm opacity-75">Required by browser policy</p>
          </div>
        </div>
      )}
    </div>
  );
} 