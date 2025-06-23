'use client';

import { useReducer, useCallback, useState, useEffect } from 'react';
import ReactPlayer from 'react-player';
import { Range, getTrackBackground } from 'react-range';
import { useDebouncedCallback } from 'use-debounce';
import { formatTime, parseTime } from '@/lib/formatTime';
import { useToast } from './ToastProvider';
import ResolutionSelector from './ResolutionSelector';

interface TrimPanelProps {
  jobMeta: { url: string; title: string; duration: number }; // duration in seconds
  onSubmit(params: { in: number; out: number; rights: boolean; formatId?: string }): void;
}

interface TrimState {
  in: number;
  out: number;
  rights: boolean;
  formatId?: string;
}

type TrimAction =
  | { type: 'SET_IN'; payload: number }
  | { type: 'SET_OUT'; payload: number }
  | { type: 'SET_RIGHTS'; payload: boolean }
  | { type: 'SET_RANGE'; payload: { in: number; out: number } }
  | { type: 'SET_FORMAT_ID'; payload: string | undefined };

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
    case 'SET_FORMAT_ID':
      return { ...state, formatId: action.payload };
    default:
      return state;
  }
}

export default function TrimPanel({ jobMeta, onSubmit }: TrimPanelProps) {
  const { pushToast } = useToast();
  const [state, dispatch] = useReducer(trimReducer, {
    in: 0,
    out: Math.min(jobMeta.duration, 180), // Cap at 3 minutes
    rights: false,
    formatId: undefined,
  });

  const [inTimeInput, setInTimeInput] = useState(formatTime(state.in));
  const [outTimeInput, setOutTimeInput] = useState(formatTime(state.out));

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
    }
  }, []);

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

  const handleFormatChange = useCallback((formatId: string | undefined) => {
    console.log('🎭 TrimPanel: Format changed to:', formatId);
    dispatch({ type: 'SET_FORMAT_ID', payload: formatId });
  }, []);

  const handleSubmit = useCallback(() => {
    if (!canSubmit) return;
    
    console.log('🎭 TrimPanel: Submitting with state:', {
      in: state.in,
      out: state.out,
      formatId: state.formatId,
      rights: state.rights
    });
    
    try {
      onSubmit({ 
        in: state.in, 
        out: state.out, 
        rights: true, 
        formatId: state.formatId 
      });
    } catch (error) {
      console.error('🎭 TrimPanel: Submit failed:', error);
      pushToast({ type: 'error', message: 'Failed to submit clip request' });
    }
  }, [canSubmit, state.in, state.out, state.formatId, state.rights, onSubmit, pushToast]);

  return (
    <div className="space-y-6 max-w-4xl mx-auto p-6">
      {/* Video Preview */}
      <div className="aspect-video bg-black rounded-lg overflow-hidden">
        <ReactPlayer
          url={jobMeta.url}
          width="100%"
          height="100%"
          controls
          muted
          playing
        />
      </div>

      {/* Video Info */}
      <div className="text-center">
        <h3 className="text-lg font-semibold text-gray-900 truncate">{jobMeta.title}</h3>
        <p className="text-sm text-gray-600">Duration: {formatTime(jobMeta.duration)}</p>
      </div>

      {/* Time Inputs */}
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label htmlFor="in-time" className="block text-sm font-medium text-gray-700 mb-1">
            Start Time (hh:mm:ss.mmm)
          </label>
          <input
            id="in-time"
            data-testid="start-time"
            type="text"
            value={inTimeInput}
            onChange={handleInTimeChange}
            className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 font-mono"
            placeholder="00:00:00.000"
          />
        </div>
        <div>
          <label htmlFor="out-time" className="block text-sm font-medium text-gray-700 mb-1">
            End Time (hh:mm:ss.mmm)
          </label>
          <input
            id="out-time"
            data-testid="end-time"
            type="text"
            value={outTimeInput}
            onChange={handleOutTimeChange}
            className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 font-mono"
            placeholder="00:00:00.000"
          />
        </div>
      </div>

      {/* Slider */}
      <div className="space-y-2">
        <Range
          values={[state.in, state.out]}
          step={0.1}
          min={0}
          max={jobMeta.duration}
          onChange={handleSliderChange}
          renderTrack={({ props, children }) => (
            <div
              {...props}
              className="h-2 w-full rounded-md"
              style={{
                background: getTrackBackground({
                  values: [state.in, state.out],
                  colors: ['#e5e7eb', '#3b82f6', '#e5e7eb'],
                  min: 0,
                  max: jobMeta.duration,
                }),
              }}
            >
              {children}
            </div>
          )}
          renderThumb={({ index, props }) => {
            const { key, ...thumbProps } = props;
            return (
              <div
                key={key}
                {...thumbProps}
                data-testid={index === 0 ? 'handle-start' : 'handle-end'}
                className="h-6 w-6 bg-blue-600 border-2 border-white rounded-full shadow-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-1"
                style={{ ...thumbProps.style }}
                aria-valuemin={0}
                aria-valuemax={jobMeta.duration}
                aria-valuenow={index === 0 ? state.in : state.out}
                aria-label={index === 0 ? 'Start time' : 'End time'}
              />
            );
          }}
        />
        <div className="flex justify-between text-xs text-gray-500">
          <span>{formatTime(state.in)}</span>
          <span className={clipDuration > maxDuration ? 'text-red-600 font-medium' : ''}>
            Duration: {formatTime(clipDuration)}
          </span>
          <span>{formatTime(state.out)}</span>
        </div>
      </div>

      {/* Validation Error */}
      {clipDuration > maxDuration && (
        <div className="text-red-600 text-sm bg-red-50 border border-red-200 rounded-md p-3">
          Trim to three minutes or less to proceed.
        </div>
      )}

      {state.out <= state.in && (
        <div className="text-red-600 text-sm bg-red-50 border border-red-200 rounded-md p-3">
          End time must be after start time.
        </div>
      )}

      {/* Resolution Selector */}
      <ResolutionSelector
        url={jobMeta.url}
        selectedFormatId={state.formatId}
        onFormatChange={handleFormatChange}
      />

      {/* Rights Checkbox */}
      <div className="flex items-start space-x-3">
        <input
          id="rights-checkbox"
          data-testid="rights-checkbox"
          type="checkbox"
          checked={state.rights}
          onChange={(e) => dispatch({ type: 'SET_RIGHTS', payload: e.target.checked })}
          className="mt-1 h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
        />
        <label htmlFor="rights-checkbox" className="text-sm text-gray-700">
          I have the right to download this video and accept the Terms of Use.
        </label>
      </div>

      {/* Submit Button */}
      <button
        onClick={handleSubmit}
        disabled={!canSubmit}
        data-testid="clip-btn"
        className={`w-full py-3 px-4 rounded-md font-semibold text-white transition-colors ${
          canSubmit
            ? 'bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2'
            : 'bg-gray-400 cursor-not-allowed'
        }`}
      >
        Clip & Download
      </button>
    </div>
  );
} 