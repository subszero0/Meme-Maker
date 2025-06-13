'use client';

import { useState, useEffect } from 'react';

interface VideoFormat {
  format_id: string;
  ext: string;
  resolution: string;
  filesize?: number;
  fps?: number;
  vcodec: string;
  acodec: string;
  format_note: string;
}

interface ResolutionSelectorProps {
  url: string;
  selectedFormatId?: string;
  onFormatChange: (formatId: string | undefined) => void;
}

export default function ResolutionSelector({ url, selectedFormatId, onFormatChange }: ResolutionSelectorProps) {
  const [formats, setFormats] = useState<VideoFormat[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isOpen, setIsOpen] = useState(false);

  useEffect(() => {
    const fetchFormats = async () => {
      setLoading(true);
      setError(null);
      
      try {
        const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/metadata/extract`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ url }),
        });

        if (!response.ok) {
          throw new Error('Failed to fetch video formats');
        }

        const data = await response.json();
        setFormats(data.formats || []);
        
        // Auto-select best quality if no format selected
        if (!selectedFormatId && data.formats && data.formats.length > 0) {
          onFormatChange(data.formats[0].format_id);
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load resolutions');
        console.error('Failed to fetch video formats:', err);
      } finally {
        setLoading(false);
      }
    };

    if (url) {
      fetchFormats();
    }
  }, [url, selectedFormatId, onFormatChange]);

  const selectedFormat = formats.find(f => f.format_id === selectedFormatId);

  const formatFileSize = (bytes?: number) => {
    if (!bytes) return '';
    const mb = bytes / (1024 * 1024);
    return mb < 1 ? '< 1 MB' : `~${Math.round(mb)} MB`;
  };

  const getQualityLabel = (resolution: string) => {
    const [width, height] = resolution.split('x').map(Number);
    if (height >= 2160) return '4K';
    if (height >= 1440) return '1440p';
    if (height >= 1080) return '1080p';
    if (height >= 720) return '720p';
    if (height >= 480) return '480p';
    if (height >= 360) return '360p';
    return `${height}p`;
  };

  if (loading) {
    return (
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Resolution
        </label>
        <div className="w-full p-3 border border-gray-300 rounded-md bg-gray-50">
          <div className="flex items-center space-x-2">
            <div className="animate-spin h-4 w-4 border-2 border-blue-600 border-t-transparent rounded-full"></div>
            <span className="text-sm text-gray-600">Loading resolutions...</span>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Resolution
        </label>
        <div className="w-full p-3 border border-red-300 rounded-md bg-red-50">
          <span className="text-sm text-red-600">{error}</span>
        </div>
      </div>
    );
  }

  if (formats.length === 0) {
    return (
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Resolution
        </label>
        <div className="w-full p-3 border border-gray-300 rounded-md bg-gray-50">
          <span className="text-sm text-gray-600">No resolutions available</span>
        </div>
      </div>
    );
  }

  return (
    <div className="relative">
      <label className="block text-sm font-medium text-gray-700 mb-2">
        Resolution
      </label>
      <div className="relative">
        <button
          type="button"
          className="w-full bg-white border border-gray-300 rounded-md pl-3 pr-10 py-2 text-left cursor-default focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
          onClick={() => setIsOpen(!isOpen)}
        >
          <span className="block truncate">
            {selectedFormat ? (
              <span className="flex items-center justify-between">
                <span>
                  <strong>{getQualityLabel(selectedFormat.resolution)}</strong> ({selectedFormat.resolution})
                </span>
                <span className="text-gray-500 text-xs ml-2">
                  {formatFileSize(selectedFormat.filesize)}
                </span>
              </span>
            ) : (
              'Select resolution'
            )}
          </span>
          <span className="absolute inset-y-0 right-0 flex items-center pr-2 pointer-events-none">
            <svg className="h-5 w-5 text-gray-400" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clipRule="evenodd" />
            </svg>
          </span>
        </button>

        {isOpen && (
          <div className="absolute z-10 mt-1 w-full bg-white shadow-lg max-h-60 rounded-md py-1 text-base ring-1 ring-black ring-opacity-5 overflow-auto focus:outline-none sm:text-sm">
            {formats.map((format) => (
              <div
                key={format.format_id}
                className={`cursor-pointer select-none relative py-2 pl-3 pr-9 hover:bg-blue-50 ${
                  selectedFormatId === format.format_id ? 'bg-blue-100 text-blue-900' : 'text-gray-900'
                }`}
                onClick={() => {
                  onFormatChange(format.format_id);
                  setIsOpen(false);
                }}
              >
                <div className="flex items-center justify-between">
                  <div className="flex flex-col">
                    <span className={`font-medium ${selectedFormatId === format.format_id ? 'text-blue-900' : 'text-gray-900'}`}>
                      {getQualityLabel(format.resolution)} ({format.resolution})
                    </span>
                    <span className="text-xs text-gray-500">
                      {format.vcodec} • {format.fps ? `${format.fps}fps` : 'Variable fps'}
                    </span>
                  </div>
                  <span className="text-xs text-gray-500">
                    {formatFileSize(format.filesize)}
                  </span>
                </div>
                {selectedFormatId === format.format_id && (
                  <span className="absolute inset-y-0 right-0 flex items-center pr-4">
                    <svg className="h-5 w-5 text-blue-600" viewBox="0 0 20 20" fill="currentColor">
                      <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                    </svg>
                  </span>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
      <p className="mt-1 text-xs text-gray-500">
        Higher resolutions may take longer to process
      </p>
    </div>
  );
} 