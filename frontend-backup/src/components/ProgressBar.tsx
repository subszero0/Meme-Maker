'use client';

import { motion } from 'framer-motion';

interface ProgressBarProps {
  progress?: number; // 0-100, undefined for indeterminate
  className?: string;
}

export default function ProgressBar({ progress, className = '' }: ProgressBarProps) {
  const isIndeterminate = progress === undefined;

  return (
    <div className={`w-full bg-gray-200 rounded-full h-2 overflow-hidden ${className}`}>
      {isIndeterminate ? (
        <motion.div
          className="h-full bg-blue-600 rounded-full"
          initial={{ x: '-100%', width: '30%' }}
          animate={{ x: '100%' }}
          transition={{
            duration: 1.5,
            repeat: Infinity,
            ease: 'easeInOut',
          }}
        />
      ) : (
        <motion.div
          className="h-full bg-blue-600 rounded-full"
          initial={{ width: 0 }}
          animate={{ width: `${Math.max(0, Math.min(100, progress))}%` }}
          transition={{ duration: 0.3, ease: 'easeOut' }}
        />
      )}
    </div>
  );
} 