'use client';

import { useEffect, useState } from 'react';

interface ProgressBarProps {
  progress?: number; // 0-100, undefined for indeterminate
  className?: string;
}

export default function ProgressBar({ progress, className = '' }: ProgressBarProps) {
  const isIndeterminate = progress === undefined;
  const [animatedProgress, setAnimatedProgress] = useState(0);

  useEffect(() => {
    if (progress !== undefined) {
      setAnimatedProgress(Math.max(0, Math.min(100, progress)));
    }
  }, [progress]);

  return (
    <div className={`w-full bg-gray-200 rounded-full h-2 overflow-hidden ${className}`}>
      {isIndeterminate ? (
        <div className="h-full bg-blue-600 rounded-full w-1/3 animate-bounce" />
      ) : (
        <div
          className="h-full bg-blue-600 rounded-full transition-all duration-300 ease-out"
          style={{ width: `${animatedProgress}%` }}
        />
      )}
    </div>
  );
} 