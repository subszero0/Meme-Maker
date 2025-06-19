import { describe, it, expect, beforeEach, vi } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

// Import hooks to test
import { useAppState, AppStateProvider } from '../hooks/useAppState';

// Mock all external dependencies that could cause hanging
vi.mock('../lib/api', () => ({
  metadataApi: {
    getBasicMetadata: vi.fn(() => Promise.resolve({ title: 'Test Video', duration: 120 })),
    getDetailedMetadata: vi.fn(() => Promise.resolve({ formats: [] })),
  },
  jobsApi: {
    createJob: vi.fn(() => Promise.resolve({ id: 'test-job', status: 'queued' })),
    getJob: vi.fn(() => Promise.resolve({ id: 'test-job', status: 'completed' })),
  },
  clipsApi: {
    deleteClip: vi.fn(() => Promise.resolve()),
  },
  healthApi: {
    check: vi.fn(() => Promise.resolve({ status: 'ok' })),
  },
  JobStatus: {
    QUEUED: 'queued',
    WORKING: 'working',
    DONE: 'completed',
    ERROR: 'error',
  },
}));

// Proper Test Wrapper with both QueryClient and AppStateProvider
const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false, staleTime: Infinity },
      mutations: { retry: false },
    },
  });

  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      <AppStateProvider enablePersistence={false}>
        {children}
      </AppStateProvider>
    </QueryClientProvider>
  );
};

describe('Hooks Fixed Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('useAppState Hook', () => {
    it('should initialize with default state', () => {
      const wrapper = createWrapper();
      const { result } = renderHook(() => useAppState(), { wrapper });

      expect(result.current.state.phase).toBe('input');
      expect(result.current.state.videoMetadata).toBeNull();
      expect(result.current.state.currentJobId).toBeNull();
      expect(result.current.state.error).toBeNull();
    });

    it('should provide action functions', () => {
      const wrapper = createWrapper();
      const { result } = renderHook(() => useAppState(), { wrapper });

      expect(typeof result.current.setPhase).toBe('function');
      expect(typeof result.current.loadVideo).toBe('function');
      expect(typeof result.current.startProcessing).toBe('function');
      expect(typeof result.current.setError).toBe('function');
      expect(typeof result.current.resetApp).toBe('function');
    });

    it('should update phase when setPhase is called', () => {
      const wrapper = createWrapper();
      const { result } = renderHook(() => useAppState(), { wrapper });

      expect(result.current.state.phase).toBe('input');
      
      // Update phase with act wrapper
      act(() => {
        result.current.setPhase('processing');
      });
      
      expect(result.current.state.phase).toBe('processing');
    });

    it('should load video when loadVideo is called', () => {
      const wrapper = createWrapper();
      const { result } = renderHook(() => useAppState(), { wrapper });

      const testMetadata = {
        title: 'Test Video',
        duration: 120,
        thumbnail_url: 'https://example.com/thumb.jpg',
        resolutions: ['720p', '480p', '360p'],
      };

      expect(result.current.state.videoMetadata).toBeNull();
      
      // Load video with act wrapper
      act(() => {
        result.current.loadVideo('https://example.com/video', testMetadata);
      });
      
      expect(result.current.state.videoMetadata).toEqual(testMetadata);
      expect(result.current.state.phase).toBe('editing');
    });

    it('should start processing when startProcessing is called', () => {
      const wrapper = createWrapper();
      const { result } = renderHook(() => useAppState(), { wrapper });

      const testJobId = 'test-job-123';

      expect(result.current.state.currentJobId).toBeNull();
      
      // Start processing with act wrapper
      act(() => {
        result.current.startProcessing(testJobId);
      });
      
      expect(result.current.state.currentJobId).toBe(testJobId);
      expect(result.current.state.phase).toBe('processing');
    });

    it('should update error when setError is called', () => {
      const wrapper = createWrapper();
      const { result } = renderHook(() => useAppState(), { wrapper });

      const testError = 'Something went wrong';

      expect(result.current.state.error).toBeNull();
      
      // Set error with act wrapper
      act(() => {
        result.current.setError(testError);
      });
      
      expect(result.current.state.error).toBe(testError);
      expect(result.current.state.phase).toBe('error');
    });

    it('should reset state when resetApp is called', () => {
      const wrapper = createWrapper();
      const { result } = renderHook(() => useAppState(), { wrapper });

      // Set some state first
      act(() => {
        result.current.setPhase('processing');
        result.current.setError('Test error');
      });

      // Verify state is set
      expect(result.current.state.phase).toBe('error'); // Should be 'error' because setError was called last
      expect(result.current.state.error).toBe('Test error');

      // Reset with act wrapper
      act(() => {
        result.current.resetApp();
      });

      // Verify state is reset
      expect(result.current.state.phase).toBe('input');
      expect(result.current.state.error).toBeNull();
    });
  });
}); 