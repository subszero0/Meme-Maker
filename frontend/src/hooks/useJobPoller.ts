"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import axios, { AxiosError, CancelTokenSource } from "axios";
import { useToast } from "@/components/ToastProvider";

interface PollResult {
  status: "queued" | "working" | "done" | "error";
  progress?: number;
  url?: string;
  errorCode?: string;
  stage?: string;
}

const DEFAULT_POLL_INTERVAL = 2000;
const MAX_POLL_INTERVAL = 10000;
const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function useJobPoller(
  jobId: string | null,
  pollIntervalMs: number = DEFAULT_POLL_INTERVAL,
): PollResult {
  const [result, setResult] = useState<PollResult>({ status: "queued" });
  const intervalRef = useRef<NodeJS.Timeout | null>(null);
  const cancelTokenRef = useRef<CancelTokenSource | null>(null);
  const currentIntervalRef = useRef<number>(pollIntervalMs);
  const consecutiveErrorsRef = useRef<number>(0);
  const { pushToast } = useToast();

  const cleanup = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
    if (cancelTokenRef.current) {
      cancelTokenRef.current.cancel("Component unmounted or polling stopped");
      cancelTokenRef.current = null;
    }
  }, []);

  const pollJob = useCallback(async () => {
    if (!jobId) {
      console.log("📊 JobPoller: No jobId provided, setting status to queued");
      setResult({ status: "queued" });
      return;
    }

    console.log(`📊 JobPoller: Polling job ${jobId}`);

    if (cancelTokenRef.current) {
      cancelTokenRef.current.cancel("New request initiated");
    }

    cancelTokenRef.current = axios.CancelToken.source();

    try {
      console.log(
        `📊 JobPoller: Making request to ${BASE_URL}/api/v1/jobs/${jobId}`,
      );
      const response = await axios.get(`${BASE_URL}/api/v1/jobs/${jobId}`, {
        cancelToken: cancelTokenRef.current.token,
        timeout: 5000,
      });

      const jobData = response.data;
      console.log("📊 JobPoller: Raw job data received:", jobData);

      currentIntervalRef.current = pollIntervalMs;
      consecutiveErrorsRef.current = 0; // Reset error counter on success

      const newResult: PollResult = {
        status: jobData.status,
        progress: jobData.progress,
        url: jobData.download_url,
        errorCode: jobData.error_code,
        stage: jobData.stage,
      };

      // Add helpful stage descriptions for queued jobs
      if (jobData.status === "queued" && !jobData.stage) {
        newResult.stage = "Waiting for worker to be available...";
      }

      console.log("📊 JobPoller: Processed result:", newResult);
      console.log(
        `📊 JobPoller: Job ${jobId} - Status: ${newResult.status}, Progress: ${newResult.progress}%, Stage: ${newResult.stage}`,
      );

      setResult(newResult);

      if (jobData.status === "done" || jobData.status === "error") {
        console.log(
          `📊 JobPoller: Job ${jobId} completed with status: ${jobData.status}`,
        );
        if (jobData.status === "done") {
          console.log(
            `📊 JobPoller: Job ${jobId} SUCCESS - Download URL: ${jobData.download_url}`,
          );
        } else {
          console.log(
            `📊 JobPoller: Job ${jobId} ERROR - Code: ${jobData.error_code}, Message: ${jobData.error_message}`,
          );
        }
        cleanup();
        if (jobData.status === "error" && jobData.error_code !== "QUEUE_FULL") {
          pushToast({
            type: "error",
            message: jobData.error_message || "Job failed to complete",
          });
        }
      }
    } catch (error) {
      if (axios.isCancel(error)) return;

      const axiosError = error as AxiosError;
      let errorCode = "NETWORK";
      let shouldRetry = true;
      let errorMessage = "";

      consecutiveErrorsRef.current++;

      if (axiosError.response) {
        const status = axiosError.response.status;
        if (status >= 500) {
          currentIntervalRef.current = Math.min(
            currentIntervalRef.current * 2,
            MAX_POLL_INTERVAL,
          );
          errorMessage = "Server error - retrying with longer interval";
        } else if (status === 404) {
          errorCode = "JOB_NOT_FOUND";
          shouldRetry = false;
          errorMessage = "Job not found";
        } else if (status === 429) {
          errorCode = "QUEUE_FULL";
          errorMessage = "Server is busy - please try again later";
        }
      } else if (axiosError.code === "ECONNABORTED") {
        currentIntervalRef.current = Math.min(
          currentIntervalRef.current * 2,
          MAX_POLL_INTERVAL,
        );
        errorMessage = "Request timeout - retrying";
      } else if (
        axiosError.code === "ECONNREFUSED" ||
        axiosError.message.includes("Network Error")
      ) {
        errorCode = "SERVICE_UNAVAILABLE";
        errorMessage =
          "Backend service unavailable. Please ensure Docker services are running.";

        // Show help message after multiple connection failures
        if (consecutiveErrorsRef.current >= 3) {
          pushToast({
            type: "error",
            message:
              "Cannot connect to backend. Make sure Docker Desktop is running and run: docker-compose up -d",
          });
          cleanup(); // Stop polling after repeated failures
          shouldRetry = false;
        }
      }

      setResult({ status: "error", errorCode, stage: errorMessage });

      if (!shouldRetry) cleanup();

      // Only show toast for first few errors to avoid spam
      if (consecutiveErrorsRef.current <= 2 && errorCode === "NETWORK") {
        pushToast({
          type: "error",
          message: errorMessage || "Network connection error. Retrying...",
        });
      }
    }
  }, [jobId, cleanup, pushToast, pollIntervalMs]);

  useEffect(() => {
    if (!jobId) {
      setResult({ status: "queued" });
      cleanup();
      consecutiveErrorsRef.current = 0;
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
