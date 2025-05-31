'use client';

import { useReducer, useCallback, useState, useEffect, useRef } from 'react';
import dynamic from 'next/dynamic';
import { useDebouncedCallback } from 'use-debounce';
import { formatTime, parseTime } from '@/lib/formatTime';
import { useToast } from './ToastProvider';
import Notification from './Notification';
import SimpleRange from './ui/SimpleRange';

// Dynamically import ReactPlayer to reduce initial bundle size
const ReactPlayer = dynamic(() => import('react-player/lazy'), {
  ssr: false,
  loading: () => (
    <div className="w-full h-64 bg-gray-200 dark:bg-gray-700 animate-pulse rounded-lg flex items-center justify-center">
      <span className="text-gray-500 dark:text-gray-400">Loading video player...</span>
    </div>
  )
});

interface TrimPanelProps {
  jobMeta: { url: string; title: string; duration: number }; // duration in seconds
  onSubmit(params: { in: number; out: number; rights: boolean }): void;
  disabled?: boolean;
  stepSize?: number; // @accessibility - Parameterized step size for keyboard navigation
}

interface TrimState {
  in: number;
  out: number;
  rights: boolean;
}

type TrimAction =
  | { type: 'SET_IN'; payload: number }
  | { type: 'SET_OUT'; payload: number }
  | { type: 'SET_RIGHTS'; payload: boolean }
  | { type: 'SET_RANGE'; payload: { in: number; out: number } };

function trimReducer(state: TrimState, action: TrimAction): TrimState {
  switch (action.type) {
    case 'SET_IN':
      return { ...state, in: action.payload };
    case 'SET_OUT':
      return { ...state, out: action.payload };
    case 'SET_RIGHTS':
      return { ...state, rights: action.payload };
    case 'SET_RANGE':
      return { ...state, in: action.payload.in, out: action.payload.out };
    default:
      return state;
  }
}

