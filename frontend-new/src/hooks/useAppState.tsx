import React, {
  createContext,
  useContext,
  useReducer,
  useCallback,
  useEffect,
} from "react";
import { MetadataResponse } from "@/lib/api";

// ===========================
// State Types and Interfaces
// ===========================

export type AppPhase =
  | "input"
  | "editing"
  | "processing"
  | "completed"
  | "error";

export interface AppState {
  // Current phase of the application
  phase: AppPhase;

  // Video data
  videoUrl: string;
  videoMetadata: MetadataResponse | null;

  // Clip selection
  clipStart: number;
  clipEnd: number;
  selectedFormatId: string | undefined;

  // Job processing
  currentJobId: string | null;
  downloadUrl: string | null;

  // Error handling
  error: string | null;
  lastError: {
    message: string;
    timestamp: number;
    phase: AppPhase;
  } | null;

  // UI state
  isVideoLoaded: boolean;

  // Analytics/tracking
  sessionId: string;
  startTime: number;
}

export type AppAction =
  | { type: "LOAD_VIDEO"; payload: { url: string; metadata: MetadataResponse } }
  | { type: "UPDATE_CLIP_RANGE"; payload: { start?: number; end?: number } }
  | { type: "SET_FORMAT"; payload: { formatId: string | undefined } }
  | { type: "START_PROCESSING"; payload: { jobId: string } }
  | { type: "PROCESSING_COMPLETE"; payload: { downloadUrl: string } }
  | { type: "SET_ERROR"; payload: { message: string } }
  | { type: "CLEAR_ERROR" }
  | { type: "RESET_APP" }
  | { type: "SET_PHASE"; payload: { phase: AppPhase } }
  | { type: "SET_VIDEO_LOADED"; payload: { loaded: boolean } }
  | { type: "RESTORE_STATE"; payload: { state: Partial<AppState> } };

// ===========================
// Initial State
// ===========================

const generateSessionId = (): string => {
  return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
};

const createInitialState = (): AppState => ({
  phase: "input",
  videoUrl: "",
  videoMetadata: null,
  clipStart: 0,
  clipEnd: 30,
  selectedFormatId: undefined,
  currentJobId: null,
  downloadUrl: null,
  error: null,
  lastError: null,
  isVideoLoaded: false,
  sessionId: generateSessionId(),
  startTime: Date.now(),
});

// ===========================
// State Reducer
// ===========================

const appStateReducer = (state: AppState, action: AppAction): AppState => {
  console.log("🏪 AppState Action:", action.type, action.payload);

  switch (action.type) {
    case "LOAD_VIDEO":
      return {
        ...state,
        phase: "editing",
        videoUrl: action.payload.url,
        videoMetadata: action.payload.metadata,
        isVideoLoaded: true,
        clipStart: 0,
        clipEnd: Math.min(action.payload.metadata.duration, 30),
        selectedFormatId: undefined,
        currentJobId: null,
        downloadUrl: null,
        error: null,
      };

    case "UPDATE_CLIP_RANGE":
      return {
        ...state,
        clipStart: action.payload.start ?? state.clipStart,
        clipEnd: action.payload.end ?? state.clipEnd,
      };

    case "SET_FORMAT":
      return {
        ...state,
        selectedFormatId: action.payload.formatId,
      };

    case "START_PROCESSING":
      return {
        ...state,
        phase: "processing",
        currentJobId: action.payload.jobId,
        error: null,
      };

    case "PROCESSING_COMPLETE":
      return {
        ...state,
        phase: "completed",
        downloadUrl: action.payload.downloadUrl,
        currentJobId: null,
      };

    case "SET_ERROR":
      return {
        ...state,
        phase: "error",
        error: action.payload.message,
        lastError: {
          message: action.payload.message,
          timestamp: Date.now(),
          phase: state.phase,
        },
        currentJobId: null,
      };

    case "CLEAR_ERROR":
      return {
        ...state,
        error: null,
      };

    case "SET_PHASE":
      return {
        ...state,
        phase: action.payload.phase,
        error: action.payload.phase !== "error" ? null : state.error,
      };

    case "SET_VIDEO_LOADED":
      return {
        ...state,
        isVideoLoaded: action.payload.loaded,
      };

    case "RESET_APP":
      return {
        ...createInitialState(),
        sessionId: state.sessionId, // Keep session ID
      };

    case "RESTORE_STATE":
      return {
        ...state,
        ...action.payload.state,
      };

    default:
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      console.warn("🏪 AppState: Unknown action type:", (action as any).type);
      return state;
  }
};

// ===========================
// Context Setup
// ===========================

interface AppStateContextType {
  state: AppState;
  dispatch: React.Dispatch<AppAction>;

  // Convenience action creators
  loadVideo: (url: string, metadata: MetadataResponse) => void;
  updateClipRange: (start?: number, end?: number) => void;
  setFormat: (formatId: string | undefined) => void;
  startProcessing: (jobId: string) => void;
  completeProcessing: (downloadUrl: string) => void;
  setError: (message: string) => void;
  clearError: () => void;
  resetApp: () => void;
  setPhase: (phase: AppPhase) => void;
  setVideoLoaded: (loaded: boolean) => void;

  // State selectors
  canCreateClip: boolean;
  clipDuration: number;
  sessionDuration: number;
}

const AppStateContext = createContext<AppStateContextType | null>(null);

// ===========================
// Provider Component
// ===========================

interface AppStateProviderProps {
  children: React.ReactNode;
  enablePersistence?: boolean;
}

const STORAGE_KEY = "meme-maker-app-state";

