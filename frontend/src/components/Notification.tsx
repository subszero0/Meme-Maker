'use client';

import { useEffect, useState, ReactNode } from 'react';
import { motion } from 'framer-motion';
import { 
  CheckCircleIcon, 
  ExclamationCircleIcon, 
  InformationCircleIcon, 
  ExclamationTriangleIcon,
  XMarkIcon 
} from '@heroicons/react/24/outline';

export type NotificationType = 'success' | 'error' | 'info' | 'warning';
export type NotificationPosition = 'toast' | 'banner' | 'inline';

export interface NotificationProps {
  /** Notification type affecting styling and ARIA roles */
  type: NotificationType;
  /** Message content - can be string or React node */
  message: string | ReactNode;
  /** Auto-dismiss duration in milliseconds (default: 3000, 0 = no auto-dismiss) */
  duration?: number;
  /** Callback when notification is dismissed */
  onClose?: () => void;
  /** Position/layout variant */
  position?: NotificationPosition;
  /** Optional title for banner/inline notifications */
  title?: string;
  /** Additional CSS classes */
  className?: string;
  /** Show dismiss button */
  dismissible?: boolean;
  /** Countdown timer (for rate limiting notifications) */
  countdown?: {
    timeLeft: number;
    totalTime: number;
    label?: string;
  };
  /** Progress bar indicator */
  showProgress?: boolean;
  /** Unique identifier for testing */
  'data-cy'?: string;
}

// Style configurations for each notification type
const typeConfig = {
  success: {
    icon: CheckCircleIcon,
    iconEmoji: '✓',
    bg: 'bg-notification-success-bg dark:bg-green-900/20',
    border: 'border-notification-success-border dark:border-green-800',
    text: 'text-notification-success-text dark:text-green-300',
    iconColor: 'text-notification-success-icon dark:text-green-400',
    progress: 'bg-green-400',
    ariaRole: 'status' as const,
    ariaLive: 'polite' as const,
  },
  error: {
    icon: ExclamationCircleIcon,
    iconEmoji: '✕',
    bg: 'bg-notification-error-bg dark:bg-red-900/20',
    border: 'border-notification-error-border dark:border-red-800',
    text: 'text-notification-error-text dark:text-red-300',
    iconColor: 'text-notification-error-icon dark:text-red-400',
    progress: 'bg-red-400',
    ariaRole: 'alert' as const,
    ariaLive: 'assertive' as const,
  },
  info: {
    icon: InformationCircleIcon,
    iconEmoji: 'ℹ',
    bg: 'bg-notification-info-bg dark:bg-blue-900/20',
    border: 'border-notification-info-border dark:border-blue-800',
    text: 'text-notification-info-text dark:text-blue-300',
    iconColor: 'text-notification-info-icon dark:text-blue-400',
    progress: 'bg-blue-400',
    ariaRole: 'status' as const,
    ariaLive: 'polite' as const,
  },
  warning: {
    icon: ExclamationTriangleIcon,
    iconEmoji: '⚠',
    bg: 'bg-notification-warning-bg dark:bg-yellow-900/20',
    border: 'border-notification-warning-border dark:border-yellow-800',
    text: 'text-notification-warning-text dark:text-yellow-300',
    iconColor: 'text-notification-warning-icon dark:text-yellow-400',
    progress: 'bg-yellow-400',
    ariaRole: 'alert' as const,
    ariaLive: 'assertive' as const,
  },
};

// Position-specific styling
const positionConfig = {
  toast: {
    container: 'max-w-sm w-full mx-auto my-2 rounded-xl shadow-lg hover:shadow-xl transition-shadow duration-200',
    layout: 'p-4',
    animation: {
      initial: { opacity: 0, translateY: -8, scale: 0.95 },
      animate: { opacity: 1, translateY: 0, scale: 1 },
      exit: { opacity: 0, translateY: -8, scale: 0.95 },
    },
  },
  banner: {
    container: 'w-full rounded-xl shadow-sm overflow-hidden mb-4',
    layout: 'p-4',
    animation: {
      initial: { opacity: 0, translateY: -12, height: 0 },
      animate: { opacity: 1, translateY: 0, height: 'auto' },
      exit: { opacity: 0, translateY: -12, height: 0 },
    },
  },
  inline: {
    container: 'w-full rounded-lg border mt-1',
    layout: 'p-3',
    animation: {
      initial: { opacity: 0, height: 0 },
      animate: { opacity: 1, height: 'auto' },
      exit: { opacity: 0, height: 0 },
    },
  },
};

