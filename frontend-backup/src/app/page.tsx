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
  | { phase: 'queue-full'; metadata: VideoMetadata }
  | { phase: 'service-error'; error: string };

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
  } else if (state.phase === 'processing' && pollerResult.status === 'error') {
    if (pollerResult.errorCode === 'QUEUE_FULL') {
      setState({
        phase: 'queue-full',
        metadata: state.metadata,
      });
    } else if (pollerResult.errorCode === 'SERVICE_UNAVAILABLE') {
      setState({
        phase: 'service-error',
        error: 'Backend services are not running. Please start Docker services.'
      });
    }
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
      setState({ phase: 'idle' });
      
      // More detailed error message
      let errorMessage = 'Failed to load video. Please check the URL and try again.';
      if (error instanceof Error) {
        if (error.message.includes('CORS')) {
          errorMessage = 'CORS error: Backend not allowing frontend requests. Check server configuration.';
        } else if (error.message.includes('Network Error') || error.message.includes('ECONNREFUSED')) {
          setState({
            phase: 'service-error',
            error: 'Cannot connect to backend. Please ensure Docker Desktop is running and start services.'
          });
          return;
        } else if (error.message.includes('timeout')) {
          errorMessage = 'Request timeout: Backend is taking too long to respond.';
        } else {
          errorMessage = `Error: ${error.message}`;
        }
      }
      
      pushToast({ type: 'error', message: errorMessage });
    }
  };

  const handleTrimSubmit = async (params: { in: number; out: number; rights: boolean; formatId?: string }) => {
    if (state.phase !== 'trim') return;

    console.log('🏠 HomePage: Received trim submit with params:', params);

    try {
      const response = await createJob({
        url: state.metadata.url,
        in: params.in,
        out: params.out,
        rights: params.rights,
        formatId: params.formatId,
      });
      
      console.log('🏠 HomePage: Job created successfully:', response);
      
      setState({
        phase: 'processing',
        metadata: state.metadata,
        jobId: response.jobId,
      });
    } catch (error) {
      console.error('🏠 HomePage: Job creation failed:', error);
      if (error instanceof Error && (error.message.includes('Network Error') || error.message.includes('ECONNREFUSED'))) {
        setState({
          phase: 'service-error',
          error: 'Cannot connect to backend. Please ensure Docker services are running.'
        });
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

  const resetToIdle = () => {
    setState({ phase: 'idle' });
  };

  const handleServiceErrorRetry = () => {
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
                {pollerResult.stage || 
                  (pollerResult.status === 'queued' && 'Waiting in queue...') ||
                  (pollerResult.status === 'working' && 'Processing...')}
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

        {/* Service Error */}
        {state.phase === 'service-error' && (
          <div className="max-w-2xl mx-auto space-y-6">
            <div className="bg-red-50 border border-red-200 rounded-lg p-6">
              <div className="flex items-center mb-4">
                <div className="flex-shrink-0">
                  <svg className="h-5 w-5 text-red-600" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                  </svg>
                </div>
                <h3 className="ml-3 text-sm font-medium text-red-800">
                  Service Unavailable
                </h3>
              </div>
              <div className="text-sm text-red-700 mb-4">
                <p className="mb-2">{state.error}</p>
                <p className="font-medium">To fix this:</p>
                <ol className="list-decimal list-inside mt-2 space-y-1">
                  <li>Ensure Docker Desktop is running</li>
                  <li>Run: <code className="bg-red-100 px-2 py-1 rounded text-xs">docker-compose up -d</code></li>
                  <li>Or use the provided script: <code className="bg-red-100 px-2 py-1 rounded text-xs">./start-dev.bat</code></li>
                </ol>
              </div>
              <div className="flex space-x-3">
                <button
                  onClick={handleServiceErrorRetry}
                  className="bg-red-600 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500"
                >
                  Try Again
                </button>
                <a
                  href="/TROUBLESHOOTING.md"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="bg-white text-red-600 px-4 py-2 rounded-md text-sm font-medium border border-red-600 hover:bg-red-50 focus:outline-none focus:ring-2 focus:ring-red-500"
                >
                  View Troubleshooting Guide
                </a>
              </div>
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
