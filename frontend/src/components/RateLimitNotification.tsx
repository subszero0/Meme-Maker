'use client';

import { useEffect, useState } from 'react';
import Notification from './Notification';
import { formatRetryTime } from '@/lib/api';

export interface RateLimitNotificationProps {
  message: string;
  retryAfter: number; // seconds
  limitType: 'global' | 'job_creation';
  onRetryAvailable?: () => void;
  onDismiss?: () => void;
}

export default function RateLimitNotification({
  message,
  retryAfter,
  limitType,
  onRetryAvailable,
  onDismiss
}: RateLimitNotificationProps) {
  const [timeLeft, setTimeLeft] = useState(retryAfter);

  useEffect(() => {
    if (timeLeft <= 0) {
      onRetryAvailable?.();
      return;
    }

    const timer = setTimeout(() => {
      setTimeLeft(prev => prev - 1);
    }, 1000);

    return () => clearTimeout(timer);
  }, [timeLeft, onRetryAvailable]);

  const getTitle = () => {
    if (limitType === 'job_creation') {
      return 'Job Creation Limit Reached';
    }
    return 'Rate Limit Exceeded';
  };

  const getType = () => {
    if (limitType === 'job_creation') {
      return 'warning' as const;
    }
    return 'error' as const;
  };

  return (
    <Notification
      type={getType()}
      title={getTitle()}
      message={message}
      position="banner"
      duration={0} // No auto-dismiss for rate limit notifications
      dismissible={!!onDismiss}
      onClose={onDismiss}
      countdown={{
        timeLeft,
        totalTime: retryAfter,
        label: 'Retry in'
      }}
      showProgress={true}
      data-cy="rate-limit-notification"
    />
  );
}

/**
 * Hook to manage rate limit notifications
 */
export function useRateLimitNotification() {
  const [notification, setNotification] = useState<{
    message: string;
    retryAfter: number;
    limitType: 'global' | 'job_creation';
  } | null>(null);

  const showNotification = (message: string, retryAfter: number, limitType: 'global' | 'job_creation') => {
    setNotification({ message, retryAfter, limitType });
  };

  const clearNotification = () => {
    setNotification(null);
  };

  return {
    notification,
    showNotification,
    clearNotification
  };
} 