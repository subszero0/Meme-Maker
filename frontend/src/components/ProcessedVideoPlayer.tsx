"use client";

import { useState, useCallback, useRef, useEffect } from "react";
import ReactPlayer from "react-player";
import { VolumeX, Volume2, Play, Pause } from "lucide-react";

interface ProcessedVideoPlayerProps {
  jobId: string;
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

export default function ProcessedVideoPlayer({
  jobId,
  onProgress,
  className = "w-full h-64",
  autoPlay = false,
  showControls = true,
}: ProcessedVideoPlayerProps) {
  const [playing, setPlaying] = useState(false);
  const [muted, setMuted] = useState(false);
  const [volume, setVolume] = useState(0.8);
  const [hasUserInteracted, setHasUserInteracted] = useState(false);
  const playerRef = useRef<ReactPlayer>(null);

  // Generate the processed video URL
  const videoUrl = `/api/v1/jobs/${jobId}/download`;

  const handlePlay = useCallback(() => {
    setHasUserInteracted(true);
    setPlaying(true);
  }, []);

  const handlePause = useCallback(() => {
    setPlaying(false);
  }, []);

  const handleMute = useCallback(() => {
    setMuted(!muted);
    setHasUserInteracted(true);
  }, [muted]);

  const handleVolumeChange = useCallback((newVolume: number) => {
    setVolume(newVolume);
    setMuted(newVolume === 0);
    setHasUserInteracted(true);
  }, []);

  // Handle autoplay with user interaction requirements
  useEffect(() => {
    if (autoPlay && hasUserInteracted) {
      setPlaying(true);
    }
  }, [autoPlay, hasUserInteracted]);

  return (
    <div className={`relative ${className}`}>
      <ReactPlayer
        ref={playerRef}
        url={videoUrl}
        width="100%"
        height="100%"
        playing={playing}
        muted={muted}
        volume={volume}
        controls={false}
        onProgress={onProgress}
        config={{
          file: {
            attributes: {
              preload: 'metadata',
              crossOrigin: 'anonymous',
            }
          }
        }}
      />
      
      {showControls && (
        <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/80 to-transparent p-4">
          <div className="flex items-center gap-3">
            {/* Play/Pause Button */}
            <button
              onClick={playing ? handlePause : handlePlay}
              className="flex items-center justify-center w-10 h-10 bg-white/20 hover:bg-white/30 rounded-full transition-colors"
              aria-label={playing ? "Pause" : "Play"}
            >
              {playing ? (
                <Pause className="w-5 h-5 text-white" />
              ) : (
                <Play className="w-5 h-5 text-white ml-0.5" />
              )}
            </button>

            {/* Volume Controls */}
            <div className="flex items-center gap-2">
              <button
                onClick={handleMute}
                className="flex items-center justify-center w-8 h-8 hover:bg-white/20 rounded transition-colors"
                aria-label={muted ? "Unmute" : "Mute"}
              >
                {muted ? (
                  <VolumeX className="w-4 h-4 text-white" />
                ) : (
                  <Volume2 className="w-4 h-4 text-white" />
                )}
              </button>
              
              <input
                type="range"
                min="0"
                max="1"
                step="0.1"
                value={muted ? 0 : volume}
                onChange={(e) => handleVolumeChange(parseFloat(e.target.value))}
                className="w-16 h-1 bg-white/30 rounded-lg appearance-none cursor-pointer"
                style={{
                  background: `linear-gradient(to right, #ffffff ${(muted ? 0 : volume) * 100}%, rgba(255,255,255,0.3) ${(muted ? 0 : volume) * 100}%)`
                }}
              />
            </div>

            {/* Audio Status Indicator */}
            <div className="flex items-center gap-1 text-xs text-white/80">
              <div className={`w-2 h-2 rounded-full ${muted ? 'bg-red-500' : 'bg-green-500'}`} />
              <span>{muted ? 'Muted' : 'Audio On'}</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
} 