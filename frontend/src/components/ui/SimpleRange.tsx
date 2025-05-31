'use client';

import { useCallback, useRef, useState, useEffect } from 'react';

interface SimpleRangeProps {
  values: [number, number];
  min: number;
  max: number;
  step?: number;
  onChange: (values: [number, number]) => void;
  onKeyDown?: (index: number, event: React.KeyboardEvent) => void;
  className?: string;
}

export default function SimpleRange({
  values,
  min,
  max,
  step = 0.1,
  onChange,
  onKeyDown,
  className = ''
}: SimpleRangeProps) {
  const trackRef = useRef<HTMLDivElement>(null);
  const [isDragging, setIsDragging] = useState<number | null>(null);
  const [dragOffset, setDragOffset] = useState(0);

  const getPercentage = (value: number) => ((value - min) / (max - min)) * 100;
  const getValueFromPercentage = (percentage: number) => min + (percentage / 100) * (max - min);

  const handleMouseDown = useCallback((index: number, event: React.MouseEvent) => {
    event.preventDefault();
    setIsDragging(index);
    
    const rect = trackRef.current?.getBoundingClientRect();
    if (rect) {
      const clickX = event.clientX - rect.left;
      const handleX = (getPercentage(values[index]) / 100) * rect.width;
      setDragOffset(clickX - handleX);
    }
  }, [values]);

  const handleMouseMove = useCallback((event: MouseEvent) => {
    if (isDragging === null || !trackRef.current) return;

    const rect = trackRef.current.getBoundingClientRect();
    const x = event.clientX - rect.left - dragOffset;
    const percentage = Math.max(0, Math.min(100, (x / rect.width) * 100));
    const newValue = Math.round(getValueFromPercentage(percentage) / step) * step;

    const newValues: [number, number] = [...values];
    
    if (isDragging === 0) {
      newValues[0] = Math.max(min, Math.min(newValue, values[1] - step));
    } else {
      newValues[1] = Math.min(max, Math.max(newValue, values[0] + step));
    }

    onChange(newValues);
  }, [isDragging, dragOffset, values, min, max, step, onChange]);

  const handleMouseUp = useCallback(() => {
    setIsDragging(null);
    setDragOffset(0);
  }, []);

  useEffect(() => {
    if (isDragging !== null) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
      return () => {
        document.removeEventListener('mousemove', handleMouseMove);
        document.removeEventListener('mouseup', handleMouseUp);
      };
    }
  }, [isDragging, handleMouseMove, handleMouseUp]);

  const handleKeyDown = useCallback((index: number, event: React.KeyboardEvent) => {
    if (onKeyDown) {
      onKeyDown(index, event);
    }
  }, [onKeyDown]);

  const startPercentage = getPercentage(values[0]);
  const endPercentage = getPercentage(values[1]);

  return (
    <div className={`relative ${className}`}>
      {/* Track */}
      <div
        ref={trackRef}
        className="h-3 w-full rounded-md relative cursor-pointer"
        style={{
          background: `linear-gradient(to right, 
            #e5e7eb 0%, 
            #e5e7eb ${startPercentage}%, 
            #3b82f6 ${startPercentage}%, 
            #3b82f6 ${endPercentage}%, 
            #e5e7eb ${endPercentage}%, 
            #e5e7eb 100%)`
        }}
      >
        {/* Start Handle */}
        <div
          className={`
            absolute h-11 w-11 bg-blue-600 border-2 border-white dark:border-gray-800 rounded-full shadow-lg 
            transition-all duration-150 ease-in-out cursor-grab
            focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2
            hover:scale-105 hover:shadow-xl
            ${isDragging === 0 ? 'scale-110 shadow-2xl ring-2 ring-blue-400 cursor-grabbing' : ''}
          `}
          style={{
            left: `${startPercentage}%`,
            top: '50%',
            transform: 'translate(-50%, -50%)',
          }}
          onMouseDown={(e) => handleMouseDown(0, e)}
          onKeyDown={(e) => handleKeyDown(0, e)}
          tabIndex={0}
          role="slider"
          aria-valuemin={min}
          aria-valuemax={max}
          aria-valuenow={values[0]}
          aria-label="Start time"
        >
          <div className="absolute inset-2 bg-white dark:bg-gray-200 rounded-full pointer-events-none" />
        </div>

        {/* End Handle */}
        <div
          className={`
            absolute h-11 w-11 bg-blue-600 border-2 border-white dark:border-gray-800 rounded-full shadow-lg 
            transition-all duration-150 ease-in-out cursor-grab
            focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2
            hover:scale-105 hover:shadow-xl
            ${isDragging === 1 ? 'scale-110 shadow-2xl ring-2 ring-blue-400 cursor-grabbing' : ''}
          `}
          style={{
            left: `${endPercentage}%`,
            top: '50%',
            transform: 'translate(-50%, -50%)',
          }}
          onMouseDown={(e) => handleMouseDown(1, e)}
          onKeyDown={(e) => handleKeyDown(1, e)}
          tabIndex={0}
          role="slider"
          aria-valuemin={min}
          aria-valuemax={max}
          aria-valuenow={values[1]}
          aria-label="End time"
        >
          <div className="absolute inset-2 bg-white dark:bg-gray-200 rounded-full pointer-events-none" />
        </div>
      </div>
    </div>
  );
} 