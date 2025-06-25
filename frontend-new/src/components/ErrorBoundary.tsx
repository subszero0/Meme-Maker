import React, { Component, ErrorInfo, ReactNode } from "react";
import { AlertTriangle, RefreshCw, Bug, Copy, CheckCircle } from "lucide-react";

// ===========================
// Error Types and Interfaces
// ===========================

export interface ErrorDetails {
  message: string;
  stack?: string;
  componentStack?: string;
  timestamp: number;
  userAgent: string;
  url: string;
  sessionId?: string;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
  errorId: string | null;
  retryCount: number;
}

interface ErrorBoundaryProps {
  children: ReactNode;
  fallback?: ReactNode;
  onError?: (
    error: Error,
    errorInfo: ErrorInfo,
    errorDetails: ErrorDetails,
  ) => void;
  maxRetries?: number;
}

// ===========================
// Error Reporting Service
// ===========================

class ErrorReporter {
  private static instance: ErrorReporter;
  private errors: ErrorDetails[] = [];

  static getInstance(): ErrorReporter {
    if (!ErrorReporter.instance) {
      ErrorReporter.instance = new ErrorReporter();
    }
    return ErrorReporter.instance;
  }

  reportError(
    error: Error,
    componentStack?: string,
    additionalInfo?: Record<string, unknown>,
  ) {
    const errorDetails: ErrorDetails = {
      message: error.message,
      stack: error.stack,
      componentStack,
      timestamp: Date.now(),
      userAgent: navigator.userAgent,
      url: window.location.href,
      sessionId: this.getSessionId(),
      ...additionalInfo,
    };

    // Store error locally
    this.errors.push(errorDetails);
    this.persistErrors();

    // Log to console in development
    if (process.env.NODE_ENV === "development") {
      console.group("🐛 Error Report");
      console.error("Error:", error);
      console.log("Details:", errorDetails);
      console.groupEnd();
    }

    // In production, you would send this to an error tracking service
    // this.sendToErrorService(errorDetails);

    return errorDetails;
  }

  private getSessionId(): string {
    let sessionId = sessionStorage.getItem("error-session-id");
    if (!sessionId) {
      sessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
      sessionStorage.setItem("error-session-id", sessionId);
    }
    return sessionId;
  }

  private persistErrors() {
    try {
      // Keep only last 10 errors
      const recentErrors = this.errors.slice(-10);
      localStorage.setItem("meme-maker-errors", JSON.stringify(recentErrors));
    } catch (error) {
      console.warn("Failed to persist errors:", error);
    }
  }

  getRecentErrors(): ErrorDetails[] {
    try {
      const stored = localStorage.getItem("meme-maker-errors");
      return stored ? JSON.parse(stored) : [];
    } catch (error) {
      console.warn("Failed to retrieve stored errors:", error);
      return [];
    }
  }

  clearErrors() {
    this.errors = [];
    localStorage.removeItem("meme-maker-errors");
  }
}

// ===========================
// Error Boundary Component
// ===========================

export class ErrorBoundary extends Component<
  ErrorBoundaryProps,
  ErrorBoundaryState
> {
  private errorReporter = ErrorReporter.getInstance();

  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
      errorId: null,
      retryCount: 0,
    };
  }

  static getDerivedStateFromError(error: Error): Partial<ErrorBoundaryState> {
    return {
      hasError: true,
      error,
      errorId: `error_${Date.now()}_${Math.random().toString(36).substr(2, 5)}`,
    };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    const errorDetails = this.errorReporter.reportError(
      error,
      errorInfo.componentStack,
      {
        retryCount: this.state.retryCount,
        errorId: this.state.errorId,
      },
    );

    this.setState({ errorInfo });

    // Call custom error handler if provided
    this.props.onError?.(error, errorInfo, errorDetails);
  }

  handleRetry = () => {
    const maxRetries = this.props.maxRetries || 3;

    if (this.state.retryCount < maxRetries) {
      this.setState((prevState) => ({
        hasError: false,
        error: null,
        errorInfo: null,
        errorId: null,
        retryCount: prevState.retryCount + 1,
      }));
    } else {
      console.warn("Max retries reached, not retrying again");
    }
  };

  handleReload = () => {
    window.location.reload();
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <ErrorFallback
          error={this.state.error}
          errorInfo={this.state.errorInfo}
          errorId={this.state.errorId}
          retryCount={this.state.retryCount}
          maxRetries={this.props.maxRetries || 3}
          onRetry={this.handleRetry}
          onReload={this.handleReload}
        />
      );
    }

    return this.props.children;
  }
}

