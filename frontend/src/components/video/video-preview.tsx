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
  const [loadError, setLoadError] = useState<string | null>(null);

  console.log(`[VideoPreview] Rendering video preview for URL: ${url}`);
  console.log(`[VideoPreview] Playing: ${playing}, Muted: ${muted}`);
  console.log(
    `[VideoPreview] Current origin: ${typeof window !== "undefined" ? window.location.origin : "SSR"}`,
  );

  if (embedError) {
    console.log(`[VideoPreview] Displaying fallback UI due to embed error`);
    return (
      <div
        className={`relative ${className} bg-gray-100 flex items-center justify-center`}
      >
        <div className="text-center p-4">
          <div className="mb-4">
            <svg
              className="w-12 h-12 mx-auto text-gray-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z"
              />
            </svg>
          </div>
          <p className="text-gray-600 mb-2">Video preview unavailable</p>
          {loadError && (
            <p className="text-sm text-gray-500 mb-4">Error: {loadError}</p>
          )}
          <a
            href={url}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 transition-colors"
          >
            <svg
              className="w-4 h-4 mr-2"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"
              />
            </svg>
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
        onReady={() => {
          console.log(`[VideoPreview] ReactPlayer ready for URL: ${url}`);
        }}
        onStart={() => {
          console.log(`[VideoPreview] ReactPlayer started for URL: ${url}`);
        }}
        onError={(error) => {
          console.error(
            `[VideoPreview] ReactPlayer error for URL ${url}:`,
            error,
          );
          console.error(`[VideoPreview] Error type:`, typeof error);
          console.error(`[VideoPreview] Error details:`, error);

          const errorMessage =
            error instanceof Error ? error.message : String(error);
          setLoadError(errorMessage);
          setEmbedError(true);
        }}
        onBuffer={() => {
          console.log(`[VideoPreview] ReactPlayer buffering for URL: ${url}`);
        }}
        config={{
          youtube: {
            playerVars: {
              showinfo: 1,
              modestbranding: 1,
              rel: 0,
              iv_load_policy: 3,
              fs: 0,
              disablekb: 1,
              origin:
                typeof window !== "undefined"
                  ? window.location.origin
                  : undefined,
            },
          },
        }}
      />
    </div>
  );
}
