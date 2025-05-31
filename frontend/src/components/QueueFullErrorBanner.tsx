'use client';

import Notification from './Notification';

interface QueueFullErrorBannerProps {
  onDismiss?: () => void;
}

export default function QueueFullErrorBanner({ onDismiss }: QueueFullErrorBannerProps) {
  return (
    <Notification
      type="warning"
      title="Queue Full"
      message="Busy right now. Try again in a minute."
      position="banner"
      dismissible={!!onDismiss}
      onClose={onDismiss}
      data-cy="queue-full-banner"
    />
  );
} 