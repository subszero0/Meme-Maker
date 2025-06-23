"use client";

import { useState, useEffect, useCallback } from "react";
import { en } from "@/i18n/en";
import getPlatform, { Platform } from "@/lib/getPlatform";

interface URLInputPanelProps {
  onSubmit: (url: string) => void;
  loading?: boolean;
}

type ComponentPlatform = Exclude<Platform, "unknown"> | null;

const PLATFORM_ICONS = {
  youtube: "🎬",
  instagram: "📷",
  facebook: "👥",
  threads: "🧵",
  reddit: "🔗",
};

const detectPlatform = (url: string): ComponentPlatform => {
  const platform = getPlatform(url);
  return platform === "unknown" ? null : platform;
};

const isValidUrl = (url: string): boolean => {
  if (!url.trim()) return false;

  try {
    new URL(url);
    return detectPlatform(url) !== null;
  } catch {
    return false;
  }
};

export default function URLInputPanel({
  onSubmit,
  loading = false,
}: URLInputPanelProps) {
  const [url, setUrl] = useState("");
  const [error, setError] = useState("");
  const [platform, setPlatform] = useState<ComponentPlatform>(null);
  const [isDebouncing, setIsDebouncing] = useState(false);

  const validateUrl = useCallback((inputUrl: string) => {
    if (!inputUrl.trim()) {
      setError(en.urlInputPanel.errors.required);
      setPlatform(null);
      return;
    }

    const detectedPlatform = detectPlatform(inputUrl);
    setPlatform(detectedPlatform);

    if (!isValidUrl(inputUrl)) {
      setError(en.urlInputPanel.errors.invalid);
    } else {
      setError("");
    }
  }, []);

  useEffect(() => {
    setIsDebouncing(true);
    const timeoutId = setTimeout(() => {
      validateUrl(url);
      setIsDebouncing(false);
    }, 300);

    return () => clearTimeout(timeoutId);
  }, [url, validateUrl]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    if (!url.trim()) {
      setError(en.urlInputPanel.errors.required);
      return;
    }

    if (!isValidUrl(url)) {
      setError(en.urlInputPanel.errors.invalid);
      return;
    }

    onSubmit(url.trim());
  };

  const hasError = !!error && !isDebouncing;

  return (
    <div className="mx-auto max-w-md">
      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        <div>
          <label
            htmlFor="video-url"
            className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2"
          >
            {en.urlInputPanel.labels.videoUrl}
          </label>
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <span className="text-gray-400 text-sm">
                {platform && platform in PLATFORM_ICONS
                  ? PLATFORM_ICONS[platform]
                  : "🌐"}
              </span>
            </div>
            <input
              id="video-url"
              type="url"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder={en.urlInputPanel.placeholder}
              aria-invalid={hasError}
              aria-describedby={hasError ? "url-error" : undefined}
              data-testid="url-input"
              className={`
                block w-full pl-10 pr-3 py-2 border rounded-md shadow-sm
                placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-indigo-500
                ${
                  hasError
                    ? "border-red-300 focus:border-red-500 focus:ring-red-500"
                    : "border-gray-300 focus:border-indigo-500"
                }
                dark:bg-gray-800 dark:border-gray-600 dark:text-white
                dark:placeholder-gray-400 dark:focus:border-indigo-400
              `}
            />
          </div>
          {hasError && (
            <p
              id="url-error"
              className="mt-1 text-sm text-red-600 dark:text-red-400"
              data-testid="url-error"
            >
              {error}
            </p>
          )}
        </div>

        <button
          type="submit"
          disabled={!url.trim() || hasError || loading}
          data-testid="start-button"
          className="
            w-full py-2 px-4 border border-transparent rounded-md shadow-sm
            text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700
            focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500
            disabled:opacity-50 disabled:cursor-not-allowed
            transition-colors duration-200
          "
        >
          {loading ? "Loading..." : en.urlInputPanel.startButton}
        </button>
      </form>
    </div>
  );
}
