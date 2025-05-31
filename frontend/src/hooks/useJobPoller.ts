'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { useToast } from '@/components/ToastProvider';

interface PollResult {
  status: 'queued' | 'working' | 'done' | 'error';
  progress?: number;
  url?: string;
  errorCode?: string;
}

const DEFAULT_POLL_INTERVAL = 3000;
const MAX_POLL_INTERVAL = 10000;
const BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export default function useJobPoller(
  jobId: string | null,
  pollIntervalMs: number = DEFAULT_POLL_INTERVAL
): PollResult {
  const [result, setResult] = useState<PollResult>({ status: 'queued' });
  const intervalRef = useRef<NodeJS.Timeout | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);
  const currentIntervalRef = useRef<number>(pollIntervalMs);
  const { pushToast } = useToast();

  const cleanup = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
  }, []);

  const pollJob = useCallback(async () => {
    if (!jobId) {
      setResult({ status: 'queued' });
      return;
    }

    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }

    abortControllerRef.current = new AbortController();

    try {
      const response = await fetch(`${BASE_URL}/api/v1/jobs/${jobId}`, {
        signal: abortControllerRef.current.signal,
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const jobData = await response.json();
      currentIntervalRef.current = pollIntervalMs;

      const newResult: PollResult = {
        status: jobData.status,
        progress: jobData.progress,
        url: jobData.download_url,
        errorCode: jobData.error_code
      };

      setResult(newResult);

      if (jobData.status === 'done' || jobData.status === 'error') {
        cleanup();
        if (jobData.status === 'error' && jobData.error_code !== 'QUEUE_FULL') {
          pushToast({
            type: 'error',
            message: jobData.error_message || 'Job failed to complete'
          });
        }
      }
    } catch (error) {
      if (error instanceof Error && error.name === 'AbortError') return;

      let errorCode = 'NETWORK';
      let shouldRetry = true;

      if (error instanceof Error && error.message.startsWith('HTTP ')) {
        const status = parseInt(error.message.replace('HTTP ', ''));
        if (status >= 500) {
          currentIntervalRef.current = Math.min(currentIntervalRef.current * 2, MAX_POLL_INTERVAL);
        } else if (status === 404) {
          errorCode = 'JOB_NOT_FOUND';
          shouldRetry = false;
        } else if (status === 429) {
          errorCode = 'QUEUE_FULL';
        }
      } else {
        currentIntervalRef.current = Math.min(currentIntervalRef.current * 2, MAX_POLL_INTERVAL);
      }

      setResult({ status: 'error', errorCode });

      if (!shouldRetry) cleanup();

      if (errorCode === 'NETWORK') {
        pushToast({
          type: 'error',
          message: 'Network connection error. Retrying...'
        });
      }
    }
  }, [jobId, cleanup, pushToast]);

  useEffect(() => {
    if (!jobId) {
      setResult({ status: 'queued' });
      cleanup();
      return;
    }

    pollJob();
    intervalRef.current = setInterval(() => {
      pollJob();
    }, currentIntervalRef.current);
    return cleanup;
  }, [jobId, pollJob, cleanup]);

  useEffect(() => {
    currentIntervalRef.current = pollIntervalMs;
  }, [pollIntervalMs]);

  return result;
} 