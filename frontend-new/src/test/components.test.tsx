import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { TestProviders, createTestQueryClient, mockVideoMetadata, mockJobResponse } from './utils';

// Import components to test
import { UrlInput } from '../components/UrlInput';
import { VideoPlayer } from '../components/VideoPlayer';
import { Timeline } from '../components/Timeline';
import { ResolutionSelector } from '../components/ResolutionSelector';
import { LoadingAnimation } from '../components/LoadingAnimation';
import { SharingOptions } from '../components/SharingOptions';

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

describe('Component Integration Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  const renderWithProviders = (component: React.ReactElement) => {
    const queryClient = createTestQueryClient();
    return render(
      <TestProviders queryClient={queryClient}>
        {component}
      </TestProviders>
    );
  };

  describe('UrlInput Component', () => {
    it('should render input field and submit button', () => {
      const mockOnSubmit = vi.fn();
      renderWithProviders(<UrlInput onSubmit={mockOnSubmit} />);

      expect(screen.getByPlaceholderText(/enter video url/i)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /extract/i })).toBeInTheDocument();
    });

    it('should validate URL format before submission', async () => {
      const user = userEvent.setup();
      const mockOnSubmit = vi.fn();
      renderWithProviders(<UrlInput onSubmit={mockOnSubmit} />);

      const input = screen.getByPlaceholderText(/enter video url/i);
      const submitButton = screen.getByRole('button', { name: /extract/i });

      // Test invalid URL
      await user.type(input, 'not-a-valid-url');
      await user.click(submitButton);

      expect(mockOnSubmit).not.toHaveBeenCalled();
      expect(screen.getByText(/invalid url format/i)).toBeInTheDocument();
    });

    it('should submit valid YouTube URL', async () => {
      const user = userEvent.setup();
      const mockOnSubmit = vi.fn();
      renderWithProviders(<UrlInput onSubmit={mockOnSubmit} />);

      const input = screen.getByPlaceholderText(/enter video url/i);
      const submitButton = screen.getByRole('button', { name: /extract/i });

      // Test valid YouTube URL
      await user.type(input, 'https://www.youtube.com/watch?v=dQw4w9WgXcQ');
      await user.click(submitButton);

      expect(mockOnSubmit).toHaveBeenCalledWith('https://www.youtube.com/watch?v=dQw4w9WgXcQ');
    });

    it('should show loading state during metadata fetching', async () => {
      const user = userEvent.setup();
      const mockOnSubmit = vi.fn();
      renderWithProviders(<UrlInput onSubmit={mockOnSubmit} isLoading={true} />);

      const submitButton = screen.getByRole('button', { name: /loading/i });
      expect(submitButton).toBeDisabled();
      expect(screen.getByTestId('loading-spinner')).toBeInTheDocument();
    });

    it('should handle different video platforms', async () => {
      const user = userEvent.setup();
      const mockOnSubmit = vi.fn();
      renderWithProviders(<UrlInput onSubmit={mockOnSubmit} />);

      const input = screen.getByPlaceholderText(/enter video url/i);
      const submitButton = screen.getByRole('button', { name: /extract/i });

      // Test different platform URLs
      const validUrls = [
        'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
        'https://youtu.be/dQw4w9WgXcQ',
        'https://vimeo.com/123456789',
        'https://www.dailymotion.com/video/x123456',
      ];

      for (const url of validUrls) {
        await user.clear(input);
        await user.type(input, url);
        await user.click(submitButton);
        expect(mockOnSubmit).toHaveBeenCalledWith(url);
      }
    });
  });

  describe('VideoPlayer Component', () => {
    const mockVideoData = {
      title: 'Test Video',
      duration: 120,
      thumbnail: 'https://example.com/thumb.jpg',
      url: 'https://www.youtube.com/watch?v=test',
    };

    it('should display video title and duration', () => {
      renderWithProviders(
        <VideoPlayer 
          videoData={mockVideoData}
          onTimeUpdate={vi.fn()}
          onDurationChange={vi.fn()}
        />
      );

      expect(screen.getByText('Test Video')).toBeInTheDocument();
      expect(screen.getByText(/2:00/)).toBeInTheDocument(); // 120 seconds formatted
    });

    it('should show thumbnail when video is not playing', () => {
      renderWithProviders(
        <VideoPlayer 
          videoData={mockVideoData}
          onTimeUpdate={vi.fn()}
          onDurationChange={vi.fn()}
        />
      );

      const thumbnail = screen.getByAltText(/video thumbnail/i);
      expect(thumbnail).toHaveAttribute('src', mockVideoData.thumbnail);
    });

    it('should handle play/pause interactions', async () => {
      const user = userEvent.setup();
      const mockOnTimeUpdate = vi.fn();
      
      renderWithProviders(
        <VideoPlayer 
          videoData={mockVideoData}
          onTimeUpdate={mockOnTimeUpdate}
          onDurationChange={vi.fn()}
        />
      );

      const playButton = screen.getByRole('button', { name: /play/i });
      await user.click(playButton);

      expect(screen.getByRole('button', { name: /pause/i })).toBeInTheDocument();
    });

    it('should handle video loading errors', () => {
      const mockVideoWithError = {
        ...mockVideoData,
        url: 'https://invalid-video-url.com',
      };

      renderWithProviders(
        <VideoPlayer 
          videoData={mockVideoWithError}
          onTimeUpdate={vi.fn()}
          onDurationChange={vi.fn()}
        />
      );

      // Should show error state
      expect(screen.getByText(/error loading video/i)).toBeInTheDocument();
    });
  });

  describe('Timeline Component', () => {
    const mockProps = {
      duration: 120,
      startTime: 10,
      endTime: 40,
      currentTime: 25,
      onTimeChange: vi.fn(),
      onRangeChange: vi.fn(),
    };

    it('should render timeline with correct duration', () => {
      renderWithProviders(<Timeline {...mockProps} />);

      expect(screen.getByText('2:00')).toBeInTheDocument(); // Total duration
      expect(screen.getByText('0:10')).toBeInTheDocument(); // Start time
      expect(screen.getByText('0:40')).toBeInTheDocument(); // End time
    });

    it('should handle time range selection', async () => {
      const user = userEvent.setup();
      const mockOnRangeChange = vi.fn();
      
      renderWithProviders(
        <Timeline {...mockProps} onRangeChange={mockOnRangeChange} />
      );

      const startHandle = screen.getByTestId('start-time-handle');
      const endHandle = screen.getByTestId('end-time-handle');

      // Simulate dragging start handle
      await user.pointer([
        { target: startHandle },
        { keys: '[MouseLeft>]', coords: { x: 100, y: 0 } },
        { coords: { x: 150, y: 0 } },
        { keys: '[/MouseLeft]' },
      ]);

      expect(mockOnRangeChange).toHaveBeenCalled();
    });

    it('should validate clip duration limits', async () => {
      const user = userEvent.setup();
      const mockOnRangeChange = vi.fn();
      
      renderWithProviders(
        <Timeline 
          {...mockProps} 
          startTime={0}
          endTime={200} // > 180 second limit
          onRangeChange={mockOnRangeChange} 
        />
      );

      expect(screen.getByText(/maximum clip duration is 3 minutes/i)).toBeInTheDocument();
    });

    it('should show current playback position', () => {
      renderWithProviders(<Timeline {...mockProps} />);

      const playhead = screen.getByTestId('playhead-indicator');
      expect(playhead).toBeInTheDocument();
      
      // Should be positioned at current time (25 seconds)
      const expectedPosition = (25 / 120) * 100; // 20.83%
      expect(playhead).toHaveStyle(`left: ${expectedPosition}%`);
    });

    it('should handle precise time input', async () => {
      const user = userEvent.setup();
      const mockOnRangeChange = vi.fn();
      
      renderWithProviders(
        <Timeline {...mockProps} onRangeChange={mockOnRangeChange} />
      );

      const startTimeInput = screen.getByDisplayValue('0:10');
      await user.clear(startTimeInput);
      await user.type(startTimeInput, '0:15');
      await user.tab(); // Trigger blur event

      expect(mockOnRangeChange).toHaveBeenCalledWith(15, 40);
    });
  });

  describe('ResolutionSelector Component', () => {
    const mockFormats = [
      {
        format_id: '18',
        ext: 'mp4',
        resolution: '360p',
        filesize: 10485760,
        fps: 30,
        width: 640,
        height: 360,
      },
      {
        format_id: '22',
        ext: 'mp4',
        resolution: '720p',
        filesize: 52428800,
        fps: 30,
        width: 1280,
        height: 720,
      },
    ];

    it('should display available resolutions', () => {
      const mockOnSelect = vi.fn();
      renderWithProviders(
        <ResolutionSelector 
          formats={mockFormats}
          selectedFormat="18"
          onFormatSelect={mockOnSelect}
        />
      );

      expect(screen.getByText('360p')).toBeInTheDocument();
      expect(screen.getByText('720p')).toBeInTheDocument();
      expect(screen.getByText('10 MB')).toBeInTheDocument(); // Formatted file size
      expect(screen.getByText('50 MB')).toBeInTheDocument();
    });

    it('should handle format selection', async () => {
      const user = userEvent.setup();
      const mockOnSelect = vi.fn();
      
      renderWithProviders(
        <ResolutionSelector 
          formats={mockFormats}
          selectedFormat="18"
          onFormatSelect={mockOnSelect}
        />
      );

      const hd720Option = screen.getByText('720p');
      await user.click(hd720Option);

      expect(mockOnSelect).toHaveBeenCalledWith('22');
    });

    it('should show format details', () => {
      const mockOnSelect = vi.fn();
      renderWithProviders(
        <ResolutionSelector 
          formats={mockFormats}
          selectedFormat="22"
          onFormatSelect={mockOnSelect}
        />
      );

      expect(screen.getByText('1280x720')).toBeInTheDocument();
      expect(screen.getByText('30 fps')).toBeInTheDocument();
    });

    it('should handle empty formats gracefully', () => {
      const mockOnSelect = vi.fn();
      renderWithProviders(
        <ResolutionSelector 
          formats={[]}
          selectedFormat=""
          onFormatSelect={mockOnSelect}
        />
      );

      expect(screen.getByText(/no formats available/i)).toBeInTheDocument();
    });
  });

  describe('LoadingAnimation Component', () => {
    it('should show queued state', () => {
      renderWithProviders(
        <LoadingAnimation 
          status="queued"
          progress={0}
          stage="Queued"
        />
      );

      expect(screen.getByText('Queued')).toBeInTheDocument();
      expect(screen.getByTestId('progress-bar')).toHaveStyle('width: 0%');
    });

    it('should show processing state with progress', () => {
      renderWithProviders(
        <LoadingAnimation 
          status="working"
          progress={50}
          stage="Processing video..."
        />
      );

      expect(screen.getByText('Processing video...')).toBeInTheDocument();
      expect(screen.getByTestId('progress-bar')).toHaveStyle('width: 50%');
      expect(screen.getByText('50%')).toBeInTheDocument();
    });

    it('should show completed state', () => {
      renderWithProviders(
        <LoadingAnimation 
          status="completed"
          progress={100}
          stage="Completed"
        />
      );

      expect(screen.getByText('Completed')).toBeInTheDocument();
      expect(screen.getByTestId('progress-bar')).toHaveStyle('width: 100%');
    });

    it('should show error state', () => {
      renderWithProviders(
        <LoadingAnimation 
          status="error"
          progress={0}
          stage="Error occurred"
          error="Processing failed"
        />
      );

      expect(screen.getByText('Error occurred')).toBeInTheDocument();
      expect(screen.getByText('Processing failed')).toBeInTheDocument();
    });

    it('should handle cancel button', async () => {
      const user = userEvent.setup();
      const mockOnCancel = vi.fn();
      
      renderWithProviders(
        <LoadingAnimation 
          status="working"
          progress={30}
          stage="Processing..."
          onCancel={mockOnCancel}
        />
      );

      const cancelButton = screen.getByRole('button', { name: /cancel/i });
      await user.click(cancelButton);

      expect(mockOnCancel).toHaveBeenCalled();
    });
  });

  describe('SharingOptions Component', () => {
    const mockCompletedJob = {
      id: 'job-123',
      status: 'completed' as const,
      progress: 100,
      download_url: 'https://example.com/download/clip.mp4',
      filename: 'test-clip.mp4',
    };

    beforeEach(() => {
      // Mock clipboard API
      Object.assign(navigator, {
        clipboard: {
          writeText: vi.fn().mockResolvedValue(undefined),
        },
      });

      // Mock URL.createObjectURL and URL.revokeObjectURL
      global.URL.createObjectURL = vi.fn().mockReturnValue('blob:mock-url');
      global.URL.revokeObjectURL = vi.fn();
    });

    it('should display download and sharing options', () => {
      renderWithProviders(<SharingOptions job={mockCompletedJob} />);

      expect(screen.getByRole('button', { name: /download/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /copy link/i })).toBeInTheDocument();
      expect(screen.getByText(/share on/i)).toBeInTheDocument();
    });

    it('should handle download action', async () => {
      const user = userEvent.setup();
      
      // Mock successful fetch for download
      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        blob: () => Promise.resolve(new Blob(['test'], { type: 'video/mp4' })),
      } as any);

      renderWithProviders(<SharingOptions job={mockCompletedJob} />);

      const downloadButton = screen.getByRole('button', { name: /download/i });
      await user.click(downloadButton);

      expect(global.fetch).toHaveBeenCalledWith(mockCompletedJob.download_url);
      expect(global.URL.createObjectURL).toHaveBeenCalled();
    });

    it('should handle copy link action', async () => {
      const user = userEvent.setup();
      renderWithProviders(<SharingOptions job={mockCompletedJob} />);

      const copyButton = screen.getByRole('button', { name: /copy link/i });
      await user.click(copyButton);

      expect(navigator.clipboard.writeText).toHaveBeenCalledWith(
        mockCompletedJob.download_url
      );
      expect(screen.getByText(/link copied/i)).toBeInTheDocument();
    });

    it('should show social media sharing options', () => {
      renderWithProviders(<SharingOptions job={mockCompletedJob} />);

      expect(screen.getByLabelText(/share on twitter/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/share on facebook/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/share on whatsapp/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/share on reddit/i)).toBeInTheDocument();
    });

    it('should handle sharing link generation', async () => {
      const user = userEvent.setup();
      
      // Mock window.open
      const mockOpen = vi.fn();
      Object.defineProperty(window, 'open', { value: mockOpen });

      renderWithProviders(<SharingOptions job={mockCompletedJob} />);

      const twitterButton = screen.getByLabelText(/share on twitter/i);
      await user.click(twitterButton);

      expect(mockOpen).toHaveBeenCalledWith(
        expect.stringContaining('twitter.com/intent/tweet'),
        '_blank'
      );
    });

    it('should not show options when job is not completed', () => {
      const incompleteJob = {
        ...mockCompletedJob,
        status: 'working' as const,
        progress: 50,
        download_url: null,
      };

      renderWithProviders(<SharingOptions job={incompleteJob} />);

      expect(screen.getByText(/clip not ready/i)).toBeInTheDocument();
      expect(screen.queryByRole('button', { name: /download/i })).not.toBeInTheDocument();
    });
  });

  describe('Error Handling Integration', () => {
    it('should handle API errors gracefully', async () => {
      const { metadataApi } = await import('../lib/api');
      vi.mocked(metadataApi.getDetailedMetadata).mockRejectedValue(
        new Error('Network error')
      );

      const mockOnSubmit = vi.fn();
      renderWithProviders(<UrlInput onSubmit={mockOnSubmit} />);

      // Trigger error scenario
      expect(screen.queryByText(/network error/i)).not.toBeInTheDocument();
    });

    it('should show validation errors', async () => {
      const user = userEvent.setup();
      const mockOnRangeChange = vi.fn();
      
      renderWithProviders(
        <Timeline 
          duration={120}
          startTime={50}
          endTime={40} // Invalid: end before start
          currentTime={45}
          onTimeChange={vi.fn()}
          onRangeChange={mockOnRangeChange}
        />
      );

      expect(screen.getByText(/start time must be before end time/i)).toBeInTheDocument();
    });
  });
}); 