// ===========================
// Error Fallback Component
// ===========================

interface ErrorFallbackProps {
  error: Error | null;
  errorInfo: ErrorInfo | null;
  errorId: string | null;
  retryCount: number;
  maxRetries: number;
  onRetry: () => void;
  onReload: () => void;
}

const ErrorFallback: React.FC<ErrorFallbackProps> = ({
  error,
  errorInfo,
  errorId,
  retryCount,
  maxRetries,
  onRetry,
  onReload,
}) => {
  const [showDetails, setShowDetails] = React.useState(false);
  const [copied, setCopied] = React.useState(false);

  const handleCopyError = async () => {
    const errorText = [
      `Error ID: ${errorId}`,
      `Message: ${error?.message}`,
      `Stack: ${error?.stack}`,
      `Component Stack: ${errorInfo?.componentStack}`,
      `Timestamp: ${new Date().toISOString()}`,
      `User Agent: ${navigator.userAgent}`,
      `URL: ${window.location.href}`,
    ].join("\n\n");

    try {
      await navigator.clipboard.writeText(errorText);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.warn("Failed to copy error details:", err);
    }
  };

  const canRetry = retryCount < maxRetries;

  return (
    <div className="min-h-screen bg-gradient-to-br from-red-50 to-orange-50 flex items-center justify-center p-4">
      <div className="max-w-lg w-full bg-white rounded-2xl shadow-xl p-6 space-y-6">
        {/* Error Icon and Title */}
        <div className="text-center">
          <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <AlertTriangle className="w-8 h-8 text-red-500" />
          </div>
          <h1 className="text-2xl font-bold text-gray-800">
            Oops! Something went wrong
          </h1>
          <p className="text-gray-600 mt-2">
            We encountered an unexpected error. Don't worry, we're working on
            it!
          </p>
        </div>

        {/* Error Details */}
        <div className="bg-gray-50 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <h3 className="font-medium text-gray-800">Error Details</h3>
            <button
              onClick={() => setShowDetails(!showDetails)}
              className="text-sm text-gray-600 hover:text-gray-800"
            >
              {showDetails ? "Hide" : "Show"} Details
            </button>
          </div>

          {showDetails && (
            <div className="mt-3 space-y-2">
              <div className="text-sm">
                <span className="font-medium text-gray-700">Error ID:</span>
                <span className="ml-2 font-mono text-gray-600">{errorId}</span>
              </div>
              <div className="text-sm">
                <span className="font-medium text-gray-700">Message:</span>
                <span className="ml-2 text-gray-600">{error?.message}</span>
              </div>
              <div className="text-sm">
                <span className="font-medium text-gray-700">Attempts:</span>
                <span className="ml-2 text-gray-600">
                  {retryCount} / {maxRetries}
                </span>
              </div>
            </div>
          )}
        </div>

        {/* Action Buttons */}
        <div className="space-y-3">
          {canRetry && (
            <button
              onClick={onRetry}
              className="w-full bg-gradient-to-r from-orange-400 to-red-400 text-white font-bold py-3 px-6 rounded-xl shadow-lg hover:shadow-xl transition-all duration-300 flex items-center justify-center space-x-2"
            >
              <RefreshCw className="w-4 h-4" />
              <span>Try Again</span>
            </button>
          )}

          <button
            onClick={onReload}
            className="w-full bg-gray-600 text-white font-bold py-3 px-6 rounded-xl shadow-lg hover:shadow-xl transition-all duration-300 flex items-center justify-center space-x-2"
          >
            <RefreshCw className="w-4 h-4" />
            <span>Reload Page</span>
          </button>

          <button
            onClick={handleCopyError}
            className="w-full bg-white border-2 border-gray-300 text-gray-700 font-medium py-3 px-6 rounded-xl hover:bg-gray-50 transition-all duration-300 flex items-center justify-center space-x-2"
          >
            {copied ? (
              <>
                <CheckCircle className="w-4 h-4 text-green-500" />
                <span>Copied!</span>
              </>
            ) : (
              <>
                <Copy className="w-4 h-4" />
                <span>Copy Error Details</span>
              </>
            )}
          </button>
        </div>

        {/* Additional Info */}
        <div className="text-center text-sm text-gray-500 space-y-1">
          <p>🐛 This error has been logged for investigation</p>
          <p>
            💡 Try refreshing the page or contact support if the problem
            persists
          </p>
        </div>
      </div>
    </div>
  );
};

