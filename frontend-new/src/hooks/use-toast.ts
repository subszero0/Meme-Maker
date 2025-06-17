import * as React from "react"
import { CheckCircle, AlertCircle, Info, AlertTriangle } from "lucide-react"

import type {
  ToastActionElement,
  ToastProps,
} from "@/components/ui/toast"

const TOAST_LIMIT = 3
const TOAST_REMOVE_DELAY = 5000

// ===========================
// Enhanced Toast Types
// ===========================

export type ToastType = 'default' | 'success' | 'error' | 'warning' | 'info';

type ToasterToast = ToastProps & {
  id: string
  title?: React.ReactNode
  description?: React.ReactNode
  action?: ToastActionElement
  type?: ToastType
  duration?: number
  persistent?: boolean
}

const actionTypes = {
  ADD_TOAST: "ADD_TOAST",
  UPDATE_TOAST: "UPDATE_TOAST",
  DISMISS_TOAST: "DISMISS_TOAST",
  REMOVE_TOAST: "REMOVE_TOAST",
} as const

let count = 0

function genId() {
  count = (count + 1) % Number.MAX_SAFE_INTEGER
  return count.toString()
}

type ActionType = typeof actionTypes

type Action =
  | {
      type: ActionType["ADD_TOAST"]
      toast: ToasterToast
    }
  | {
      type: ActionType["UPDATE_TOAST"]
      toast: Partial<ToasterToast>
    }
  | {
      type: ActionType["DISMISS_TOAST"]
      toastId?: ToasterToast["id"]
    }
  | {
      type: ActionType["REMOVE_TOAST"]
      toastId?: ToasterToast["id"]
    }

interface State {
  toasts: ToasterToast[]
}

const toastTimeouts = new Map<string, ReturnType<typeof setTimeout>>()

const addToRemoveQueue = (toastId: string, duration?: number) => {
  if (toastTimeouts.has(toastId)) {
    return
  }

  const timeout = setTimeout(() => {
    toastTimeouts.delete(toastId)
    dispatch({
      type: "REMOVE_TOAST",
      toastId: toastId,
    })
  }, duration || TOAST_REMOVE_DELAY)

  toastTimeouts.set(toastId, timeout)
}

export const reducer = (state: State, action: Action): State => {
  switch (action.type) {
    case "ADD_TOAST":
      return {
        ...state,
        toasts: [action.toast, ...state.toasts].slice(0, TOAST_LIMIT),
      }

    case "UPDATE_TOAST":
      return {
        ...state,
        toasts: state.toasts.map((t) =>
          t.id === action.toast.id ? { ...t, ...action.toast } : t
        ),
      }

    case "DISMISS_TOAST": {
      const { toastId } = action

      // ! Side effects ! - This could be extracted into a dismissToast() action,
      // but I'll keep it here for simplicity
      if (toastId) {
        addToRemoveQueue(toastId)
      } else {
        state.toasts.forEach((toast) => {
          addToRemoveQueue(toast.id)
        })
      }

      return {
        ...state,
        toasts: state.toasts.map((t) =>
          t.id === toastId || toastId === undefined
            ? {
                ...t,
                open: false,
              }
            : t
        ),
      }
    }
    case "REMOVE_TOAST":
      if (action.toastId === undefined) {
        return {
          ...state,
          toasts: [],
        }
      }
      return {
        ...state,
        toasts: state.toasts.filter((t) => t.id !== action.toastId),
      }
  }
}

const listeners: Array<(state: State) => void> = []

let memoryState: State = { toasts: [] }

function dispatch(action: Action) {
  memoryState = reducer(memoryState, action)
  listeners.forEach((listener) => {
    listener(memoryState)
  })
}

// ===========================
// Enhanced Toast Configuration
// ===========================

const getToastConfig = (type: ToastType) => {
  switch (type) {
    case 'success':
      return {
        variant: 'default' as const,
        className: 'border-green-200 bg-green-50 text-green-800',
        iconType: 'success',
        duration: 4000,
      };
    case 'error':
      return {
        variant: 'destructive' as const,
        className: 'border-red-200 bg-red-50 text-red-800',
        iconType: 'error',
        duration: 6000,
      };
    case 'warning':
      return {
        variant: 'default' as const,
        className: 'border-yellow-200 bg-yellow-50 text-yellow-800',
        iconType: 'warning',
        duration: 5000,
      };
    case 'info':
      return {
        variant: 'default' as const,
        className: 'border-blue-200 bg-blue-50 text-blue-800',
        iconType: 'info',
        duration: 4000,
      };
    default:
      return {
        variant: 'default' as const,
        className: '',
        iconType: null,
        duration: TOAST_REMOVE_DELAY,
      };
  }
};

const getToastIcon = (iconType: string | null) => {
  switch (iconType) {
    case 'success':
      return React.createElement(CheckCircle, { className: "w-4 h-4 text-green-600" });
    case 'error':
      return React.createElement(AlertCircle, { className: "w-4 h-4 text-red-600" });
    case 'warning':
      return React.createElement(AlertTriangle, { className: "w-4 h-4 text-yellow-600" });
    case 'info':
      return React.createElement(Info, { className: "w-4 h-4 text-blue-600" });
    default:
      return null;
  }
};

type Toast = Omit<ToasterToast, "id">

