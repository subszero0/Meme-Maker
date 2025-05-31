'use client';

import { useState } from 'react';
import dynamic from 'next/dynamic';
import URLInputPanel from '@/components/URLInputPanel';
import QueueFullErrorBanner from '@/components/QueueFullErrorBanner';
import ProgressBar from '@/components/ProgressBar';
import RateLimitNotification, { useRateLimitNotification } from '@/components/RateLimitNotification';
import Footer from '@/components/Footer';
import { useToast } from '@/components/ToastProvider';
import useJobPoller from '@/hooks/useJobPoller';
import { fetchVideoMetadata, createJob, isRateLimitError, type VideoMetadata } from '@/lib/api';
import { formatTimeForAPI } from '@/lib/formatTime';

// Dynamically import TrimPanel since it's only needed after metadata is loaded
const TrimPanel = dynamic(() => import('@/components/TrimPanel'), {
  loading: () => (
    <div className="max-w-4xl mx-auto p-6 space-y-6">
      <div className="aspect-video bg-gray-200 dark:bg-gray-700 animate-pulse rounded-lg"></div>
      <div className="space-y-4">
        <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded animate-pulse"></div>
        <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded animate-pulse w-3/4"></div>
      </div>
    </div>
  )
});

// Dynamically import DownloadModal since it's only shown at the end
const DownloadModal = dynamic(() => import('@/components/DownloadModal'), {
  loading: () => <div className="fixed inset-0 bg-black bg-opacity-50" />
});

type AppState = 
  | { phase: 'idle' }
  | { phase: 'loading-metadata'; url: string }
  | { phase: 'trim'; metadata: VideoMetadata }
  | { phase: 'processing'; metadata: VideoMetadata; jobId: string }
  | { phase: 'download'; metadata: VideoMetadata; downloadUrl: string }
  | { phase: 'queue-full'; metadata: VideoMetadata };

export default function Home() {
  const { pushToast } = useToast();
  const { notification, showNotification, clearNotification } = useRateLimitNotification();
  const [state, setState] = useState<AppState>({ phase: 'idle' });
  const [isRetryDisabled, setIsRetryDisabled] = useState(false);
  
  const jobId = state.phase === 'processing' ? state.jobId : null;
  const pollerResult = useJobPoller(jobId);

  // Handle job polling results
  if (state.phase === 'processing' && pollerResult.status === 'done' && pollerResult.url) {
    setState({
      phase: 'download',
      metadata: state.metadata,
      downloadUrl: pollerResult.url,
    });
  } else if (state.phase === 'processing' && pollerResult.status === 'error' && pollerResult.errorCode === 'QUEUE_FULL') {
    setState({
      phase: 'queue-full',
      metadata: state.metadata,
    });
  }

  const handleUrlSubmit = async (url: string) => {
    setState({ phase: 'loading-metadata', url });
    
    try {
      const metadata = await fetchVideoMetadata(url);
      setState({ phase: 'trim', metadata });
      pushToast({ type: 'success', message: 'Video loaded successfully!' });
    } catch (error) {
      setState({ phase: 'idle' });
      
      if (isRateLimitError(error)) {
        showNotification(error.message, error.retryAfter, error.limitType);
        setIsRetryDisabled(true);
      } else {
        pushToast({ type: 'error', message: 'Failed to load video. Please check the URL and try again.' });
      }
    }
  };

  const handleTrimSubmit = async (params: { in: number; out: number; rights: boolean }) => {
    if (state.phase !== 'trim') return;

    try {
      const response = await createJob({
        url: state.metadata.url,
        start: formatTimeForAPI(params.in),
        end: formatTimeForAPI(params.out),
        accepted_terms: params.rights,
      });
      
      setState({
        phase: 'processing',
        metadata: state.metadata,
        jobId: response.jobId,
      });
    } catch (error) {
      if (isRateLimitError(error)) {
        showNotification(error.message, error.retryAfter, error.limitType);
        setIsRetryDisabled(true);
      } else {
        pushToast({ type: 'error', message: 'Failed to start processing. Please try again.' });
      }
    }
  };

  const handleDownloadClose = () => {
    setState({ phase: 'idle' });
  };

  const handleQueueFullDismiss = () => {
    if (state.phase === 'queue-full') {
      setState({ phase: 'trim', metadata: state.metadata });
    }
  };

  const handleRateLimitRetryAvailable = () => {
    setIsRetryDisabled(false);
    clearNotification();
    pushToast({ 
      type: 'info', 
      message: 'Rate limit has expired. You can now make requests again.' 
    });
  };

  const handleRateLimitDismiss = () => {
    clearNotification();
  };

  const resetToIdle = () => {
    setState({ phase: 'idle' });
  };

  return (
    <main className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="container mx-auto px-4 py-16">
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-text-primary dark:text-white mb-4">
            Meme Maker
          </h1>
          <p className="text-lg text-text-secondary dark:text-text-secondary max-w-2xl mx-auto">
            Paste a video URL from YouTube, Instagram, Facebook, Threads, or Reddit.
            Trim your clip and download it instantly.
          </p>
        </div>

        {/* Rate Limit Notification */}
        {notification && (
          <div className="mb-8">
            <RateLimitNotification
              message={notification.message}
              retryAfter={notification.retryAfter}
              limitType={notification.limitType}
              onRetryAvailable={handleRateLimitRetryAvailable}
              onDismiss={handleRateLimitDismiss}
            />
          </div>
        )}

        {/* URL Input Phase */}
        {(state.phase === 'idle' || state.phase === 'loading-metadata') && (
          <URLInputPanel 
            onSubmit={handleUrlSubmit} 
            loading={state.phase === 'loading-metadata'}
            disabled={isRetryDisabled}
          />
        )}

        {/* Trim Phase */}
        {state.phase === 'trim' && (
          <TrimPanel 
            jobMeta={state.metadata}
            onSubmit={handleTrimSubmit}
            disabled={isRetryDisabled}
          />
        )}

        {/* Processing Phase */}
        {state.phase === 'processing' && (
          <div className="max-w-2xl mx-auto space-y-6">
            <div className="text-center">
              <h3 className="text-lg font-medium text-text-primary dark:text-white mb-2">
                Processing your clip...
              </h3>
              <p className="text-sm text-text-secondary dark:text-text-secondary mb-4">
                {state.metadata.title}
              </p>
              <ProgressBar progress={pollerResult.progress} />
              <p className="text-xs text-text-muted dark:text-text-muted mt-2">
                {pollerResult.status === 'queued' && 'Waiting in queue...'}
                {pollerResult.status === 'working' && 'Trimming video...'}
              </p>
            </div>
            <div className="text-center">
              <button
                onClick={resetToIdle}
                className="text-sm text-text-muted hover:text-text-secondary dark:text-text-muted dark:hover:text-text-secondary"
              >
                Cancel
              </button>
            </div>
          </div>
        )}

        {/* Queue Full Error */}
        {state.phase === 'queue-full' && (
          <div className="max-w-2xl mx-auto space-y-6">
            <QueueFullErrorBanner onDismiss={handleQueueFullDismiss} />
            <div className="text-center">
              <button
                onClick={resetToIdle}
                className="text-sm text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-200"
              >
                Start over
              </button>
            </div>
          </div>
        )}

        {/* Footer */}
        <Footer />

        {/* Download Modal */}
        {state.phase === 'download' && (
          <DownloadModal 
            url={state.downloadUrl}
            onClose={handleDownloadClose}
          />
        )}
      </div>
    </main>
  );
}
