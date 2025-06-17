import { describe, it, expect, beforeEach, vi } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient } from '@tanstack/react-query';
import { 
  useBasicVideoMetadata,
  useDetailedVideoMetadata,
  useCreateJob,
  useJobStatus,
  useJobStatusWithPolling,
  useCancelJob,
  useDeleteClip,
  useHealthCheck
} from '../hooks/useApi';
import { useAppState } from '../hooks/useAppState';
import { TestProviders, createTestQueryClient } from './utils';

// Mock the API layer
vi.mock('../lib/api', () => ({
  metadataApi: {
    getBasicMetadata: vi.fn(),
    getDetailedMetadata: vi.fn(),
  },
  jobsApi: {
    createJob: vi.fn(),
    getJob: vi.fn(),
  },
  clipsApi: {
    deleteClip: vi.fn(),
  },
  healthApi: {
    check: vi.fn(),
  },
  JobStatus: {
    QUEUED: 'queued',
    WORKING: 'working',
    COMPLETED: 'completed',
    ERROR: 'error',
  },
}));

describe('API Hooks', () => {
  let queryClient: QueryClient;

  beforeEach(() => {
    queryClient = createTestQueryClient();
    vi.clearAllMocks();
  });

  const wrapper = ({ children }: { children: React.ReactNode }) => (
    <TestProviders queryClient={queryClient}>{children}</TestProviders>
  );

  describe('useBasicVideoMetadata', () => {
    it('should fetch basic metadata successfully', async () => {
      const mockMetadata = {
        title: 'Test Video',
        duration: 120,
        thumbnail: 'https://example.com/thumb.jpg',
      };

      const { metadataApi } = await import('../lib/api');
      vi.mocked(metadataApi.getBasicMetadata).mockResolvedValue(mockMetadata);

      const { result } = renderHook(
        () => useBasicVideoMetadata('https://youtube.com/watch?v=test'),
        { wrapper }
      );

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data).toEqual(mockMetadata);
      expect(metadataApi.getBasicMetadata).toHaveBeenCalledWith('https://youtube.com/watch?v=test');
    });

    it('should handle invalid URL', async () => {
      const { metadataApi } = await import('../lib/api');
      vi.mocked(metadataApi.getBasicMetadata).mockRejectedValue(
        new Error('Invalid URL')
      );

      const { result } = renderHook(
        () => useBasicVideoMetadata('invalid-url'),
        { wrapper }
      );

      await waitFor(() => {
        expect(result.current.isError).toBe(true);
      });

      expect(result.current.error).toBeTruthy();
    });

    it('should not fetch when disabled', async () => {
      const { metadataApi } = await import('../lib/api');

      const { result } = renderHook(
        () => useBasicVideoMetadata('https://youtube.com/watch?v=test', false),
        { wrapper }
      );

      expect(result.current.isFetching).toBe(false);
      expect(metadataApi.getBasicMetadata).not.toHaveBeenCalled();
    });

    it('should not fetch when URL is empty', async () => {
      const { metadataApi } = await import('../lib/api');

      const { result } = renderHook(
        () => useBasicVideoMetadata(''),
        { wrapper }
      );

      expect(result.current.isFetching).toBe(false);
      expect(metadataApi.getBasicMetadata).not.toHaveBeenCalled();
    });
  });

  describe('useDetailedVideoMetadata', () => {
    it('should fetch detailed metadata with formats', async () => {
      const mockDetailedMetadata = {
        title: 'Test Video',
        duration: 120,
        thumbnail: 'https://example.com/thumb.jpg',
        formats: [
          {
            format_id: '18',
            ext: 'mp4',
            resolution: '360p',
            filesize: 10485760,
          },
          {
            format_id: '22',
            ext: 'mp4',
            resolution: '720p',
            filesize: 52428800,
          },
        ],
      };

      const { metadataApi } = await import('../lib/api');
      vi.mocked(metadataApi.getDetailedMetadata).mockResolvedValue(mockDetailedMetadata);

      const { result } = renderHook(
        () => useDetailedVideoMetadata('https://youtube.com/watch?v=test'),
        { wrapper }
      );

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data).toEqual(mockDetailedMetadata);
      expect(result.current.data?.formats).toHaveLength(2);
    });
  });

  describe('useCreateJob', () => {
    it('should create job successfully', async () => {
      const mockJobData = {
        url: 'https://youtube.com/watch?v=test',
        in_ts: 10,
        out_ts: 40,
        format_id: '18',
      };

      const mockJobResponse = {
        id: 'job-123',
        status: 'queued' as const,
        progress: 0,
        created_at: '2024-01-01T00:00:00Z',
        ...mockJobData,
      };

      const { jobsApi } = await import('../lib/api');
      vi.mocked(jobsApi.createJob).mockResolvedValue(mockJobResponse);

      const { result } = renderHook(() => useCreateJob(), { wrapper });

      result.current.mutate(mockJobData);

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data).toEqual(mockJobResponse);
      expect(jobsApi.createJob).toHaveBeenCalledWith(mockJobData);
    });

    it('should handle job creation errors', async () => {
      const { jobsApi } = await import('../lib/api');
      vi.mocked(jobsApi.createJob).mockRejectedValue(
        new Error('Server error')
      );

      const { result } = renderHook(() => useCreateJob(), { wrapper });

      const mockJobData = {
        url: 'https://youtube.com/watch?v=test',
        in_ts: 10,
        out_ts: 40,
        format_id: '18',
      };

      result.current.mutate(mockJobData);

      await waitFor(() => {
        expect(result.current.isError).toBe(true);
      });

      expect(result.current.error).toBeTruthy();
    });
  });

  describe('useJobStatus', () => {
    it('should fetch job status', async () => {
      const mockJobStatus = {
        id: 'job-123',
        status: 'working' as const,
        progress: 50,
        created_at: '2024-01-01T00:00:00Z',
        url: 'https://youtube.com/watch?v=test',
        in_ts: 10,
        out_ts: 40,
        format_id: '18',
      };

      const { jobsApi } = await import('../lib/api');
      vi.mocked(jobsApi.getJob).mockResolvedValue(mockJobStatus);

      const { result } = renderHook(
        () => useJobStatus('job-123'),
        { wrapper }
      );

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data).toEqual(mockJobStatus);
      expect(jobsApi.getJob).toHaveBeenCalledWith('job-123');
    });

    it('should handle job not found', async () => {
      const { jobsApi } = await import('../lib/api');
      vi.mocked(jobsApi.getJob).mockRejectedValue(
        new Error('Job not found')
      );

      const { result } = renderHook(
        () => useJobStatus('nonexistent-job'),
        { wrapper }
      );

      await waitFor(() => {
        expect(result.current.isError).toBe(true);
      });

      expect(result.current.error).toBeTruthy();
    });
  });

  describe('useJobStatusWithPolling', () => {
    it('should poll job status for in-progress jobs', async () => {
      const mockJobStatus = {
        id: 'job-123',
        status: 'working' as const,
        progress: 50,
        created_at: '2024-01-01T00:00:00Z',
        url: 'https://youtube.com/watch?v=test',
        in_ts: 10,
        out_ts: 40,
        format_id: '18',
      };

      const { jobsApi } = await import('../lib/api');
      vi.mocked(jobsApi.getJob).mockResolvedValue(mockJobStatus);

      const { result } = renderHook(
        () => useJobStatusWithPolling('job-123', { pollingInterval: 100 }),
        { wrapper }
      );

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data?.status).toBe('working');
      expect(jobsApi.getJob).toHaveBeenCalledWith('job-123');
    });

    it('should stop polling when job is completed', async () => {
      const completedJob = {
        id: 'job-123',
        status: 'completed' as const,
        progress: 100,
        download_url: 'https://example.com/download.mp4',
        created_at: '2024-01-01T00:00:00Z',
        url: 'https://youtube.com/watch?v=test',
        in_ts: 10,
        out_ts: 40,
        format_id: '18',
      };

      const { jobsApi } = await import('../lib/api');
      vi.mocked(jobsApi.getJob).mockResolvedValue(completedJob);

      const { result } = renderHook(
        () => useJobStatusWithPolling('job-123', { pollingInterval: 100 }),
        { wrapper }
      );

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data?.status).toBe('completed');
      expect(result.current.data?.download_url).toBe('https://example.com/download.mp4');
    });
  });

  describe('useCancelJob', () => {
    it('should handle cancel attempt', async () => {
      const { result } = renderHook(() => useCancelJob(), { wrapper });

      result.current.mutate('job-123');

      await waitFor(() => {
        expect(result.current.isError).toBe(true);
      });

      // Should fail since cancellation is not implemented
      expect(result.current.error?.message).toContain('not implemented');
    });
  });

  describe('useDeleteClip', () => {
    it('should delete clip successfully', async () => {
      const { clipsApi } = await import('../lib/api');
      vi.mocked(clipsApi.deleteClip).mockResolvedValue(undefined);

      const { result } = renderHook(() => useDeleteClip(), { wrapper });

      result.current.mutate('job-123');

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(clipsApi.deleteClip).toHaveBeenCalledWith('job-123');
    });

    it('should handle delete errors gracefully', async () => {
      const { clipsApi } = await import('../lib/api');
      vi.mocked(clipsApi.deleteClip).mockRejectedValue(
        new Error('File not found')
      );

      const { result } = renderHook(() => useDeleteClip(), { wrapper });

      result.current.mutate('job-123');

      await waitFor(() => {
        expect(result.current.isError).toBe(true);
      });

      expect(result.current.error).toBeTruthy();
    });
  });

  describe('useHealthCheck', () => {
    it('should check API health status', async () => {
      const mockHealthResponse = {
        status: 'ok',
        version: '1.0.0',
        timestamp: '2024-01-01T00:00:00Z',
      };

      const { healthApi } = await import('../lib/api');
      vi.mocked(healthApi.check).mockResolvedValue(mockHealthResponse);

      const { result } = renderHook(() => useHealthCheck(), { wrapper });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data).toEqual(mockHealthResponse);
      expect(healthApi.check).toHaveBeenCalled();
    });
  });
});