export default function TrimPanel({ 
  jobMeta, 
  onSubmit, 
  disabled,
  stepSize = 0.1 // @accessibility - Default 0.1 second increment
}: TrimPanelProps) {
  const { pushToast } = useToast();
  const [state, dispatch] = useReducer(trimReducer, {
    in: 0,
    out: Math.min(jobMeta.duration, 180), // Cap at 3 minutes
    rights: false,
  });

  const [inTimeInput, setInTimeInput] = useState(formatTime(state.in));
  const [outTimeInput, setOutTimeInput] = useState(formatTime(state.out));
  
  // @accessibility - Refs for screen reader announcements
  const announcementRef = useRef<HTMLDivElement>(null);
  const lastAnnouncedValues = useRef<{ in: number; out: number }>({ in: state.in, out: state.out });

  // Update time inputs when state changes
  useEffect(() => {
    setInTimeInput(formatTime(state.in));
    setOutTimeInput(formatTime(state.out));
  }, [state.in, state.out]);

  const clipDuration = state.out - state.in;
  const maxDuration = 180; // 3 minutes in seconds

  // Validation
  const isValidClip = state.out > state.in && clipDuration <= maxDuration;
  const canSubmit = isValidClip && state.rights;

  // @accessibility - Debounced screen reader announcement on handle release
  const announceValue = useDebouncedCallback((index: number, value: number) => {
    const label = index === 0 ? 'Start time' : 'End time';
    const announcement = `${label}: ${formatTime(value)}`;
    
    if (announcementRef.current) {
      announcementRef.current.textContent = announcement;
    }
  }, 250); // Announce only after handle release

  // Debounced input handlers
  const debouncedInChange = useDebouncedCallback((value: string) => {
    const parsed = parseTime(value);
    if (parsed !== null && parsed >= 0 && parsed <= jobMeta.duration) {
      dispatch({ type: 'SET_IN', payload: parsed });
    }
  }, 150);

  const debouncedOutChange = useDebouncedCallback((value: string) => {
    const parsed = parseTime(value);
    if (parsed !== null && parsed >= 0 && parsed <= jobMeta.duration) {
      dispatch({ type: 'SET_OUT', payload: parsed });
    }
  }, 150);

  const handleSliderChange = useCallback((values: number[]) => {
    const [newIn, newOut] = values;
    // Snap to 0.1s precision
    const snappedIn = Math.round(newIn * 10) / 10;
    const snappedOut = Math.round(newOut * 10) / 10;
    
    // Ensure minimum gap of 0.1s
    if (snappedOut - snappedIn >= 0.1) {
      dispatch({ type: 'SET_RANGE', payload: { in: snappedIn, out: snappedOut } });
      
      // @accessibility - Announce value changes for significant moves only
      if (Math.abs(snappedIn - lastAnnouncedValues.current.in) >= 1 || 
          Math.abs(snappedOut - lastAnnouncedValues.current.out) >= 1) {
        announceValue(0, snappedIn);
        announceValue(1, snappedOut);
        lastAnnouncedValues.current = { in: snappedIn, out: snappedOut };
      }
    }
  }, [announceValue]);

  // @accessibility - Keyboard navigation handlers
  const handleKeyDown = useCallback((index: number, event: React.KeyboardEvent) => {
    const currentValue = index === 0 ? state.in : state.out;
    let newValue = currentValue;

    switch (event.key) {
      case 'ArrowRight':
      case 'ArrowUp':
        event.preventDefault();
        newValue = Math.min(currentValue + stepSize, jobMeta.duration);
        break;
      case 'ArrowLeft':
      case 'ArrowDown':
        event.preventDefault();
        newValue = Math.max(currentValue - stepSize, 0);
        break;
      case 'Home':
        event.preventDefault();
        newValue = 0;
        break;
      case 'End':
        event.preventDefault();
        newValue = jobMeta.duration;
        break;
      case 'PageUp':
        event.preventDefault();
        newValue = Math.min(currentValue + 10, jobMeta.duration); // 10-second jump
        break;
      case 'PageDown':
        event.preventDefault();
        newValue = Math.max(currentValue - 10, 0); // 10-second jump
        break;
      default:
        return; // Don't prevent default for other keys
    }

    // Snap to step precision
    newValue = Math.round(newValue / stepSize) * stepSize;

    // Update appropriate handle
    if (index === 0) {
      // Start handle - ensure it doesn't exceed end handle
      newValue = Math.min(newValue, state.out - stepSize);
      dispatch({ type: 'SET_IN', payload: newValue });
    } else {
      // End handle - ensure it doesn't go below start handle
      newValue = Math.max(newValue, state.in + stepSize);
      dispatch({ type: 'SET_OUT', payload: newValue });
    }

    // @accessibility - Immediate announcement for keyboard navigation
    announceValue(index, newValue);
  }, [state.in, state.out, stepSize, jobMeta.duration, announceValue]);

  const handleInTimeChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setInTimeInput(value);
    debouncedInChange(value);
  }, [debouncedInChange]);

  const handleOutTimeChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setOutTimeInput(value);
    debouncedOutChange(value);
  }, [debouncedOutChange]);

  const handleSubmit = useCallback(() => {
    if (!canSubmit) return;
    
    try {
      onSubmit({ in: state.in, out: state.out, rights: true });
    } catch (error) {
      pushToast({ type: 'error', message: 'Failed to submit clip request' });
    }
  }, [canSubmit, state.in, state.out, onSubmit, pushToast]);

  return (
    <div className="space-y-6 max-w-4xl mx-auto p-6">
      {/* @accessibility - Hidden live region for screen reader announcements */}
      <div 
        ref={announcementRef}
        className="sr-only"
        aria-live="polite"
        aria-atomic="true"
        data-testid="slider-announcement"
      />

      {/* Video Preview */}
      <div className="aspect-video bg-black rounded-lg overflow-hidden">
        <ReactPlayer
          url={jobMeta.url}
          width="100%"
          height="100%"
          controls
          muted
          playing
          data-testid="video-player"
        />
      </div>

      {/* Video Info */}
      <div className="text-center">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white truncate">{jobMeta.title}</h3>
        <p className="text-sm text-gray-600 dark:text-gray-400">Duration: {formatTime(jobMeta.duration)}</p>
      </div>

      {/* Time Inputs */}
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label 
            htmlFor="in-time" 
            id="start-time-label"
            className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1"
          >
            Start Time (hh:mm:ss.mmm)
          </label>
          <input
            id="in-time"
            data-testid="start-time"
            data-cy="start-time-input"
            type="text"
            value={inTimeInput}
            onChange={handleInTimeChange}
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-800 dark:text-white font-mono"
            placeholder="00:00:00.000"
            aria-describedby="start-time-help"
          />
          <div id="start-time-help" className="sr-only">
            Enter start time in hours, minutes, seconds, and milliseconds format
          </div>
        </div>
        <div>
          <label 
            htmlFor="out-time" 
            id="end-time-label"
            className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1"
          >
            End Time (hh:mm:ss.mmm)
          </label>
          <input
            id="out-time"
            data-testid="end-time"
            data-cy="end-time-input"
            type="text"
            value={outTimeInput}
            onChange={handleOutTimeChange}
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-800 dark:text-white font-mono"
            placeholder="00:00:00.000"
            aria-describedby="end-time-help"
          />
          <div id="end-time-help" className="sr-only">
            Enter end time in hours, minutes, seconds, and milliseconds format
          </div>
        </div>
      </div>

      {/* @accessibility - Enhanced Slider with full ARIA support */}
      <div className="space-y-2">
        <div className="flex justify-between text-sm text-gray-700 dark:text-gray-300 mb-2">
          <span>Video Timeline</span>
          <span>Use arrow keys to adjust by {stepSize}s, Page Up/Down for 10s jumps</span>
        </div>
        
        <SimpleRange
          values={[state.in, state.out]}
          step={stepSize}
          min={0}
          max={jobMeta.duration}
          onChange={handleSliderChange}
        />
        
        <div className="flex justify-between text-xs text-gray-500 dark:text-gray-400">
          <span aria-label={`Current start time: ${formatTime(state.in)}`}>{formatTime(state.in)}</span>
          <span 
            className={clipDuration > maxDuration ? 'text-red-600 dark:text-red-400 font-medium' : ''}
            aria-label={`Clip duration: ${formatTime(clipDuration)}${clipDuration > maxDuration ? ' - exceeds maximum allowed duration' : ''}`}
          >
            Duration: {formatTime(clipDuration)}
          </span>
          <span aria-label={`Current end time: ${formatTime(state.out)}`}>{formatTime(state.out)}</span>
        </div>
      </div>

      {/* Validation Error */}
      {clipDuration > maxDuration && (
        <Notification
          type="error"
          message="Trim to three minutes or less to proceed."
          position="inline"
          data-cy="duration-error"
        />
      )}

      {state.out <= state.in && (
        <Notification
          type="error"
          message="End time must be after start time."
          position="inline"
          data-cy="range-error"
        />
      )}

      {/* Rights Checkbox */}
      <div className="flex items-start space-x-3">
        <input
          id="rights-checkbox"
          data-testid="rights-checkbox"
          data-cy="rights-checkbox"
          type="checkbox"
          checked={state.rights}
          onChange={(e) => dispatch({ type: 'SET_RIGHTS', payload: e.target.checked })}
          className="mt-1 h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 dark:border-gray-600 rounded dark:bg-gray-800"
          aria-describedby="rights-description"
        />
        <div>
          <label htmlFor="rights-checkbox" className="text-sm text-text-primary dark:text-gray-200">
            I confirm I have the right to download this content and agree to the{' '}
            <a
              href="/terms"
              target="_blank"
              rel="noopener noreferrer"
              className="text-link-primary hover:text-link-hover dark:text-link-dark dark:hover:text-link-dark-hover underline focus:outline-none focus:ring-2 focus:ring-blue-500 rounded"
            >
              Terms of Use
            </a>
            .
          </label>
          <div id="rights-description" className="sr-only">
            Required: You must confirm you have the legal right to download this video content
          </div>
        </div>
      </div>

      {/* Submit Button */}
      <button
        onClick={handleSubmit}
        disabled={!canSubmit || disabled}
        data-testid="clip-btn"
        data-cy="clip-button"
        className={`w-full min-h-[44px] py-3 px-4 rounded-md font-semibold text-white transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 ${
          canSubmit && !disabled
            ? 'bg-primary-800 hover:bg-primary-900 focus-visible:ring-primary-500 dark:focus-visible:ring-offset-gray-900'
            : 'bg-gray-400 dark:bg-gray-600 cursor-not-allowed'
        }`}
        aria-describedby="submit-button-help"
      >
        Clip & Download
      </button>
      <div id="submit-button-help" className="sr-only">
        {!isValidClip && !state.rights ? 
          'Button disabled: Please set valid clip times and accept terms' :
          !isValidClip ? 
            'Button disabled: Please set valid clip times within 3 minutes' :
            !state.rights ? 
              'Button disabled: Please accept the terms of use' :
              'Create and download your video clip'
        }
      </div>
    </div>
  );
} 