export default function Notification({
  type,
  message,
  duration = 3000,
  onClose,
  position = 'toast',
  title,
  className = '',
  dismissible = true,
  countdown,
  showProgress = false,
  'data-cy': dataCy = 'notification',
  ...props
}: NotificationProps) {
  const [isVisible, setIsVisible] = useState(true);
  const [isPaused, setIsPaused] = useState(false);
  
  const config = typeConfig[type];
  const posConfig = positionConfig[position];
  const IconComponent = config.icon;

  // Auto-dismiss logic with pause on hover/focus
  useEffect(() => {
    if (duration === 0 || !isVisible || isPaused) return;

    const timer = setTimeout(() => {
      handleClose();
    }, duration);

    return () => clearTimeout(timer);
  }, [duration, isVisible, isPaused]);

  const handleClose = () => {
    setIsVisible(false);
    // Delay onClose to allow exit animation
    setTimeout(() => {
      onClose?.();
    }, 200);
  };

  const handleMouseEnter = () => setIsPaused(true);
  const handleMouseLeave = () => setIsPaused(false);
  const handleFocus = () => setIsPaused(true);
  const handleBlur = () => setIsPaused(false);

  if (!isVisible) return null;

  return (
    <motion.div
      {...posConfig.animation}
      transition={{ 
        duration: 0.2,
        ease: 'easeOut'
      }}
      role={config.ariaRole}
      aria-live={config.ariaLive}
      data-cy={dataCy}
      className={`
        ${posConfig.container}
        ${config.bg}
        ${config.border}
        border
        ${className}
      `}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
      onFocus={handleFocus}
      onBlur={handleBlur}
      {...props}
    >
      {/* Progress bar for countdown/progress notifications */}
      {(showProgress || countdown) && (
        <div className="h-1 bg-gray-200 dark:bg-gray-700 relative">
          <motion.div
            className={config.progress}
            initial={{ width: 0 }}
            animate={{ 
              width: countdown 
                ? `${((countdown.totalTime - countdown.timeLeft) / countdown.totalTime) * 100}%`
                : showProgress ? '100%' : 0
            }}
            transition={{ duration: 0.5 }}
            style={{ height: '100%' }}
          />
        </div>
      )}

      <div className={posConfig.layout}>
        <div className="flex items-start">
          {/* Icon */}
          <div className="flex-shrink-0 mr-3">
            {position === 'toast' ? (
              <span className="text-lg font-bold">{config.iconEmoji}</span>
            ) : (
              <IconComponent className={`h-5 w-5 ${config.iconColor}`} aria-hidden="true" />
            )}
          </div>

          {/* Content */}
          <div className="flex-1 min-w-0">
            {title && (
              <h3 className={`text-sm font-semibold mb-1 ${config.text}`}>
                {title}
              </h3>
            )}
            
            <div className={`text-sm leading-relaxed ${config.text}`}>
              {typeof message === 'string' ? (
                <p className="font-medium">{message}</p>
              ) : (
                message
              )}
            </div>

            {/* Countdown display */}
            {countdown && (
              <div className="flex items-center mt-3 space-x-2">
                <span className="text-xs font-medium">{countdown.label || 'Retry in'}:</span>
                <div className={`
                  inline-flex items-center px-2 py-1 rounded-full text-xs font-mono font-bold
                  ${type === 'warning' ? 'bg-yellow-200 text-yellow-900 dark:bg-yellow-800 dark:text-yellow-100' : 
                    type === 'error' ? 'bg-red-200 text-red-900 dark:bg-red-800 dark:text-red-100' : 
                    'bg-gray-200 text-gray-900 dark:bg-gray-700 dark:text-gray-100'}
                `}>
                  {formatTime(countdown.timeLeft)}
                </div>
              </div>
            )}
          </div>

          {/* Dismiss button */}
          {dismissible && onClose && (
            <button
              onClick={handleClose}
              className="ml-auto flex-shrink-0 inline-flex items-center justify-center w-11 h-11 rounded-md opacity-70 hover:opacity-100 focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2 transition-opacity"
              aria-label="Close notification"
              data-cy={`${dataCy}-dismiss`}
            >
              {position === 'toast' ? (
                <span className="text-lg">×</span>
              ) : (
                <XMarkIcon className="h-4 w-4" />
              )}
            </button>
          )}
        </div>
      </div>
    </motion.div>
  );
}

/**
 * Helper function to format time in MM:SS format
 */
function formatTime(seconds: number): string {
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
}

/**
 * Convenience components for specific notification types
 */
export const SuccessNotification = (props: Omit<NotificationProps, 'type'>) => 
  <Notification type="success" {...props} />;

export const ErrorNotification = (props: Omit<NotificationProps, 'type'>) => 
  <Notification type="error" {...props} />;

export const InfoNotification = (props: Omit<NotificationProps, 'type'>) => 
  <Notification type="info" {...props} />;

export const WarningNotification = (props: Omit<NotificationProps, 'type'>) => 
  <Notification type="warning" {...props} />; 