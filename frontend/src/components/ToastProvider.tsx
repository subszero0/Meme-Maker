'use client';

import React, { createContext, useContext, useState, useCallback, ReactNode } from 'react';
import { createPortal } from 'react-dom';
import { AnimatePresence } from 'framer-motion';
import Notification, { NotificationType } from './Notification';

interface ToastData {
  id: string;
  type: NotificationType;
  message: string;
  timestamp: number;
}

interface ToastContextValue {
  pushToast: (toast: { type: NotificationType; message: string }) => void;
}

const ToastContext = createContext<ToastContextValue | null>(null);

export const useToast = () => {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error('useToast must be used within a ToastProvider');
  }
  return context;
};

interface ToastProviderProps {
  children: ReactNode;
}

export default function ToastProvider({ children }: ToastProviderProps) {
  const [toasts, setToasts] = useState<ToastData[]>([]);

  const removeToast = useCallback((id: string) => {
    setToasts(prev => prev.filter(toast => toast.id !== id));
  }, []);

  const pushToast = useCallback(({ type, message }: { type: NotificationType; message: string }) => {
    const now = Date.now();
    const id = `toast-${now}-${Math.random().toString(36).substr(2, 9)}`;

    // Debounce: Check for identical messages within 1 second
    const isDuplicate = toasts.some(toast => 
      toast.message === message && 
      toast.type === type && 
      now - toast.timestamp < 1000
    );

    if (isDuplicate) {
      return;
    }

    const newToast: ToastData = {
      id,
      type,
      message,
      timestamp: now
    };

    setToasts(prev => [...prev, newToast]);
  }, [toasts]);

  const contextValue: ToastContextValue = {
    pushToast
  };

  return (
    <ToastContext.Provider value={contextValue}>
      {children}
      {typeof window !== 'undefined' && createPortal(
        <div 
          className="fixed top-20 right-4 z-50 pointer-events-none"
          style={{ maxWidth: '24rem' }}
        >
          <AnimatePresence mode="popLayout">
            {toasts.map(toast => (
              <div key={toast.id} className="pointer-events-auto">
                <Notification
                  type={toast.type}
                  message={toast.message}
                  position="toast"
                  duration={4000}
                  onClose={() => removeToast(toast.id)}
                  data-cy="toast"
                />
              </div>
            ))}
          </AnimatePresence>
        </div>,
        document.body
      )}
    </ToastContext.Provider>
  );
} 