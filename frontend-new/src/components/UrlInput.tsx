import React, { useState } from "react";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Link2, Loader2, AlertCircle } from "lucide-react";
import { useVideoMetadata } from "../hooks/useApi";
import { useDebounce } from "use-debounce";
import type { MetadataResponse } from "@/lib/api";

interface UrlInputProps {
  onSubmit: (url: string, metadata: MetadataResponse) => void;
}

export const UrlInput: React.FC<UrlInputProps> = ({ onSubmit }) => {
  const [url, setUrl] = useState("");
  const [submittedUrl, setSubmittedUrl] = useState("");
  const [validationError, setValidationError] = useState("");

  // Debounce URL for validation
  const [debouncedUrl] = useDebounce(url, 500);

  // Fetch metadata when URL is valid
  const {
    data: metadata,
    isLoading,
    error: metadataError,
    isError,
  } = useVideoMetadata(submittedUrl, !!submittedUrl && !validationError);

  const validateUrl = (inputUrl: string): boolean => {
    if (!inputUrl.trim()) {
      setValidationError("");
      return false;
    }

    try {
      const urlObj = new URL(inputUrl);
      const supportedDomains = [
        "youtube.com",
        "youtu.be",
        "facebook.com",
        "fb.watch",
        "instagram.com",
        "threads.net",
        "whatsapp.com",
      ];

      const isSupported = supportedDomains.some((domain) =>
        urlObj.hostname.includes(domain),
      );

      if (!isSupported) {
        setValidationError(
          "Please enter a valid URL from YouTube, Instagram, Facebook, WhatsApp, or Threads",
        );
        return false;
      }

      setValidationError("");
      return true;
    } catch {
      setValidationError("Please enter a valid URL");
      return false;
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const trimmedUrl = url.trim();

    if (!trimmedUrl) {
      setValidationError("Please enter a video URL");
      return;
    }

    if (validateUrl(trimmedUrl)) {
      setSubmittedUrl(trimmedUrl);
    }
  };

  // Handle successful metadata fetch
  React.useEffect(() => {
    if (metadata && submittedUrl) {
      onSubmit(submittedUrl, metadata);
    }
  }, [metadata, submittedUrl, onSubmit]);

  return (
    <div className="space-y-4">
      <div className="text-center">
        <h2 className="text-2xl font-bold text-gray-800 mb-2">
          Start Your Creative Journey
        </h2>
        <p className="text-gray-600">
          Paste any video link from YouTube, Instagram, Facebook, WhatsApp, or
          Threads
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="relative">
          <input
            type="url"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="https://youtube.com/watch?v=... or any video URL"
            className={`w-full p-4 pr-12 border-2 rounded-2xl focus:ring-4 focus:ring-orange-100 outline-none text-lg bg-orange-50/30 transition-colors ${
              validationError
                ? "border-red-300 focus:border-red-400"
                : "border-orange-200 focus:border-orange-400"
            }`}
            disabled={isLoading}
          />
          {isLoading ? (
            <Loader2 className="absolute right-4 top-1/2 transform -translate-y-1/2 text-orange-400 w-6 h-6 animate-spin" />
          ) : (
            <Link2 className="absolute right-4 top-1/2 transform -translate-y-1/2 text-orange-400 w-6 h-6" />
          )}
        </div>

        {/* Validation Error */}
        {validationError && (
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>{validationError}</AlertDescription>
          </Alert>
        )}

        {/* API Error */}
        {isError && metadataError && (
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>
              {metadataError instanceof Error && metadataError.message
                ? metadataError.message.includes("Sign in to confirm")
                  ? "YouTube is temporarily blocking automated requests. Please try again in a few minutes or try a different video."
                  : metadataError.message.includes(
                        "Failed to extract video metadata",
                      )
                    ? metadataError.message.replace(
                        "Failed to extract video metadata: ",
                        "",
                      )
                    : metadataError.message
                : "Failed to fetch video information. Please check the URL and try again."}
            </AlertDescription>
          </Alert>
        )}

        <Button
          type="submit"
          disabled={isLoading || !!validationError}
          className="w-full bg-gradient-to-r from-orange-400 to-red-400 hover:from-orange-500 hover:to-red-500 text-white font-bold py-4 px-8 rounded-2xl shadow-lg hover:shadow-xl transform hover:scale-105 transition-all duration-200 text-lg disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none"
        >
          {isLoading ? (
            <>
              <Loader2 className="w-5 h-5 mr-2 animate-spin" />
              Fetching Video...
            </>
          ) : (
            "🚀 Let's Go!"
          )}
        </Button>
      </form>
    </div>
  );
};
