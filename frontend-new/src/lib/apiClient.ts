import axios, { AxiosError } from "axios";
import { config } from "../config/environment";

// ===========================
// Configuration
// ===========================

const API_BASE_URL = config.API_BASE_URL;
const API_TIMEOUT = parseInt(import.meta.env.VITE_API_TIMEOUT || "30000");

// ===========================
// Error Handling
// ===========================

export class ApiException extends Error {
  status?: number;
  code?: string;

  constructor(message: string, status?: number, code?: string) {
    super(message);
    this.name = "ApiException";
    this.status = status;
    this.code = code;
  }
}

// Global error handler for axios responses
export function handleApiError(error: AxiosError): never {
  if (error.response) {
    // Server responded with error status
    const status = error.response.status;
    const data = error.response.data as {
      detail?: string;
      message?: string;
      code?: string;
    };
    const message = data?.detail || data?.message || error.message;

    throw new ApiException(message, status, data?.code);
  } else if (error.request) {
    // Request was made but no response received
    throw new ApiException(
      "Network error: Unable to connect to server",
      0,
      "NETWORK_ERROR",
    );
  } else {
    // Something else happened
    throw new ApiException(error.message, 0, "UNKNOWN_ERROR");
  }
}

// ===========================
// API Client Instance
// ===========================

// Create axios instance with default configuration
export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: API_TIMEOUT,
  headers: {
    "Content-Type": "application/json",
    Accept: "application/json",
  },
});

// Add request interceptor for mobile compatibility
apiClient.interceptors.request.use(
  (config) => {
    // Add mobile-specific headers if on mobile device
    const isMobile =
      /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(
        navigator.userAgent,
      );

    if (isMobile) {
      // Increase timeout for mobile networks
      config.timeout = Math.max(config.timeout || 30000, 45000);
    }

    return config;
  },
  (error) => {
    return Promise.reject(error);
  },
);

// Add response interceptor for better error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.code === "ECONNABORTED") {
      console.error(
        "Request timeout - this may be due to slow network connection",
      );
    }
    return Promise.reject(error);
  },
); 