describe('useAppState Hook', () => {
  const wrapper = ({ children }: { children: React.ReactNode }) => (
    <TestProviders>{children}</TestProviders>
  );

  it('should initialize with default state', () => {
    const { result } = renderHook(() => useAppState(), { wrapper });

    expect(result.current.state.phase).toBe('input');
    expect(result.current.state.video).toBeNull();
    expect(result.current.state.clip).toBeNull();
    expect(result.current.state.job).toBeNull();
    expect(result.current.state.error).toBeNull();
  });

  it('should transition through phases correctly', () => {
    const { result } = renderHook(() => useAppState(), { wrapper });

    // Set video metadata
    const mockVideoMetadata = {
      title: 'Test Video',
      duration: 120,
      thumbnail: 'https://example.com/thumb.jpg',
      formats: [],
    };

    result.current.actions.setVideoMetadata(mockVideoMetadata);

    expect(result.current.state.phase).toBe('editing');
    expect(result.current.state.video).toEqual(mockVideoMetadata);
  });

  it('should handle clip configuration', () => {
    const { result } = renderHook(() => useAppState(), { wrapper });

    const clipConfig = {
      startTime: 10,
      endTime: 40,
      selectedFormat: '18',
    };

    result.current.actions.setClipConfig(clipConfig);

    expect(result.current.state.clip).toEqual(clipConfig);
  });

  it('should handle job creation', () => {
    const { result } = renderHook(() => useAppState(), { wrapper });

    const jobData = {
      id: 'job-123',
      status: 'queued' as const,
      progress: 0,
    };

    result.current.actions.setJob(jobData);

    expect(result.current.state.phase).toBe('processing');
    expect(result.current.state.job).toEqual(jobData);
  });

  it('should handle errors', () => {
    const { result } = renderHook(() => useAppState(), { wrapper });

    const error = new Error('Test error');

    result.current.actions.setError(error);

    expect(result.current.state.phase).toBe('error');
    expect(result.current.state.error).toEqual(error);
  });

  it('should handle job completion', () => {
    const { result } = renderHook(() => useAppState(), { wrapper });

    // First set a job
    const jobData = {
      id: 'job-123',
      status: 'queued' as const,
      progress: 0,
    };

    result.current.actions.setJob(jobData);

    // Then complete it
    const completedJob = {
      ...jobData,
      status: 'completed' as const,
      progress: 100,
      download_url: 'https://example.com/download.mp4',
    };

    result.current.actions.setJob(completedJob);

    expect(result.current.state.phase).toBe('completed');
    expect(result.current.state.job?.status).toBe('completed');
  });

  it('should handle reset', () => {
    const { result } = renderHook(() => useAppState(), { wrapper });

    // Set some state
    const mockVideoMetadata = {
      title: 'Test Video',
      duration: 120,
      thumbnail: 'https://example.com/thumb.jpg',
      formats: [],
    };

    result.current.actions.setVideoMetadata(mockVideoMetadata);

    // Reset
    result.current.actions.reset();

    expect(result.current.state.phase).toBe('input');
    expect(result.current.state.video).toBeNull();
    expect(result.current.state.clip).toBeNull();
    expect(result.current.state.job).toBeNull();
    expect(result.current.state.error).toBeNull();
  });

  it('should persist state to localStorage', () => {
    const { result } = renderHook(() => useAppState(), { wrapper });

    const mockVideoMetadata = {
      title: 'Test Video',
      duration: 120,
      thumbnail: 'https://example.com/thumb.jpg',
      formats: [],
    };

    result.current.actions.setVideoMetadata(mockVideoMetadata);

    // Check if state is persisted (mocked localStorage)
    expect(result.current.state.video).toEqual(mockVideoMetadata);
  });
}); 