function toast({ type = 'default', duration, persistent = false, ...props }: Toast) {
  const id = genId()
  const config = getToastConfig(type);
  const toastDuration = duration || (persistent ? 0 : config.duration);

  const update = (props: ToasterToast) =>
    dispatch({
      type: "UPDATE_TOAST",
      toast: { ...props, id },
    })
  const dismiss = () => dispatch({ type: "DISMISS_TOAST", toastId: id })

  // Enhanced title with icon
  const icon = getToastIcon(config.iconType);
  const enhancedTitle = icon ? React.createElement(
    'div',
    { className: "flex items-center space-x-2" },
    icon,
    React.createElement('span', {}, props.title)
  ) : props.title;

  dispatch({
    type: "ADD_TOAST",
    toast: {
      ...props,
      title: enhancedTitle,
      variant: config.variant,
      className: `${config.className} ${props.className || ''}`,
      id,
      type,
      duration: toastDuration,
      persistent,
      open: true,
      onOpenChange: (open) => {
        if (!open) dismiss()
      },
    },
  })

  // Auto-dismiss non-persistent toasts
  if (!persistent && toastDuration > 0) {
    addToRemoveQueue(id, toastDuration);
  }

  return {
    id: id,
    dismiss,
    update,
  }
}

// ===========================
// Convenience Toast Functions
// ===========================

function toastSuccess(title: string, description?: string, options?: Partial<Toast>) {
  return toast({
    type: 'success',
    title,
    description,
    ...options,
  });
}

function toastError(title: string, description?: string, options?: Partial<Toast>) {
  return toast({
    type: 'error',
    title,
    description,
    ...options,
  });
}

function toastWarning(title: string, description?: string, options?: Partial<Toast>) {
  return toast({
    type: 'warning',
    title,
    description,
    ...options,
  });
}

function toastInfo(title: string, description?: string, options?: Partial<Toast>) {
  return toast({
    type: 'info',
    title,
    description,
    ...options,
  });
}

function toastJobProgress(title: string, description: string, progress?: number) {
  const progressElement = progress !== undefined ? React.createElement(
    'div',
    { className: "w-full bg-blue-200 rounded-full h-2" },
    React.createElement('div', {
      className: "bg-blue-600 h-2 rounded-full transition-all duration-500",
      style: { width: `${Math.min(100, Math.max(0, progress))}%` }
    })
  ) : null;

  const descriptionElement = React.createElement(
    'div',
    { className: "space-y-2" },
    React.createElement('div', {}, description),
    progressElement
  );

  return toast({
    type: 'info',
    title,
    description: descriptionElement,
    persistent: true,
  });
}

function useToast() {
  const [state, setState] = React.useState<State>(memoryState)

  React.useEffect(() => {
    listeners.push(setState)
    return () => {
      const index = listeners.indexOf(setState)
      if (index > -1) {
        listeners.splice(index, 1)
      }
    }
  }, [state])

  return {
    ...state,
    toast,
    toastSuccess,
    toastError,
    toastWarning,
    toastInfo,
    toastJobProgress,
    dismiss: (toastId?: string) => dispatch({ type: "DISMISS_TOAST", toastId }),
    dismissAll: () => dispatch({ type: "DISMISS_TOAST" }),
  }
}

// ===========================
// Application-Specific Toast Hooks
// ===========================

export const useVideoToasts = () => {
  const { toastSuccess, toastError, toastWarning, toastInfo } = useToast();

  return {
    videoLoaded: (title: string) => toastSuccess(
      "Video Loaded",
      `Successfully loaded: ${title}`,
    ),
    videoError: (error: string) => toastError(
      "Video Loading Failed",
      error,
    ),
    formatSelected: (format: string) => toastInfo(
      "Quality Selected",
      `Video quality set to ${format}`,
    ),
    clipValidation: (message: string) => toastWarning(
      "Invalid Clip Selection",
      message,
    ),
  };
};

export const useJobToasts = () => {
  const { toastSuccess, toastError, toastInfo, toastJobProgress, dismiss } = useToast();

  return {
    jobCreated: (jobId: string) => toastInfo(
      "Processing Started",
      `Your video is being processed (Job: ${jobId.slice(0, 8)}...)`,
    ),
    jobProgress: (title: string, stage: string, progress?: number) => toastJobProgress(
      title,
      stage,
      progress,
    ),
    jobCompleted: (downloadUrl: string) => toastSuccess(
      "Video Ready!",
      "Your clip has been processed successfully and is ready for download.",
    ),
    jobFailed: (error: string) => toastError(
      "Processing Failed",
      error,
      { persistent: true },
    ),
    jobCancelled: () => toastWarning(
      "Processing Cancelled",
      "Video processing was cancelled by user.",
    ),
    dismiss,
  };
};

export const useShareToasts = () => {
  const { toastSuccess, toastError, toastInfo } = useToast();

  return {
    downloadStarted: () => toastSuccess(
      "Download Started",
      "Your video file is being downloaded.",
    ),
    linkCopied: () => toastSuccess(
      "Link Copied",
      "Share link has been copied to clipboard.",
    ),
    shareOpened: (platform: string) => toastInfo(
      "Opening Share",
      `Redirecting to ${platform}...`,
    ),
    shareError: (platform: string, error: string) => toastError(
      `${platform} Share Failed`,
      error,
    ),
  };
};

export { useToast, toast, toastSuccess, toastError, toastWarning, toastInfo }