export const AppStateProvider: React.FC<AppStateProviderProps> = ({
  children,
  enablePersistence = true,
}) => {
  const [state, dispatch] = useReducer(appStateReducer, createInitialState());

  // Load persisted state on mount
  useEffect(() => {
    if (enablePersistence) {
      try {
        const persistedState = localStorage.getItem(STORAGE_KEY);
        if (persistedState) {
          const parsed = JSON.parse(persistedState);
          // Only restore certain fields to avoid breaking the app
          const safeState = {
            sessionId: parsed.sessionId || state.sessionId,
            lastError: parsed.lastError,
          };
          dispatch({ type: "RESTORE_STATE", payload: { state: safeState } });
          console.log("🏪 AppState: Restored persisted state");
        }
      } catch (error) {
        console.warn("🏪 AppState: Failed to restore persisted state:", error);
      }
    }
  }, [enablePersistence, state.sessionId]);

  // Persist state changes
  useEffect(() => {
    if (enablePersistence) {
      try {
        // Only persist certain fields
        const persistState = {
          sessionId: state.sessionId,
          lastError: state.lastError,
          startTime: state.startTime,
        };
        localStorage.setItem(STORAGE_KEY, JSON.stringify(persistState));
      } catch (error) {
        console.warn("🏪 AppState: Failed to persist state:", error);
      }
    }
  }, [state.sessionId, state.lastError, state.startTime, enablePersistence]);

  // Action creators
  const loadVideo = useCallback((url: string, metadata: MetadataResponse) => {
    dispatch({ type: "LOAD_VIDEO", payload: { url, metadata } });
  }, []);

  const updateClipRange = useCallback((start?: number, end?: number) => {
    dispatch({ type: "UPDATE_CLIP_RANGE", payload: { start, end } });
  }, []);

  const setFormat = useCallback((formatId: string | undefined) => {
    dispatch({ type: "SET_FORMAT", payload: { formatId } });
  }, []);

  const startProcessing = useCallback((jobId: string) => {
    dispatch({ type: "START_PROCESSING", payload: { jobId } });
  }, []);

  const completeProcessing = useCallback((downloadUrl: string) => {
    dispatch({ type: "PROCESSING_COMPLETE", payload: { downloadUrl } });
  }, []);

  const setError = useCallback((message: string) => {
    dispatch({ type: "SET_ERROR", payload: { message } });
  }, []);

  const clearError = useCallback(() => {
    dispatch({ type: "CLEAR_ERROR" });
  }, []);

  const resetApp = useCallback(() => {
    dispatch({ type: "RESET_APP" });
  }, []);

  const setPhase = useCallback((phase: AppPhase) => {
    dispatch({ type: "SET_PHASE", payload: { phase } });
  }, []);

  const setVideoLoaded = useCallback((loaded: boolean) => {
    dispatch({ type: "SET_VIDEO_LOADED", payload: { loaded } });
  }, []);

  // Computed values
  const canCreateClip = React.useMemo(() => {
    const clipDuration = state.clipEnd - state.clipStart;
    return (
      state.videoMetadata &&
      clipDuration > 0 &&
      clipDuration <= 180 && // 3 minutes max
      state.selectedFormatId &&
      state.phase === "editing"
    );
  }, [
    state.videoMetadata,
    state.clipStart,
    state.clipEnd,
    state.selectedFormatId,
    state.phase,
  ]);

  const clipDuration = React.useMemo(() => {
    return state.clipEnd - state.clipStart;
  }, [state.clipStart, state.clipEnd]);

  const sessionDuration = React.useMemo(() => {
    return Date.now() - state.startTime;
  }, [state.startTime]);

  const contextValue = React.useMemo(
    () => ({
      state,
      dispatch,
      loadVideo,
      updateClipRange,
      setFormat,
      startProcessing,
      completeProcessing,
      setError,
      clearError,
      resetApp,
      setPhase,
      setVideoLoaded,
      canCreateClip,
      clipDuration,
      sessionDuration,
    }),
    [
      state,
      loadVideo,
      updateClipRange,
      setFormat,
      startProcessing,
      completeProcessing,
      setError,
      clearError,
      resetApp,
      setPhase,
      setVideoLoaded,
      canCreateClip,
      clipDuration,
      sessionDuration,
    ],
  );

  return (
    <AppStateContext.Provider value={contextValue}>
      {children}
    </AppStateContext.Provider>
  );
};

// ===========================
// Hook for using the context
// ===========================

export const useAppState = (): AppStateContextType => {
  const context = useContext(AppStateContext);
  if (!context) {
    throw new Error("useAppState must be used within an AppStateProvider");
  }
  return context;
};

// ===========================
// Utility hooks for specific aspects
// ===========================

export const useAppPhase = () => {
  const { state, setPhase } = useAppState();
  return { phase: state.phase, setPhase };
};

export const useVideoState = () => {
  const { state, loadVideo, setVideoLoaded } = useAppState();
  return {
    videoUrl: state.videoUrl,
    videoMetadata: state.videoMetadata,
    isVideoLoaded: state.isVideoLoaded,
    loadVideo,
    setVideoLoaded,
  };
};

export const useClipState = () => {
  const { state, updateClipRange, setFormat, canCreateClip, clipDuration } =
    useAppState();
  return {
    clipStart: state.clipStart,
    clipEnd: state.clipEnd,
    selectedFormatId: state.selectedFormatId,
    updateClipRange,
    setFormat,
    canCreateClip,
    clipDuration,
  };
};

export const useJobState = () => {
  const { state, startProcessing, completeProcessing } = useAppState();
  return {
    currentJobId: state.currentJobId,
    downloadUrl: state.downloadUrl,
    startProcessing,
    completeProcessing,
  };
};

export const useErrorState = () => {
  const { state, setError, clearError } = useAppState();
  return {
    error: state.error,
    lastError: state.lastError,
    setError,
    clearError,
  };
};
