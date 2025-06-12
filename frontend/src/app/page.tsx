'use client';

import { useState } from 'react';
import URLInputPanel from '@/components/URLInputPanel';
import TrimPanel from '@/components/TrimPanel';
import DownloadModal from '@/components/DownloadModal';
import QueueFullErrorBanner from '@/components/QueueFullErrorBanner';
import ProgressBar from '@/components/ProgressBar';
import { useToast } from '@/components/ToastProvider';
import useJobPoller from '@/hooks/useJobPoller';
import { fetchVideoMetadata, createJob, type VideoMetadata } from '@/lib/api';

type AppState = 
  | { phase: 'idle' }
  | { phase: 'loading-metadata'; url: string }
  | { phase: 'trim'; metadata: VideoMetadata }
  | { phase: 'processing'; metadata: VideoMetadata; jobId: string }
  | { phase: 'download'; metadata: VideoMetadata; downloadUrl: string }
  | { phase: 'queue-full'; metadata: VideoMetadata };

export default function Home() {
  const { pushToast } = useToast();
  const [state, setState] = useState<AppState>({ phase: 'idle' });
  
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
      console.log('Making API request to:', `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/metadata`);
      const metadata = await fetchVideoMetadata(url);
      console.log('API response received:', metadata);
      setState({ phase: 'trim', metadata });
      pushToast({ type: 'success', message: 'Video loaded successfully!' });
    } catch (error) {
      console.error('API request failed:', error);
      if (error instanceof Error) {
        console.error('Error message:', error.message);
        console.error('Error stack:', error.stack);
      }
      setState({ phase: 'idle' });
      
      // More detailed error message
      let errorMessage = 'Failed to load video. Please check the URL and try again.';
      if (error instanceof Error) {
        if (error.message.includes('CORS')) {
          errorMessage = 'CORS error: Backend not allowing frontend requests. Check server configuration.';
        } else if (error.message.includes('Network Error')) {
          errorMessage = 'Network error: Cannot connect to backend server. Is it running on port 8000?';
        } else if (error.message.includes('timeout')) {
          errorMessage = 'Request timeout: Backend is taking too long to respond.';
        } else {
          errorMessage = `Error: ${error.message}`;
        }
      }
      
      pushToast({ type: 'error', message: errorMessage });
    }
  };

  const handleTrimSubmit = async (params: { in: number; out: number; rights: boolean }) => {
    if (state.phase !== 'trim') return;

    try {
      const response = await createJob({
        url: state.metadata.url,
        in: params.in,
        out: params.out,
        rights: params.rights,
      });
      
      setState({
        phase: 'processing',
        metadata: state.metadata,
        jobId: response.jobId,
      });
    } catch (error) {
      pushToast({ type: 'error', message: 'Failed to start processing. Please try again.' });
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

  const resetToIdle = () => {
    setState({ phase: 'idle' });
  };

  return (
    <main className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="container mx-auto px-4 py-16">
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-4">
            Meme Maker
          </h1>
          <p className="text-lg text-gray-600 dark:text-gray-400 max-w-2xl mx-auto">
            Paste a video URL from YouTube, Instagram, Facebook, Threads, or Reddit.
            Trim your clip and download it instantly.
          </p>
        </div>

        {/* URL Input Phase */}
        {(state.phase === 'idle' || state.phase === 'loading-metadata') && (
          <URLInputPanel 
            onSubmit={handleUrlSubmit} 
            loading={state.phase === 'loading-metadata'}
          />
        )}

        {/* Trim Phase */}
        {state.phase === 'trim' && (
          <TrimPanel 
            jobMeta={state.metadata}
            onSubmit={handleTrimSubmit}
          />
        )}

        {/* Processing Phase */}
        {state.phase === 'processing' && (
          <div className="max-w-2xl mx-auto space-y-6">
            <div className="text-center">
              <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
                Processing your clip...
              </h3>
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
                {state.metadata.title}
              </p>
              <ProgressBar progress={pollerResult.progress} />
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">
                {pollerResult.status === 'queued' && 'Waiting in queue...'}
                {pollerResult.status === 'working' && 'Trimming video...'}
              </p>
            </div>
            <div className="text-center">
              <button
                onClick={resetToIdle}
                className="text-sm text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
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
        <div className="mt-12 text-center">
          <p className="text-sm text-gray-500 dark:text-gray-400">
            Maximum clip length: 3 minutes • Files self-destruct after download
          </p>
        </div>

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
