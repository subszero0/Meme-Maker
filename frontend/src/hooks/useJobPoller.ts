'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import axios, { AxiosError, CancelTokenSource } from 'axios';
import { useToast } from '@/components/ToastProvider';

interface PollResult {
  status: 'queued' | 'working' | 'done' | 'error';
  progress?: number;
  url?: string;
  errorCode?: string;
}

const DEFAULT_POLL_INTERVAL = 2000;
const MAX_POLL_INTERVAL = 10000;
const BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export default function useJobPoller(
  jobId: string | null,
  pollIntervalMs: number = DEFAULT_POLL_INTERVAL
): PollResult {
  const [result, setResult] = useState<PollResult>({ status: 'queued' });
  const intervalRef = useRef<NodeJS.Timeout | null>(null);
  const cancelTokenRef = useRef<CancelTokenSource | null>(null);
  const currentIntervalRef = useRef<number>(pollIntervalMs);
  const { pushToast } = useToast();

  const cleanup = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
    if (cancelTokenRef.current) {
      cancelTokenRef.current.cancel('Component unmounted or polling stopped');
      cancelTokenRef.current = null;
    }
  }, []);

  const pollJob = useCallback(async () => {
    if (!jobId) {
      setResult({ status: 'queued' });
      return;
    }

    if (cancelTokenRef.current) {
      cancelTokenRef.current.cancel('New request initiated');
    }

    cancelTokenRef.current = axios.CancelToken.source();

    try {
      const response = await axios.get(`${BASE_URL}/api/v1/jobs/${jobId}`, {
        cancelToken: cancelTokenRef.current.token,
        timeout: 5000,
      });

      const jobData = response.data;
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
      if (axios.isCancel(error)) return;

      const axiosError = error as AxiosError;
      let errorCode = 'NETWORK';
      let shouldRetry = true;

      if (axiosError.response) {
        const status = axiosError.response.status;
        if (status >= 500) {
          currentIntervalRef.current = Math.min(currentIntervalRef.current * 2, MAX_POLL_INTERVAL);
        } else if (status === 404) {
          errorCode = 'JOB_NOT_FOUND';
          shouldRetry = false;
        } else if (status === 429) {
          errorCode = 'QUEUE_FULL';
        }
      } else if (axiosError.code === 'ECONNABORTED') {
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