// ===========================
// Retry Hook
// ===========================

interface UseRetryOptions {
  maxRetries?: number;
  retryDelay?: number;
  onError?: (error: Error, attempt: number) => void;
}

export const useRetry = (options: UseRetryOptions = {}) => {
  const { maxRetries = 3, retryDelay = 1000, onError } = options;
  const [isRetrying, setIsRetrying] = React.useState(false);
  const [retryCount, setRetryCount] = React.useState(0);

  const retry = React.useCallback(
    async function <T>(
      operation: () => Promise<T>,
      customMaxRetries?: number,
    ): Promise<T> {
      const maxAttempts = customMaxRetries ?? maxRetries;
      let lastError: Error;

      for (let attempt = 0; attempt <= maxAttempts; attempt++) {
        try {
          setIsRetrying(attempt > 0);
          setRetryCount(attempt);

          if (attempt > 0) {
            await new Promise((resolve) =>
              setTimeout(resolve, retryDelay * attempt),
            );
          }

          const result = await operation();
          setIsRetrying(false);
          setRetryCount(0);
          return result;
        } catch (error) {
          lastError = error as Error;
          onError?.(lastError, attempt);

          if (attempt === maxAttempts) {
            setIsRetrying(false);
            throw lastError;
          }
        }
      }

      throw lastError!;
    },
    [maxRetries, retryDelay, onError],
  );

  return { retry, isRetrying, retryCount };
};

// ===========================
// Error Context Hook
// ===========================

interface ErrorContextType {
  reportError: (error: Error, additionalInfo?: Record<string, unknown>) => void;
  clearErrors: () => void;
  getRecentErrors: () => ErrorDetails[];
}

const ErrorContext = React.createContext<ErrorContextType | null>(null);

export const ErrorProvider: React.FC<{ children: ReactNode }> = ({
  children,
}) => {
  const errorReporter = React.useMemo(() => ErrorReporter.getInstance(), []);

  const reportError = React.useCallback(
    (error: Error, additionalInfo?: Record<string, unknown>) => {
      errorReporter.reportError(error, undefined, additionalInfo);
    },
    [errorReporter],
  );

  const clearErrors = React.useCallback(() => {
    errorReporter.clearErrors();
  }, [errorReporter]);

  const getRecentErrors = React.useCallback(() => {
    return errorReporter.getRecentErrors();
  }, [errorReporter]);

  const value = React.useMemo(
    () => ({
      reportError,
      clearErrors,
      getRecentErrors,
    }),
    [reportError, clearErrors, getRecentErrors],
  );

  return (
    <ErrorContext.Provider value={value}>{children}</ErrorContext.Provider>
  );
};

export const useErrorReporting = () => {
  const context = React.useContext(ErrorContext);
  if (!context) {
    throw new Error("useErrorReporting must be used within an ErrorProvider");
  }
  return context;
};
