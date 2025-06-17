'use client';

import dynamic from 'next/dynamic';

// Dynamically import ReactPlayer to avoid SSR issues
const ReactPlayer = dynamic(() => import('react-player/lazy'), {
  ssr: false,
  loading: () => <div className="w-full h-64 bg-gray-200 animate-pulse rounded-lg" />
});

interface VideoPreviewProps {
  url: string;
  onProgress?: (state: { played: number; loaded: number; playedSeconds: number; loadedSeconds: number }) => void;
  playing?: boolean;
  muted?: boolean;
  className?: string;
}

export default function VideoPreview({ 
  url, 
  onProgress, 
  playing = false, 
  muted = true,
  className = "w-full h-64" 
}: VideoPreviewProps) {
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
        config={{
          youtube: {
            playerVars: { showinfo: 1 }
          }
        }}
      />
    </div>
  );
} 