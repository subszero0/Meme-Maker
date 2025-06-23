"use client";

import { useEffect } from "react";
import { motion } from "framer-motion";

export interface ToastData {
  id: string;
  type: "success" | "error" | "info";
  message: string;
  timestamp: number;
}

interface ToastProps {
  toast: ToastData;
  onDismiss: (id: string) => void;
}

const variants = {
  success: "bg-green-50 border-green-200 text-green-800",
  error: "bg-red-50 border-red-200 text-red-800",
  info: "bg-indigo-50 border-indigo-200 text-indigo-800",
};

const icons = {
  success: "✓",
  error: "✕",
  info: "ℹ",
};

export default function Toast({ toast, onDismiss }: ToastProps) {
  useEffect(() => {
    const timer = setTimeout(() => {
      onDismiss(toast.id);
    }, 4000);

    return () => clearTimeout(timer);
  }, [toast.id, onDismiss]);

  return (
    <motion.div
      initial={{ opacity: 0, translateY: -8, scale: 0.95 }}
      animate={{ opacity: 1, translateY: 0, scale: 1 }}
      exit={{ opacity: 0, translateY: -8, scale: 0.95 }}
      transition={{
        duration: 0.2,
        ease: "easeOut",
      }}
      style={
        {
          // Respect prefers-reduced-motion
          "--duration": "var(--motion-duration, 0.2s)",
        } as React.CSSProperties
      }
      role="status"
      aria-live="polite"
      data-testid="toast"
      className={`
        max-w-sm w-full mx-auto my-2 p-4 rounded-lg border shadow-lg
        ${variants[toast.type]}
        cursor-pointer hover:shadow-xl transition-shadow duration-200
      `}
      onClick={() => onDismiss(toast.id)}
    >
      <div className="flex items-start">
        <span className="flex-shrink-0 mr-3 text-lg font-bold">
          {icons[toast.type]}
        </span>
        <p className="text-sm font-medium leading-5">{toast.message}</p>
        <button
          onClick={(e) => {
            e.stopPropagation();
            onDismiss(toast.id);
          }}
          className="ml-auto flex-shrink-0 text-lg opacity-70 hover:opacity-100"
          aria-label="Dismiss notification"
        >
          ×
        </button>
      </div>
    </motion.div>
  );
}
