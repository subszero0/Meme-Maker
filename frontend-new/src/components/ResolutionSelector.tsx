import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { Settings, Zap, Monitor, Smartphone, Download, AlertCircle, Loader } from 'lucide-react';
import { VideoFormat, metadataApi } from '@/lib/api';

interface ResolutionSelectorProps {
  videoUrl: string;
  selectedFormatId?: string;
  onFormatChange: (formatId: string | undefined) => void;
}

export const ResolutionSelector: React.FC<ResolutionSelectorProps> = ({
  videoUrl,
  selectedFormatId,
  onFormatChange,
}) => {
  const [formats, setFormats] = useState<VideoFormat[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Helper functions
  const formatFileSize = useCallback((bytes?: number) => {
    if (!bytes) return 'Unknown size';
    const mb = bytes / (1024 * 1024);
    if (mb < 1) return '< 1 MB';
    if (mb < 1000) return `~${Math.round(mb)} MB`;
    const gb = mb / 1024;
    return `~${gb.toFixed(1)} GB`;
  }, []);

  const getQualityLabel = useCallback((resolution: string) => {
    // Parse resolution string (e.g., "1920x1080" or "1280x720")
    const [width, height] = resolution.split('x').map(Number);
    if (height >= 2160) return '4K';
    if (height >= 1440) return '1440p';
    if (height >= 1080) return '1080p';
    if (height >= 720) return '720p';
    if (height >= 480) return '480p';
    if (height >= 360) return '360p';
    if (height >= 240) return '240p';
    return `${height}p`;
  }, []);

  const getQualityIcon = useCallback((resolution: string) => {
    const [, height] = resolution.split('x').map(Number);
    if (height >= 1080) return <Monitor className="w-4 h-4" />;
    if (height >= 720) return <Monitor className="w-4 h-4" />;
    return <Smartphone className="w-4 h-4" />;
  }, []);

  const getQualityDescription = useCallback((resolution: string) => {
    const [, height] = resolution.split('x').map(Number);
    if (height >= 2160) return 'Ultra HD - Best quality';
    if (height >= 1440) return '2K - Excellent quality';
    if (height >= 1080) return 'Full HD - Great quality';
    if (height >= 720) return 'HD - Good quality';
    if (height >= 480) return 'SD - Standard quality';
    if (height >= 360) return 'Low - Small file';
    return 'Basic quality';
  }, []);

  // Fetch formats from API
  useEffect(() => {
    const fetchFormats = async () => {
      if (!videoUrl) return;

      console.log('🎬 ResolutionSelector: Fetching formats for:', videoUrl);
      setLoading(true);
      setError(null);

      try {
        const metadata = await metadataApi.getDetailedMetadata(videoUrl);
        console.log('🎬 ResolutionSelector: Got metadata with', metadata.formats.length, 'formats');
        
        setFormats(metadata.formats);

        // Auto-select best format if none selected
        if (!selectedFormatId && metadata.formats.length > 0) {
          // Prefer 1080p, then 720p, then highest available
          const preferredFormat = 
            metadata.formats.find(f => f.resolution.includes('1080')) ||
            metadata.formats.find(f => f.resolution.includes('720')) ||
            metadata.formats[0];
          
          if (preferredFormat) {
            console.log('🎬 ResolutionSelector: Auto-selecting format:', preferredFormat.format_id);
            onFormatChange(preferredFormat.format_id);
          }
        }
      } catch (err) {
        console.error('🎬 ResolutionSelector: Error fetching formats:', err);
        setError(err instanceof Error ? err.message : 'Failed to load resolutions');
        
        // Fallback to default formats
        const fallbackFormats: VideoFormat[] = [
          {
            format_id: '18',
            ext: 'mp4',
            resolution: '640x360',
            fps: 25,
            vcodec: 'avc1.42001E',
            acodec: 'mp4a.40.2',
            format_note: '360p'
          },
          {
            format_id: '22',
            ext: 'mp4',
            resolution: '1280x720',
            fps: 25,
            vcodec: 'avc1.64001F',
            acodec: 'mp4a.40.2',
            format_note: '720p'
          }
        ];
        
        setFormats(fallbackFormats);
        
        // Auto-select 720p fallback
        if (!selectedFormatId) {
          onFormatChange('22');
        }
      } finally {
        setLoading(false);
      }
    };

    fetchFormats();
  }, [videoUrl, selectedFormatId, onFormatChange]);

  // Group formats by quality for better organization
  const groupedFormats = useMemo(() => {
    const groups: { [key: string]: VideoFormat[] } = {};
    
    formats.forEach(format => {
      const quality = getQualityLabel(format.resolution);
      if (!groups[quality]) {
        groups[quality] = [];
      }
      groups[quality].push(format);
    });

    // Sort groups by quality (descending)
    const sortedGroups = Object.entries(groups).sort(([a], [b]) => {
      const getHeight = (label: string) => {
        if (label === '4K') return 2160;
        return parseInt(label.replace('p', '')) || 0;
      };
      return getHeight(b) - getHeight(a);
    });

    return sortedGroups;
  }, [formats, getQualityLabel]);

  const selectedFormat = formats.find(f => f.format_id === selectedFormatId);

  // Loading state
  if (loading) {
    return (
      <div className="space-y-4">
        <div className="text-center">
          <h3 className="text-xl font-bold text-gray-800 mb-2 flex items-center justify-center">
            <Settings className="w-5 h-5 mr-2 text-orange-500" />
            Output Quality
          </h3>
          <p className="text-gray-600">Loading available resolutions...</p>
        </div>
        
        <div className="flex items-center justify-center p-8">
          <div className="flex items-center space-x-3">
            <Loader className="w-6 h-6 animate-spin text-orange-500" />
            <span className="text-gray-600">Analyzing video formats...</span>
          </div>
        </div>
      </div>
    );
  }

  // Error state
  if (error && formats.length === 0) {
    return (
      <div className="space-y-4">
        <div className="text-center">
          <h3 className="text-xl font-bold text-gray-800 mb-2 flex items-center justify-center">
            <Settings className="w-5 h-5 mr-2 text-orange-500" />
            Output Quality
          </h3>
          <p className="text-gray-600">Choose your preferred resolution</p>
        </div>
        
        <div className="flex items-center gap-3 text-red-600 bg-red-50 border border-red-200 rounded-lg p-4">
          <AlertCircle className="w-5 h-5 flex-shrink-0" />
          <div>
            <p className="font-medium">Unable to load video formats</p>
            <p className="text-sm text-red-500">{error}</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="text-center">
        <h3 className="text-xl font-bold text-gray-800 mb-2 flex items-center justify-center">
          <Settings className="w-5 h-5 mr-2 text-orange-500" />
          Output Quality
        </h3>
        <p className="text-gray-600">Choose your preferred resolution</p>
        {error && (
          <p className="text-sm text-yellow-600 mt-1">Using fallback formats</p>
        )}
      </div>

      {/* Selected Format Display */}
      {selectedFormat && (
        <div className="bg-gradient-to-r from-orange-50 to-red-50 border border-orange-200 rounded-2xl p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              {getQualityIcon(selectedFormat.resolution)}
              <div>
                <p className="font-bold text-gray-800">
                  {getQualityLabel(selectedFormat.resolution)}
                </p>
                <p className="text-sm text-gray-600">
                  {selectedFormat.resolution} • {selectedFormat.ext.toUpperCase()}
                </p>
              </div>
            </div>
            <div className="text-right">
              <p className="text-sm font-medium text-gray-700">
                {formatFileSize(selectedFormat.filesize)}
              </p>
              <p className="text-xs text-gray-500">
                {selectedFormat.fps}fps
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Format Selection */}
      <div className="space-y-3 max-h-80 overflow-y-auto">
        {groupedFormats.map(([quality, qualityFormats]) => (
          <div key={quality} className="space-y-2">
            {/* Quality Group Header */}
            <div className="flex items-center space-x-2 px-2">
              <div className="text-sm font-medium text-gray-700">{quality}</div>
              <div className="flex-1 border-t border-gray-200"></div>
            </div>
            
            {/* Formats in this quality group */}
            {qualityFormats.map((format) => (
              <button
                key={format.format_id}
                onClick={() => onFormatChange(format.format_id)}
                className={`w-full p-4 rounded-2xl border-2 transition-all duration-200 text-left hover:scale-[1.02] ${
                  selectedFormatId === format.format_id
                    ? 'border-orange-400 bg-gradient-to-r from-orange-50 to-red-50 shadow-lg'
                    : 'border-gray-200 bg-white hover:border-orange-200 hover:shadow-md'
                }`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <div className={`w-3 h-3 rounded-full ${
                      selectedFormatId === format.format_id
                        ? 'bg-gradient-to-r from-orange-400 to-red-400'
                        : 'bg-gray-300'
                    }`} />
                    
                    <div className="flex items-center space-x-2">
                      {getQualityIcon(format.resolution)}
                      <div>
                        <div className="flex items-center space-x-2">
                          <span className="font-bold text-gray-800">
                            {getQualityLabel(format.resolution)}
                          </span>
                          {quality === '1080p' && (
                            <div className="flex items-center text-yellow-600">
                              <Zap className="w-4 h-4 mr-1" />
                              <span className="text-xs font-medium">Recommended</span>
                            </div>
                          )}
                        </div>
                        <p className="text-sm text-gray-600">
                          {getQualityDescription(format.resolution)}
                        </p>
                        <p className="text-xs text-gray-500">
                          {format.resolution} • {format.ext.toUpperCase()} • {format.fps}fps
                        </p>
                      </div>
                    </div>
                  </div>
                  
                  <div className="text-right">
                    <div className="flex items-center text-gray-600 mb-1">
                      <Download className="w-4 h-4 mr-1" />
                      <span className="text-sm font-medium">
                        {formatFileSize(format.filesize)}
                      </span>
                    </div>
                    <p className="text-xs text-gray-500">
                      {format.vcodec?.split('.')[0] || 'H.264'}
                    </p>
                  </div>
                </div>
              </button>
            ))}
          </div>
        ))}
      </div>

      {/* Format Info */}
      <div className="text-center">
        <p className="text-xs text-gray-500">
          {formats.length} format{formats.length !== 1 ? 's' : ''} available • 
          Format ID: {selectedFormatId || 'None selected'}
        </p>
      </div>
    </div>
  );
};
