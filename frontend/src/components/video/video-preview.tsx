"use client";

import { useState } from "react";
import dynamic from "next/dynamic";

// Dynamically import ReactPlayer to avoid SSR issues
const ReactPlayer = dynamic(() => import("react-player/lazy"), {
  ssr: false,
  loading: () => (
    <div className="w-full h-64 bg-gray-200 animate-pulse rounded-lg" />
  ),
});

interface VideoPreviewProps {
  url: string;
  onProgress?: (state: {
    played: number;
    loaded: number;
    playedSeconds: number;
    loadedSeconds: number;
  }) => void;
  playing?: boolean;
  muted?: boolean;
  className?: string;
}

export default function VideoPreview({
  url,
  onProgress,
  playing = false,
  muted = true,
  className = "w-full h-64",
}: VideoPreviewProps) {
  const [embedError, setEmbedError] = useState(false);
  
  if (embedError) {
    return (
      <div className={`relative ${className} bg-gray-100 flex items-center justify-center`}>
        <div className="text-center">
          <p className="text-gray-600 mb-4">Video preview unavailable</p>
          <a 
            href={url} 
            target="_blank" 
            rel="noopener noreferrer"
            className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
          >
            Watch on YouTube
          </a>
        </div>
      </div>
    );
  }

  return (
    <div className={`relative ${className}`}>
      <ReactPlayer
        url={url}
        width="100%"
        height="100%"
        playing={playing}
        muted={muted}
        controls={false}
        onProgress={onProgress}
        onError={(error) => {
          console.error('ReactPlayer error:', error);
          setEmbedError(true);
        }}
        config={{
          youtube: {
            playerVars: { 
              showinfo: 1,
              origin: typeof window !== 'undefined' ? window.location.origin : undefined
            },
          },
        }}
      />
    </div>
  );
}
