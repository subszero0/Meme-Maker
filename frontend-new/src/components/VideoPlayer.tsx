import React, { useState, useRef, useEffect, useMemo } from "react";
import ReactPlayer from "react-player";
import {
  Play,
  Pause,
  SkipBack,
  SkipForward,
  Maximize2,
  Volume2,
  AlertCircle,
} from "lucide-react";
import { Alert, AlertDescription } from "./ui/alert";
import { formatDuration } from "../lib/api";
import type { VideoMetadata } from "@/types/metadata";

interface VideoPlayerProps {
  videoUrl: string;
  metadata?: VideoMetadata;
  onDurationChange: (duration: number) => void;
  onCurrentTimeChange?: (time: number) => void;
}

export const VideoPlayer: React.FC<VideoPlayerProps> = ({
  videoUrl,
  metadata,
  onDurationChange,
  onCurrentTimeChange,
}) => {
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [volume, setVolume] = useState(0.8);
  const [showControls, setShowControls] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isReady, setIsReady] = useState(false);
  const playerRef = useRef<ReactPlayer>(null);
  const audioRef = useRef<ReactPlayer>(null);

  // Determine audio URL if available (audio-only format)
  const audioUrl = useMemo(() => {
    if (!metadata?.formats) return null;

    // If any of the reported formats already contains both video *and* audio we
    // don't need a separate audio track – using one would cause double audio.
    const hasMerged = metadata.formats.some(
      (f) => f.vcodec !== "none" && f.acodec !== "none",
    );
    if (hasMerged) return null;

    // Otherwise look for a dedicated audio-only stream (common for Facebook DASH)
    const audioFormat = metadata.formats.find(
      (f) =>
        f.acodec !== "none" && f.vcodec === "none" && f.url?.startsWith("http"),
    );
    if (!audioFormat?.url) return null;

    const apiBase = import.meta.env.DEV ? "http://localhost:8000" : "";
    const u = `${apiBase}/api/v1/video/proxy?url=${encodeURIComponent(
      audioFormat.url,
    )}`;
    console.log("Audio URL selected:", u);
    return u;
  }, [metadata]);

  useEffect(() => {
    console.log("VideoPlayer: URL received:", videoUrl);
    setIsReady(false);
    setError(null);
  }, [videoUrl]);

  // Sync audio player with video player
  useEffect(() => {
    if (!audioUrl || !audioRef.current || !playerRef.current) return;

    if (isPlaying) {
      audioRef.current.seekTo(currentTime, "seconds");
    }
  }, [currentTime, isPlaying, audioUrl]);

  // Initialize duration from metadata
  useEffect(() => {
    if (metadata?.duration) {
      setDuration(metadata.duration);
      onDurationChange(metadata.duration);
    }
  }, [metadata, onDurationChange]);

  // Update parent component with current time
  useEffect(() => {
    if (onCurrentTimeChange) {
      onCurrentTimeChange(currentTime);
    }
  }, [currentTime, onCurrentTimeChange]);

  const togglePlay = () => {
    console.log(
      `VideoPlayer: togglePlay called. Current state: isPlaying=${isPlaying}, isReady=${isReady}`,
    );
    if (isReady) {
      setIsPlaying(!isPlaying);
      if (audioUrl && audioRef.current) {
        // Toggle audio playback in sync
        if (isPlaying) {
          audioRef.current.getInternalPlayer()?.pause?.();
        } else {
          audioRef.current.getInternalPlayer()?.play?.();
        }
      }
    } else {
      console.warn("VideoPlayer: Tried to play but player is not ready.");
    }
  };

  const skipSeconds = (seconds: number) => {
    if (playerRef.current) {
      const newTime = Math.max(0, Math.min(duration, currentTime + seconds));
      playerRef.current.seekTo(newTime, "seconds");
      setCurrentTime(newTime);
    }
  };

  const handleSeek = (time: number) => {
    if (playerRef.current) {
      playerRef.current.seekTo(time, "seconds");
      setCurrentTime(time);
    }
  };

  const handleProgress = (state: { played: number; playedSeconds: number }) => {
    setCurrentTime(state.playedSeconds);
  };

  const handleDuration = (duration: number) => {
    setDuration(duration);
    onDurationChange(duration);
  };

  const handleReady = () => {
    console.log("VideoPlayer: onReady event fired. Player is ready to play.");
    setIsReady(true);
    setError(null);
  };

  const handleError = (e: unknown) => {
    console.error("VideoPlayer: onError event fired.", e);
    let errorMessage = "Failed to load video.";
    if (
      typeof e === "object" &&
      e !== null &&
      "message" in e &&
      typeof e.message === "string"
    ) {
      errorMessage = e.message;
    } else if (typeof e === "string") {
      errorMessage = e;
    }
    setError(`Video Error: ${errorMessage}`);
    setIsReady(false);
  };

  const handlePlay = () => {
    console.log("VideoPlayer: onPlay event fired. Playback has started.");
    setIsPlaying(true);
  };

  const handlePause = () => {
    console.log("VideoPlayer: onPause event fired. Playback has paused.");
    setIsPlaying(false);
  };

  return (
    <div className="relative bg-black rounded-2xl overflow-hidden aspect-video">
      {/* Error Display */}
      {error && (
        <div className="absolute inset-0 z-10 flex items-center justify-center bg-black/80 backdrop-blur-sm">
          <Alert variant="destructive" className="max-w-md">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        </div>
      )}

      {/* Video Thumbnail (before ready) */}
      {!isReady && metadata?.thumbnail && (
        <div
          className="absolute inset-0 bg-cover bg-center"
          style={{ backgroundImage: `url(${metadata.thumbnail})` }}
        >
          <div className="absolute inset-0 bg-black/30" />
        </div>
      )}

      {/* ReactPlayer */}
      <ReactPlayer
        ref={playerRef}
        url={videoUrl}
        width="100%"
        height="100%"
        playing={isPlaying}
        volume={audioUrl ? 0 : volume} // Mute main player when external audio is used
        muted={!!audioUrl}
        onReady={handleReady}
        onPlay={handlePlay}
        onPause={handlePause}
        onDuration={handleDuration}
        onProgress={handleProgress}
        onError={handleError}
        config={{
          youtube: {
            playerVars: { showinfo: 0, controls: 0, modestbranding: 1 },
          },
          file: {
            attributes: {
              crossOrigin: "anonymous",
              preload: "metadata",
            },
            tracks: [],
            forceHLS: false,
            forceVideo: true,
          },
        }}
      />

      {/* Hidden Audio Player for DASH video-only streams */}
      {audioUrl && (
        <ReactPlayer
          ref={audioRef}
          url={audioUrl}
          playing={isPlaying}
          volume={volume}
          width={0}
          height={0}
          style={{ display: "none" }}
          config={{ file: { forceAudio: true } }}
          onReady={() => console.log("AudioPlayer ready", audioUrl)}
          onError={(e) => console.error("AudioPlayer error", e)}
        />
      )}

      {/* Video Controls Overlay */}
      {showControls && isReady && (
        <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent">
          {/* Center Play Button */}
          <div className="absolute inset-0 flex items-center justify-center">
            <button
              onClick={togglePlay}
              className="w-16 h-16 md:w-20 md:h-20 bg-white/20 backdrop-blur-sm rounded-full flex items-center justify-center hover:bg-white/30 transition-all duration-200 hover:scale-110"
            >
              {isPlaying ? (
                <Pause className="w-6 h-6 md:w-8 md:h-8 text-white" />
              ) : (
                <Play className="w-6 h-6 md:w-8 md:h-8 text-white ml-1" />
              )}
            </button>
          </div>

          {/* Video Info Overlay */}
          {metadata && (
            <div className="absolute top-4 left-4 right-4">
              <h3 className="text-white font-semibold text-lg truncate">
                {metadata.title}
              </h3>
              <p className="text-white/80 text-sm">
                Duration: {formatDuration(metadata.duration)}
              </p>
            </div>
          )}

          {/* Bottom Controls */}
          <div className="absolute bottom-0 left-0 right-0 p-4 space-y-3">
            {/* Progress Bar */}
            <div className="w-full">
              <div
                className="relative h-2 bg-white/20 rounded-full cursor-pointer"
                onClick={(e) => {
                  const rect = e.currentTarget.getBoundingClientRect();
                  const percent = (e.clientX - rect.left) / rect.width;
                  const newTime = percent * duration;
                  handleSeek(newTime);
                }}
              >
                <div
                  className="absolute h-full bg-gradient-to-r from-orange-400 to-red-400 rounded-full transition-all duration-300"
                  style={{ width: `${(currentTime / duration) * 100}%` }}
                />
                <div
                  className="absolute w-4 h-4 bg-white rounded-full shadow-lg top-1/2 transform -translate-y-1/2 transition-all duration-300"
                  style={{ left: `${(currentTime / duration) * 100}%` }}
                />
              </div>
            </div>

            {/* Control Buttons */}
            <div className="flex items-center justify-between text-white">
              <div className="flex items-center space-x-3">
                <button
                  onClick={() => skipSeconds(-10)}
                  className="p-2 hover:bg-white/20 rounded-full transition-all duration-200"
                >
                  <SkipBack className="w-5 h-5" />
                </button>

                <button
                  onClick={togglePlay}
                  className="p-2 hover:bg-white/20 rounded-full transition-all duration-200"
                >
                  {isPlaying ? (
                    <Pause className="w-5 h-5" />
                  ) : (
                    <Play className="w-5 h-5" />
                  )}
                </button>

                <button
                  onClick={() => skipSeconds(10)}
                  className="p-2 hover:bg-white/20 rounded-full transition-all duration-200"
                >
                  <SkipForward className="w-5 h-5" />
                </button>

                <span className="text-sm font-medium">
                  {formatDuration(currentTime)} / {formatDuration(duration)}
                </span>
              </div>

              <div className="flex items-center space-x-2">
                <Volume2 className="w-4 h-4" />
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.05"
                  value={volume}
                  onChange={(e) => setVolume(parseFloat(e.target.value))}
                  className="w-16 h-1 bg-white/20 rounded-lg appearance-none slider"
                />
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
