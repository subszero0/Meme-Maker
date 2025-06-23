"use client";

import { useState, useCallback } from "react";

interface TimeRangeSliderProps {
  duration: number; // in seconds
  startTime: number;
  endTime: number;
  onTimeChange: (start: number, end: number) => void;
  disabled?: boolean;
}

export default function TimeRangeSlider({
  duration,
  startTime,
  endTime,
  onTimeChange,
  disabled = false,
}: TimeRangeSliderProps) {
  const [isDragging, setIsDragging] = useState<"start" | "end" | null>(null);

  const formatTime = (seconds: number) => {
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const s = Math.floor(seconds % 60);
    const ms = Math.floor((seconds % 1) * 1000);

    if (h > 0) {
      return `${h.toString().padStart(2, "0")}:${m.toString().padStart(2, "0")}:${s.toString().padStart(2, "0")}.${ms.toString().padStart(3, "0")}`;
    }
    return `${m.toString().padStart(2, "0")}:${s.toString().padStart(2, "0")}.${ms.toString().padStart(3, "0")}`;
  };

  const handleMouseDown = useCallback(
    (type: "start" | "end") => {
      if (!disabled) {
        setIsDragging(type);
      }
    },
    [disabled],
  );

  const handleMouseMove = useCallback(
    (e: React.MouseEvent) => {
      if (!isDragging || disabled) return;

      const rect = e.currentTarget.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const percentage = Math.max(0, Math.min(1, x / rect.width));
      const newTime = percentage * duration;

      if (isDragging === "start") {
        const newStart = Math.min(newTime, endTime - 1);
        onTimeChange(newStart, endTime);
      } else {
        const newEnd = Math.max(newTime, startTime + 1);
        onTimeChange(startTime, newEnd);
      }
    },
    [isDragging, disabled, duration, startTime, endTime, onTimeChange],
  );

  const handleMouseUp = useCallback(() => {
    setIsDragging(null);
  }, []);

  const startPercentage = (startTime / duration) * 100;
  const endPercentage = (endTime / duration) * 100;
  const clipDuration = endTime - startTime;
  const maxDuration = 3 * 60; // 3 minutes in seconds

  return (
    <div className="w-full space-y-4">
      {/* Time inputs */}
      <div className="flex items-center justify-between text-sm">
        <div className="flex items-center space-x-2">
          <label className="text-gray-600">Start:</label>
          <span className="font-mono bg-gray-100 px-2 py-1 rounded">
            {formatTime(startTime)}
          </span>
        </div>
        <div className="flex items-center space-x-2">
          <label className="text-gray-600">Duration:</label>
          <span
            className={`font-mono px-2 py-1 rounded ${
              clipDuration > maxDuration
                ? "bg-red-100 text-red-800"
                : "bg-gray-100"
            }`}
          >
            {formatTime(clipDuration)}
          </span>
        </div>
        <div className="flex items-center space-x-2">
          <label className="text-gray-600">End:</label>
          <span className="font-mono bg-gray-100 px-2 py-1 rounded">
            {formatTime(endTime)}
          </span>
        </div>
      </div>

      {/* Slider */}
      <div
        className="relative h-6 bg-gray-200 rounded-lg cursor-pointer"
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
      >
        {/* Track */}
        <div
          className="absolute h-full bg-blue-500 rounded-lg"
          style={{
            left: `${startPercentage}%`,
            width: `${endPercentage - startPercentage}%`,
          }}
        />

        {/* Start handle */}
        <div
          className="absolute w-6 h-6 bg-blue-600 border-2 border-white rounded-full cursor-grab active:cursor-grabbing transform -translate-y-0 -translate-x-3 hover:scale-110 transition-transform"
          style={{ left: `${startPercentage}%` }}
          onMouseDown={() => handleMouseDown("start")}
        />

        {/* End handle */}
        <div
          className="absolute w-6 h-6 bg-blue-600 border-2 border-white rounded-full cursor-grab active:cursor-grabbing transform -translate-y-0 -translate-x-3 hover:scale-110 transition-transform"
          style={{ left: `${endPercentage}%` }}
          onMouseDown={() => handleMouseDown("end")}
        />
      </div>

      {/* Validation message */}
      {clipDuration > maxDuration && (
        <p className="text-red-600 text-sm">
          Trim to three minutes or less to proceed.
        </p>
      )}
    </div>
  );
}
