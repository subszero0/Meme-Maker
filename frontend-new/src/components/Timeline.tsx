import React, { useState, useRef, useCallback, useMemo } from "react";
import { Scissors, AlertTriangle, CheckCircle } from "lucide-react";

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
  const [isDragging, setIsDragging] = useState<"start" | "end" | null>(null);
  const [clipStartInput, setClipStartInput] = useState("");
  const [clipEndInput, setClipEndInput] = useState("");
  const [clipDurationInput, setClipDurationInput] = useState("");
  const timelineRef = useRef<HTMLDivElement>(null);

  // Format time with more precision for accurate display
  const formatTime = useCallback((seconds: number) => {
    if (seconds < 0) return "0:00.0";

    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    const decimals = Math.floor((seconds % 1) * 10);

    return `${mins}:${secs.toString().padStart(2, "0")}.${decimals}`;
  }, []);

  // Parse time string back to seconds
  const parseTime = useCallback((timeStr: string): number | null => {
    // Handle formats: MM:SS.D, MM:SS, SS.D, SS
    const patterns = [
      /^(\d+):(\d{1,2})\.(\d)$/, // MM:SS.D
      /^(\d+):(\d{1,2})$/, // MM:SS
      /^(\d{1,2})\.(\d)$/, // SS.D
      /^(\d+)$/, // SS
    ];

    for (const pattern of patterns) {
      const match = timeStr.match(pattern);
      if (match) {
        if (match.length === 4) {
          // MM:SS.D
          const minutes = parseInt(match[1]);
          const seconds = parseInt(match[2]);
          const decimals = parseInt(match[3]);
          return minutes * 60 + seconds + decimals / 10;
        } else if (match.length === 3 && timeStr.includes(":")) {
          // MM:SS
          const minutes = parseInt(match[1]);
          const seconds = parseInt(match[2]);
          return minutes * 60 + seconds;
        } else if (match.length === 3 && timeStr.includes(".")) {
          // SS.D
          const seconds = parseInt(match[1]);
          const decimals = parseInt(match[2]);
          return seconds + decimals / 10;
        } else if (match.length === 2) {
          // SS
          return parseInt(match[1]);
        }
      }
    }
    return null;
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
      isValid:
        isValidRange &&
        isMinDuration &&
        isMaxDuration &&
        isValidStart &&
        isValidEnd,
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

  // Get position from mouse or touch event
  const getPositionFromEvent = useCallback(
    (e: React.MouseEvent | React.TouchEvent) => {
      const rect = timelineRef.current?.getBoundingClientRect();
      if (!rect) return null;

      let clientX: number;
      if ("touches" in e) {
        // Touch event
        if (e.touches.length === 0) {
          // Use changedTouches for touchend events
          clientX = e.changedTouches[0]?.clientX || 0;
        } else {
          clientX = e.touches[0].clientX;
        }
      } else {
        // Mouse event
        clientX = e.clientX;
      }

      const percentage = Math.max(
        0,
        Math.min(1, (clientX - rect.left) / rect.width),
      );
      return snapTime(percentage * duration);
    },
    [duration, snapTime],
  );

  const handleStart = useCallback((type: "start" | "end") => {
    setIsDragging(type);
  }, []);

  const handleMove = useCallback(
    (e: React.MouseEvent | React.TouchEvent) => {
      if (!isDragging) return;

      e.preventDefault(); // Prevent scrolling on touch devices

      const time = getPositionFromEvent(e);
      if (time === null) return;

      if (isDragging === "start") {
        // Ensure start doesn't exceed end minus minimum duration
        const maxStart = Math.max(
          0,
          Math.min(time, clipEnd - MIN_CLIP_DURATION),
        );
        onClipStartChange(maxStart);
      } else {
        // Ensure end doesn't go below start plus minimum duration
        const minEnd = Math.min(
          duration,
          Math.max(time, clipStart + MIN_CLIP_DURATION),
        );
        onClipEndChange(minEnd);
      }
    },
    [
      isDragging,
      clipStart,
      clipEnd,
      onClipStartChange,
      onClipEndChange,
      getPositionFromEvent,
      duration,
    ],
  );

  const handleEnd = useCallback(() => {
    setIsDragging(null);
  }, []);

  // Handle direct timeline clicks/taps for setting positions
  const handleTimelineInteraction = useCallback(
    (e: React.MouseEvent | React.TouchEvent) => {
      if (isDragging) return;

      const time = getPositionFromEvent(e);
      if (time === null) return;

      // Determine which handle to move based on proximity
      const distanceToStart = Math.abs(time - clipStart);
      const distanceToEnd = Math.abs(time - clipEnd);

      if (distanceToStart < distanceToEnd) {
        // Move start handle
        const maxStart = Math.max(
          0,
          Math.min(time, clipEnd - MIN_CLIP_DURATION),
        );
        onClipStartChange(maxStart);
      } else {
        // Move end handle
        const minEnd = Math.min(
          duration,
          Math.max(time, clipStart + MIN_CLIP_DURATION),
        );
        onClipEndChange(minEnd);
      }
    },
    [
      isDragging,
      clipStart,
      clipEnd,
      onClipStartChange,
      onClipEndChange,
      getPositionFromEvent,
      duration,
    ],
  );

  // Handle time input changes
  const handleStartTimeChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const value = e.target.value;
      setClipStartInput(value);

      const parsed = parseTime(value);
      if (
        parsed !== null &&
        parsed >= 0 &&
        parsed <= duration &&
        parsed < clipEnd - MIN_CLIP_DURATION
      ) {
        onClipStartChange(parsed);
      }
    },
    [parseTime, duration, clipEnd, onClipStartChange],
  );

  const handleEndTimeChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const value = e.target.value;
      setClipEndInput(value);

      const parsed = parseTime(value);
      if (
        parsed !== null &&
        parsed >= 0 &&
        parsed <= duration &&
        parsed > clipStart + MIN_CLIP_DURATION
      ) {
        onClipEndChange(parsed);
      }
    },
    [parseTime, duration, clipStart, onClipEndChange],
  );

  const handleDurationChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const value = e.target.value;
      setClipDurationInput(value);

      const parsed = parseTime(value);
      if (
        parsed !== null &&
        parsed > MIN_CLIP_DURATION &&
        parsed <= MAX_CLIP_DURATION
      ) {
        const newEnd = clipStart + parsed;
        if (newEnd <= duration) {
          onClipEndChange(newEnd);
        }
      }
    },
    [parseTime, clipStart, duration, onClipEndChange],
  );

  // Update input fields when slider values change
  React.useEffect(() => {
    setClipStartInput(formatTime(clipStart));
  }, [clipStart, formatTime]);

  React.useEffect(() => {
    setClipEndInput(formatTime(clipEnd));
  }, [clipEnd, formatTime]);

  React.useEffect(() => {
    setClipDurationInput(formatTime(clipDuration));
  }, [clipDuration, formatTime]);

  return (
    <div className="space-y-6">
      <div className="text-center">
        <h3 className="text-xl font-bold text-gray-800 mb-2 flex items-center justify-center">
          <Scissors className="w-5 h-5 mr-2 text-orange-500" />
          Clip Timeline
        </h3>
        <p className="text-gray-600">
          Drag the handles to select your perfect clip
        </p>
        {duration > 0 && (
          <p className="text-sm text-gray-500 mt-1">
            Video Duration: {formatTime(duration)} • Max Clip:{" "}
            {formatTime(MAX_CLIP_DURATION)}
          </p>
        )}
      </div>

      {/* Timeline Visualization */}
      <div className="space-y-4">
        <div
          ref={timelineRef}
          className="relative h-16 bg-gradient-to-r from-gray-200 via-gray-300 to-gray-200 rounded-2xl cursor-pointer shadow-inner touch-none"
          onMouseMove={handleMove}
          onMouseUp={handleEnd}
          onMouseLeave={handleEnd}
          onClick={handleTimelineInteraction}
          onTouchMove={handleMove}
          onTouchEnd={handleEnd}
          onTouchStart={handleTimelineInteraction}
        >
          {/* Selected Clip Area */}
          <div
            className={`absolute top-0 h-full rounded-2xl shadow-lg transition-colors duration-200 ${
              validation.isValid
                ? "bg-gradient-to-r from-orange-400 to-red-400 opacity-80"
                : "bg-gradient-to-r from-red-500 to-red-600 opacity-90"
            }`}
            style={{
              left: `${(clipStart / duration) * 100}%`,
              width: `${((clipEnd - clipStart) / duration) * 100}%`,
            }}
          />

          {/* Start Handle - Enhanced for mobile */}
          <div
            className={`absolute top-1/2 transform -translate-y-1/2 w-8 h-14 bg-white rounded-lg shadow-lg cursor-grab active:cursor-grabbing border-2 hover:scale-110 transition-transform duration-200 ${
              validation.isValidStart ? "border-orange-400" : "border-red-500"
            } touch-manipulation`}
            style={{
              left: `${(clipStart / duration) * 100}%`,
              marginLeft: "-16px",
            }}
            onMouseDown={() => handleStart("start")}
            onTouchStart={() => handleStart("start")}
          >
            <div
              className={`w-full h-full rounded-md flex items-center justify-center ${
                validation.isValidStart
                  ? "bg-gradient-to-b from-orange-400 to-red-400"
                  : "bg-gradient-to-b from-red-500 to-red-600"
              }`}
            >
              <div className="w-1 h-8 bg-white rounded-full" />
            </div>
          </div>

          {/* End Handle - Enhanced for mobile */}
          <div
            className={`absolute top-1/2 transform -translate-y-1/2 w-8 h-14 bg-white rounded-lg shadow-lg cursor-grab active:cursor-grabbing border-2 hover:scale-110 transition-transform duration-200 ${
              validation.isValidEnd ? "border-red-400" : "border-red-500"
            } touch-manipulation`}
            style={{
              left: `${(clipEnd / duration) * 100}%`,
              marginLeft: "-16px",
            }}
            onMouseDown={() => handleStart("end")}
            onTouchStart={() => handleStart("end")}
          >
            <div
              className={`w-full h-full rounded-md flex items-center justify-center ${
                validation.isValidEnd
                  ? "bg-gradient-to-b from-orange-400 to-red-400"
                  : "bg-gradient-to-b from-red-500 to-red-600"
              }`}
            >
              <div className="w-1 h-8 bg-white rounded-full" />
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
                <span>
                  Clip duration cannot exceed {formatTime(MAX_CLIP_DURATION)} (3
                  minutes)
                </span>
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

        {/* Editable Time Inputs */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div
            className={`p-4 rounded-2xl border transition-colors duration-200 ${
              validation.isValidStart
                ? "bg-orange-50 border-orange-200"
                : "bg-red-50 border-red-200"
            }`}
          >
            <label className="block text-sm text-gray-600 mb-2 font-medium">
              Clip Start
            </label>
            <input
              type="text"
              value={clipStartInput}
              onChange={handleStartTimeChange}
              placeholder="0:00.0"
              className={`w-full text-center text-lg font-bold bg-white border rounded-lg px-3 py-2 transition-colors duration-200 focus:outline-none focus:ring-2 ${
                validation.isValidStart
                  ? "text-orange-600 border-orange-300 focus:ring-orange-500"
                  : "text-red-600 border-red-300 focus:ring-red-500"
              }`}
            />
            <p className="text-xs text-gray-500 mt-1">Format: M:SS.D</p>
          </div>

          <div
            className={`p-4 rounded-2xl border transition-colors duration-200 ${
              validation.isMaxDuration
                ? "bg-blue-50 border-blue-200"
                : "bg-red-50 border-red-200"
            }`}
          >
            <label className="block text-sm text-gray-600 mb-2 font-medium">
              Clip Duration
            </label>
            <input
              type="text"
              value={clipDurationInput}
              onChange={handleDurationChange}
              placeholder="0:30.0"
              className={`w-full text-center text-lg font-bold bg-white border rounded-lg px-3 py-2 transition-colors duration-200 focus:outline-none focus:ring-2 ${
                validation.isMaxDuration
                  ? "text-blue-600 border-blue-300 focus:ring-blue-500"
                  : "text-red-600 border-red-300 focus:ring-red-500"
              }`}
            />
            {validation.exceedsMaxDuration && (
              <p className="text-xs text-red-500 mt-1">
                Exceeds {formatTime(MAX_CLIP_DURATION)} limit
              </p>
            )}
            <p className="text-xs text-gray-500 mt-1">
              Max: {formatTime(MAX_CLIP_DURATION)}
            </p>
          </div>

          <div
            className={`p-4 rounded-2xl border transition-colors duration-200 ${
              validation.isValidEnd
                ? "bg-yellow-50 border-yellow-200"
                : "bg-red-50 border-red-200"
            }`}
          >
            <label className="block text-sm text-gray-600 mb-2 font-medium">
              Clip End
            </label>
            <input
              type="text"
              value={clipEndInput}
              onChange={handleEndTimeChange}
              placeholder="0:30.0"
              className={`w-full text-center text-lg font-bold bg-white border rounded-lg px-3 py-2 transition-colors duration-200 focus:outline-none focus:ring-2 ${
                validation.isValidEnd
                  ? "text-yellow-600 border-yellow-300 focus:ring-yellow-500"
                  : "text-red-600 border-red-300 focus:ring-red-500"
              }`}
            />
            <p className="text-xs text-gray-500 mt-1">Format: M:SS.D</p>
          </div>
        </div>

        {/* Usage Instructions */}
        <div className="text-center">
          <p className="text-xs text-gray-500">
            Drag handles • Tap timeline • Edit time inputs • Precision:{" "}
            {SNAP_PRECISION}s
          </p>
          <p className="text-xs text-gray-400 mt-1">
            Touch-optimized for mobile devices
          </p>
        </div>
      </div>
    </div>
  );
};
