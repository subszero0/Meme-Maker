import React, { useState, useRef, useCallback, useMemo } from 'react';
import { Scissors, AlertTriangle, CheckCircle } from 'lucide-react';

interface TimelineProps {
  duration: number;
  clipStart: number;
  clipEnd: number;
  onClipStartChange: (start: number) => void;
  onClipEndChange: (end: number) => void;
}

// Constants for validation
const MAX_CLIP_DURATION = 180; // 3 minutes in seconds
const MIN_CLIP_DURATION = 0.1; // Minimum 0.1 seconds
const SNAP_PRECISION = 0.1; // Snap to 0.1 second precision

export const Timeline: React.FC<TimelineProps> = ({
  duration,
  clipStart,
  clipEnd,
  onClipStartChange,
  onClipEndChange,
}) => {
  const [isDragging, setIsDragging] = useState<'start' | 'end' | null>(null);
  const timelineRef = useRef<HTMLDivElement>(null);

  // Format time with more precision for accurate display
  const formatTime = useCallback((seconds: number) => {
    if (seconds < 0) return '0:00';
    
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    const decimals = Math.floor((seconds % 1) * 10);
    
    return `${mins}:${secs.toString().padStart(2, '0')}.${decimals}`;
  }, []);

  // Calculate clip duration and validation
  const clipDuration = useMemo(() => clipEnd - clipStart, [clipStart, clipEnd]);
  
  const validation = useMemo(() => {
    const isValidRange = clipEnd > clipStart;
    const isMinDuration = clipDuration >= MIN_CLIP_DURATION;
    const isMaxDuration = clipDuration <= MAX_CLIP_DURATION;
    const isValidStart = clipStart >= 0 && clipStart <= duration;
    const isValidEnd = clipEnd >= 0 && clipEnd <= duration;
    
    return {
      isValid: isValidRange && isMinDuration && isMaxDuration && isValidStart && isValidEnd,
      isValidRange,
      isMinDuration,
      isMaxDuration,
      isValidStart,
      isValidEnd,
      exceedsMaxDuration: clipDuration > MAX_CLIP_DURATION,
    };
  }, [clipStart, clipEnd, clipDuration, duration]);

  // Snap time to precision
  const snapTime = useCallback((time: number) => {
    return Math.round(time / SNAP_PRECISION) * SNAP_PRECISION;
  }, []);

  const handleMouseDown = useCallback((type: 'start' | 'end') => {
    setIsDragging(type);
  }, []);

  const handleMouseMove = useCallback((e: React.MouseEvent) => {
    if (!isDragging || !timelineRef.current) return;

    const rect = timelineRef.current.getBoundingClientRect();
    const percentage = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width));
    const time = snapTime(percentage * duration);

    if (isDragging === 'start') {
      // Ensure start doesn't exceed end minus minimum duration
      const maxStart = Math.max(0, Math.min(time, clipEnd - MIN_CLIP_DURATION));
      onClipStartChange(maxStart);
    } else {
      // Ensure end doesn't go below start plus minimum duration
      const minEnd = Math.min(duration, Math.max(time, clipStart + MIN_CLIP_DURATION));
      onClipEndChange(minEnd);
    }
  }, [isDragging, duration, clipStart, clipEnd, onClipStartChange, onClipEndChange, snapTime]);

  const handleMouseUp = useCallback(() => {
    setIsDragging(null);
  }, []);

  // Handle direct timeline clicks for setting positions
  const handleTimelineClick = useCallback((e: React.MouseEvent) => {
    if (isDragging) return;
    
    const rect = timelineRef.current?.getBoundingClientRect();
    if (!rect) return;

    const percentage = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width));
    const clickedTime = snapTime(percentage * duration);

    // Determine which handle to move based on proximity
    const distanceToStart = Math.abs(clickedTime - clipStart);
    const distanceToEnd = Math.abs(clickedTime - clipEnd);

    if (distanceToStart < distanceToEnd) {
      // Move start handle
      const maxStart = Math.max(0, Math.min(clickedTime, clipEnd - MIN_CLIP_DURATION));
      onClipStartChange(maxStart);
    } else {
      // Move end handle
      const minEnd = Math.min(duration, Math.max(clickedTime, clipStart + MIN_CLIP_DURATION));
      onClipEndChange(minEnd);
    }
  }, [isDragging, duration, clipStart, clipEnd, onClipStartChange, onClipEndChange, snapTime]);

  return (
    <div className="space-y-6">
      <div className="text-center">
        <h3 className="text-xl font-bold text-gray-800 mb-2 flex items-center justify-center">
          <Scissors className="w-5 h-5 mr-2 text-orange-500" />
          Clip Timeline
        </h3>
        <p className="text-gray-600">Drag the handles to select your perfect clip</p>
        {duration > 0 && (
          <p className="text-sm text-gray-500 mt-1">
            Video Duration: {formatTime(duration)} • Max Clip: {formatTime(MAX_CLIP_DURATION)}
          </p>
        )}
      </div>

      {/* Timeline Visualization */}
      <div className="space-y-4">
        <div
          ref={timelineRef}
          className="relative h-16 bg-gradient-to-r from-gray-200 via-gray-300 to-gray-200 rounded-2xl cursor-pointer shadow-inner"
          onMouseMove={handleMouseMove}
          onMouseUp={handleMouseUp}
          onMouseLeave={handleMouseUp}
          onClick={handleTimelineClick}
        >
          {/* Selected Clip Area */}
          <div
            className={`absolute top-0 h-full rounded-2xl shadow-lg transition-colors duration-200 ${
              validation.isValid 
                ? 'bg-gradient-to-r from-orange-400 to-red-400 opacity-80' 
                : 'bg-gradient-to-r from-red-500 to-red-600 opacity-90'
            }`}
            style={{
              left: `${(clipStart / duration) * 100}%`,
              width: `${((clipEnd - clipStart) / duration) * 100}%`,
            }}
          />

          {/* Start Handle */}
          <div
            className={`absolute top-1/2 transform -translate-y-1/2 w-6 h-12 bg-white rounded-lg shadow-lg cursor-grab active:cursor-grabbing border-2 hover:scale-110 transition-transform duration-200 ${
              validation.isValidStart ? 'border-orange-400' : 'border-red-500'
            }`}
            style={{ left: `${(clipStart / duration) * 100}%`, marginLeft: '-12px' }}
            onMouseDown={() => handleMouseDown('start')}
          >
            <div className={`w-full h-full rounded-md flex items-center justify-center ${
              validation.isValidStart 
                ? 'bg-gradient-to-b from-orange-400 to-red-400' 
                : 'bg-gradient-to-b from-red-500 to-red-600'
            }`}>
              <div className="w-1 h-6 bg-white rounded-full" />
            </div>
          </div>

          {/* End Handle */}
          <div
            className={`absolute top-1/2 transform -translate-y-1/2 w-6 h-12 bg-white rounded-lg shadow-lg cursor-grab active:cursor-grabbing border-2 hover:scale-110 transition-transform duration-200 ${
              validation.isValidEnd ? 'border-red-400' : 'border-red-500'
            }`}
            style={{ left: `${(clipEnd / duration) * 100}%`, marginLeft: '-12px' }}
            onMouseDown={() => handleMouseDown('end')}
          >
            <div className={`w-full h-full rounded-md flex items-center justify-center ${
              validation.isValidEnd 
                ? 'bg-gradient-to-b from-orange-400 to-red-400' 
                : 'bg-gradient-to-b from-red-500 to-red-600'
            }`}>
              <div className="w-1 h-6 bg-white rounded-full" />
            </div>
          </div>

          {/* Time Markers */}
          <div className="absolute -bottom-8 left-0 right-0 flex justify-between text-xs text-gray-500">
            <span>0:00</span>
            <span>{formatTime(duration)}</span>
          </div>
        </div>

        {/* Validation Messages */}
        {!validation.isValid && (
          <div className="space-y-2">
            {!validation.isValidRange && (
              <div className="flex items-center gap-2 text-red-600 text-sm bg-red-50 border border-red-200 rounded-lg p-3">
                <AlertTriangle className="w-4 h-4 flex-shrink-0" />
                <span>End time must be after start time</span>
              </div>
            )}
            {validation.exceedsMaxDuration && (
              <div className="flex items-center gap-2 text-red-600 text-sm bg-red-50 border border-red-200 rounded-lg p-3">
                <AlertTriangle className="w-4 h-4 flex-shrink-0" />
                <span>Clip duration cannot exceed {formatTime(MAX_CLIP_DURATION)} (3 minutes)</span>
              </div>
            )}
            {(!validation.isValidStart || !validation.isValidEnd) && (
              <div className="flex items-center gap-2 text-red-600 text-sm bg-red-50 border border-red-200 rounded-lg p-3">
                <AlertTriangle className="w-4 h-4 flex-shrink-0" />
                <span>Clip times must be within video duration</span>
              </div>
            )}
          </div>
        )}

        {/* Success Message */}
        {validation.isValid && (
          <div className="flex items-center gap-2 text-green-600 text-sm bg-green-50 border border-green-200 rounded-lg p-3">
            <CheckCircle className="w-4 h-4 flex-shrink-0" />
            <span>Clip selection is valid and ready for processing</span>
          </div>
        )}

        {/* Clip Information */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className={`p-4 rounded-2xl text-center border transition-colors duration-200 ${
            validation.isValidStart 
              ? 'bg-orange-50 border-orange-200' 
              : 'bg-red-50 border-red-200'
          }`}>
            <p className="text-sm text-gray-600 mb-1">Clip Start</p>
            <p className={`text-lg font-bold ${
              validation.isValidStart ? 'text-orange-600' : 'text-red-600'
            }`}>
              {formatTime(clipStart)}
            </p>
          </div>
          
          <div className={`p-4 rounded-2xl text-center border transition-colors duration-200 ${
            validation.isMaxDuration 
              ? 'bg-blue-50 border-blue-200' 
              : 'bg-red-50 border-red-200'
          }`}>
            <p className="text-sm text-gray-600 mb-1">Clip Duration</p>
            <p className={`text-lg font-bold ${
              validation.isMaxDuration ? 'text-blue-600' : 'text-red-600'
            }`}>
              {formatTime(clipDuration)}
            </p>
            {validation.exceedsMaxDuration && (
              <p className="text-xs text-red-500 mt-1">
                Exceeds {formatTime(MAX_CLIP_DURATION)} limit
              </p>
            )}
          </div>
          
          <div className={`p-4 rounded-2xl text-center border transition-colors duration-200 ${
            validation.isValidEnd 
              ? 'bg-yellow-50 border-yellow-200' 
              : 'bg-red-50 border-red-200'
          }`}>
            <p className="text-sm text-gray-600 mb-1">Clip End</p>
            <p className={`text-lg font-bold ${
              validation.isValidEnd ? 'text-yellow-600' : 'text-red-600'
            }`}>
              {formatTime(clipEnd)}
            </p>
          </div>
        </div>

        {/* Precision Info */}
        <div className="text-center">
          <p className="text-xs text-gray-500">
            Precision: {SNAP_PRECISION}s • Click timeline to quickly position handles
          </p>
        </div>
      </div>
    </div>
  );
};
