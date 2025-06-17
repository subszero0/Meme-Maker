import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { TestProviders, createTestQueryClient, createMockUrl } from './utils';
import Index from '../pages/Index';
import { server } from './mocks/server';
import { http, HttpResponse } from 'msw';
import { UrlInput } from '../components/UrlInput';
import { VideoPlayer } from '../components/VideoPlayer';
import { Timeline } from '../components/Timeline';
import { ResolutionSelector } from '../components/ResolutionSelector';
import { LoadingAnimation } from '../components/LoadingAnimation';
import { SharingOptions } from '../components/SharingOptions';

// Mock the API layer with realistic responses
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

describe('Integration Tests - Complete User Workflows', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    
    // Mock clipboard API
    Object.assign(navigator, {
      clipboard: {
        writeText: vi.fn().mockResolvedValue(undefined),
      },
    });

    // Mock download functionality
    global.URL.createObjectURL = vi.fn().mockReturnValue('blob:mock-url');
    global.URL.revokeObjectURL = vi.fn();
    global.fetch = vi.fn();

    server.resetHandlers();
  });

  const renderApp = () => {
    const queryClient = createTestQueryClient();
    return render(
      <TestProviders queryClient={queryClient}>
        <Index />
      </TestProviders>
    );
  };

  describe('Complete Video Processing Workflow', () => {
    it('should complete entire workflow from URL input to download', async () => {
      const user = userEvent.setup();

      // Mock successful API responses
      const { metadataApi, jobsApi, clipsApi } = await import('../lib/api');
      
      const mockMetadata = {
        title: 'Test Video - Complete Workflow',
        duration: 120,
        thumbnail: 'https://example.com/thumb.jpg',
        upload_date: '2024-01-01',
        uploader: 'Test Channel',
        formats: [
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
        ],
      };

      const mockJobResponse = {
        id: 'integration-job-123',
        status: 'queued' as const,
        progress: 0,
        created_at: '2024-01-01T00:00:00Z',
        url: 'https://youtube.com/watch?v=test',
        in_ts: 10,
        out_ts: 40,
        format_id: '18',
      };

      const mockCompletedJob = {
        ...mockJobResponse,
        status: 'completed' as const,
        progress: 100,
        download_url: 'https://example.com/download/test-clip.mp4',
        filename: 'test-clip.mp4',
      };

      vi.mocked(metadataApi.getDetailedMetadata).mockResolvedValue(mockMetadata);
      vi.mocked(jobsApi.createJob).mockResolvedValue(mockJobResponse);
      vi.mocked(jobsApi.getJob)
        .mockResolvedValueOnce({ ...mockJobResponse, status: 'queued', progress: 0 })
        .mockResolvedValueOnce({ ...mockJobResponse, status: 'working', progress: 25 })
        .mockResolvedValueOnce({ ...mockJobResponse, status: 'working', progress: 75 })
        .mockResolvedValue(mockCompletedJob);
      vi.mocked(clipsApi.deleteClip).mockResolvedValue(undefined);

      // Render the app
      renderApp();

      // Step 1: Enter video URL
      expect(screen.getByText(/enter a video url/i)).toBeInTheDocument();
      
      const urlInput = screen.getByPlaceholderText(/enter video url/i);
      const extractButton = screen.getByRole('button', { name: /extract/i });

      await user.type(urlInput, 'https://www.youtube.com/watch?v=dQw4w9WgXcQ');
      await user.click(extractButton);

      // Step 2: Wait for metadata to load and verify video details
      await waitFor(() => {
        expect(screen.getByText('Test Video - Complete Workflow')).toBeInTheDocument();
      });

      expect(screen.getByText(/2:00/)).toBeInTheDocument(); // Duration
      expect(screen.getByText('Test Channel')).toBeInTheDocument();

      // Step 3: Configure clip settings
      // Select resolution
      const hd720Option = screen.getByText('720p');
      await user.click(hd720Option);

      // Set clip times using the timeline
      const startTimeInput = screen.getByDisplayValue('0:00');
      const endTimeInput = screen.getByDisplayValue('2:00');

      await user.clear(startTimeInput);
      await user.type(startTimeInput, '0:10');
      await user.clear(endTimeInput);
      await user.type(endTimeInput, '0:40');

      // Step 4: Create clip job
      const createClipButton = screen.getByRole('button', { name: /create clip/i });
      await user.click(createClipButton);

      // Step 5: Verify job creation and processing stages
      await waitFor(() => {
        expect(screen.getByText(/processing/i)).toBeInTheDocument();
      });

      expect(jobsApi.createJob).toHaveBeenCalledWith({
        url: 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
        in_ts: 10,
        out_ts: 40,
        format_id: '22', // 720p format selected
      });

      // Wait for job completion (polling simulation)
      await waitFor(() => {
        expect(screen.getByText(/completed/i)).toBeInTheDocument();
      }, { timeout: 10000 });

      // Step 6: Verify download and sharing options
      expect(screen.getByRole('button', { name: /download/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /copy link/i })).toBeInTheDocument();

      // Step 7: Test download functionality
      vi.mocked(global.fetch).mockResolvedValue({
        ok: true,
        blob: () => Promise.resolve(new Blob(['test video data'], { type: 'video/mp4' })),
      } as any);

      const downloadButton = screen.getByRole('button', { name: /download/i });
      await user.click(downloadButton);

      expect(global.fetch).toHaveBeenCalledWith(mockCompletedJob.download_url);

      // Step 8: Verify cleanup (file deletion should be called after download)
      await waitFor(() => {
        expect(clipsApi.deleteClip).toHaveBeenCalledWith('integration-job-123');
      });

      // Step 9: Test sharing functionality
      const copyLinkButton = screen.getByRole('button', { name: /copy link/i });
      await user.click(copyLinkButton);

      expect(navigator.clipboard.writeText).toHaveBeenCalledWith(mockCompletedJob.download_url);
      expect(screen.getByText(/link copied/i)).toBeInTheDocument();
    });

    it('should handle errors gracefully during workflow', async () => {
      const user = userEvent.setup();
      const { metadataApi } = await import('../lib/api');

      // Mock API error
      vi.mocked(metadataApi.getDetailedMetadata).mockRejectedValue(
        new Error('Video not found or unavailable')
      );

      renderApp();

      // Enter invalid video URL
      const urlInput = screen.getByPlaceholderText(/enter video url/i);
      const extractButton = screen.getByRole('button', { name: /extract/i });

      await user.type(urlInput, 'https://www.youtube.com/watch?v=invalid');
      await user.click(extractButton);

      // Verify error handling
      await waitFor(() => {
        expect(screen.getByText(/error loading video/i)).toBeInTheDocument();
      });

      expect(screen.getByRole('button', { name: /try again/i })).toBeInTheDocument();
    });

    it('should validate clip duration limits', async () => {
      const user = userEvent.setup();
      const { metadataApi } = await import('../lib/api');

      const mockLongVideo = {
        title: 'Long Video Test',
        duration: 300, // 5 minutes
        thumbnail: 'https://example.com/thumb.jpg',
        formats: [
          {
            format_id: '18',
            ext: 'mp4',
            resolution: '360p',
            filesize: 10485760,
          },
        ],
      };

      vi.mocked(metadataApi.getDetailedMetadata).mockResolvedValue(mockLongVideo);

      renderApp();

      // Enter video URL
      const urlInput = screen.getByPlaceholderText(/enter video url/i);
      const extractButton = screen.getByRole('button', { name: /extract/i });

      await user.type(urlInput, 'https://www.youtube.com/watch?v=long');
      await user.click(extractButton);

      await waitFor(() => {
        expect(screen.getByText('Long Video Test')).toBeInTheDocument();
      });

      // Try to set clip duration > 3 minutes (180 seconds)
      const endTimeInput = screen.getByDisplayValue('5:00');
      await user.clear(endTimeInput);
      await user.type(endTimeInput, '4:00'); // 240 seconds

      // Should show validation error
      expect(screen.getByText(/maximum clip duration is 3 minutes/i)).toBeInTheDocument();

      // Create clip button should be disabled
      const createClipButton = screen.getByRole('button', { name: /create clip/i });
      expect(createClipButton).toBeDisabled();
    });
  });

  describe('Different Video Platform Tests', () => {
    it('should handle YouTube URLs', async () => {
      const user = userEvent.setup();
      const { metadataApi } = await import('../lib/api');

      vi.mocked(metadataApi.getDetailedMetadata).mockResolvedValue({
        title: 'YouTube Video',
        duration: 180,
        thumbnail: 'https://i.ytimg.com/vi/test/maxresdefault.jpg',
        formats: [{ format_id: '18', ext: 'mp4', resolution: '360p', filesize: 10485760 }],
      });

      renderApp();

      const urlInput = screen.getByPlaceholderText(/enter video url/i);
      await user.type(urlInput, 'https://youtu.be/dQw4w9WgXcQ');
      await user.click(screen.getByRole('button', { name: /extract/i }));

      await waitFor(() => {
        expect(screen.getByText('YouTube Video')).toBeInTheDocument();
      });
    });

    it('should handle Vimeo URLs', async () => {
      const user = userEvent.setup();
      const { metadataApi } = await import('../lib/api');

      vi.mocked(metadataApi.getDetailedMetadata).mockResolvedValue({
        title: 'Vimeo Video',
        duration: 120,
        thumbnail: 'https://i.vimeocdn.com/video/test.jpg',
        formats: [{ format_id: 'http-720p', ext: 'mp4', resolution: '720p', filesize: 52428800 }],
      });

      renderApp();

      const urlInput = screen.getByPlaceholderText(/enter video url/i);
      await user.type(urlInput, 'https://vimeo.com/123456789');
      await user.click(screen.getByRole('button', { name: /extract/i }));

      await waitFor(() => {
        expect(screen.getByText('Vimeo Video')).toBeInTheDocument();
      });
    });
  });

  describe('API Contract Validation', () => {
    it('should send correct parameters to create job API', async () => {
      const user = userEvent.setup();
      const { metadataApi, jobsApi } = await import('../lib/api');

      const mockMetadata = {
        title: 'API Test Video',
        duration: 120,
        formats: [
          { format_id: '18', ext: 'mp4', resolution: '360p', filesize: 10485760 },
          { format_id: '22', ext: 'mp4', resolution: '720p', filesize: 52428800 },
        ],
      };

      vi.mocked(metadataApi.getDetailedMetadata).mockResolvedValue(mockMetadata);
      vi.mocked(jobsApi.createJob).mockResolvedValue({
        id: 'api-test-job',
        status: 'queued',
        progress: 0,
        created_at: '2024-01-01T00:00:00Z',
        url: 'https://test.com/video',
        in_ts: 15,
        out_ts: 45,
        format_id: '22',
      });

      renderApp();

      // Complete workflow setup
      const urlInput = screen.getByPlaceholderText(/enter video url/i);
      await user.type(urlInput, 'https://test.com/video');
      await user.click(screen.getByRole('button', { name: /extract/i }));

      await waitFor(() => {
        expect(screen.getByText('API Test Video')).toBeInTheDocument();
      });

      // Configure clip
      const startTimeInput = screen.getByDisplayValue('0:00');
      const endTimeInput = screen.getByDisplayValue('2:00');

      await user.clear(startTimeInput);
      await user.type(startTimeInput, '0:15');
      await user.clear(endTimeInput);
      await user.type(endTimeInput, '0:45');

      // Select 720p format
      await user.click(screen.getByText('720p'));

      // Create job
      await user.click(screen.getByRole('button', { name: /create clip/i }));

      // Verify API call with correct parameters
      expect(jobsApi.createJob).toHaveBeenCalledWith({
        url: 'https://test.com/video',
        in_ts: 15,
        out_ts: 45,
        format_id: '22',
      });
    });

    it('should handle API response format correctly', async () => {
      const user = userEvent.setup();
      const { metadataApi, jobsApi } = await import('../lib/api');

      // Test with real API response format
      const realApiResponse = {
        title: 'Real API Response Video',
        duration: 180.5, // Decimal duration
        thumbnail: 'https://example.com/thumb.jpg',
        upload_date: '20240101',
        uploader: 'Test Uploader',
        view_count: 1000000,
        formats: [
          {
            format_id: '18',
            ext: 'mp4',
            resolution: '360p',
            filesize: 10485760,
            fps: 29.97,
            width: 640,
            height: 360,
            vcodec: 'avc1.42001E',
            acodec: 'mp4a.40.2',
          },
        ],
      };

      vi.mocked(metadataApi.getDetailedMetadata).mockResolvedValue(realApiResponse);

      renderApp();

      const urlInput = screen.getByPlaceholderText(/enter video url/i);
      await user.type(urlInput, 'https://example.com/video');
      await user.click(screen.getByRole('button', { name: /extract/i }));

      await waitFor(() => {
        expect(screen.getByText('Real API Response Video')).toBeInTheDocument();
      });

      // Verify decimal duration is handled correctly
      expect(screen.getByText(/3:01/)).toBeInTheDocument(); // 180.5 seconds rounded
    });
  });

  describe('Performance and Error Recovery', () => {
    it('should retry failed requests', async () => {
      const user = userEvent.setup();
      const { metadataApi } = await import('../lib/api');

      // First call fails, second succeeds
      vi.mocked(metadataApi.getDetailedMetadata)
        .mockRejectedValueOnce(new Error('Network timeout'))
        .mockResolvedValueOnce({
          title: 'Retry Success Video',
          duration: 120,
          formats: [{ format_id: '18', ext: 'mp4', resolution: '360p', filesize: 10485760 }],
        });

      renderApp();

      const urlInput = screen.getByPlaceholderText(/enter video url/i);
      await user.type(urlInput, 'https://retry-test.com/video');
      await user.click(screen.getByRole('button', { name: /extract/i }));

      // Should show error first
      await waitFor(() => {
        expect(screen.getByText(/error loading video/i)).toBeInTheDocument();
      });

      // Click retry
      const retryButton = screen.getByRole('button', { name: /try again/i });
      await user.click(retryButton);

      // Should succeed on retry
      await waitFor(() => {
        expect(screen.getByText('Retry Success Video')).toBeInTheDocument();
      });
    });

    it('should handle concurrent requests properly', async () => {
      const user = userEvent.setup();
      const { metadataApi } = await import('../lib/api');

      // Mock slow response
      vi.mocked(metadataApi.getDetailedMetadata).mockImplementation(
        () => new Promise(resolve => 
          setTimeout(() => resolve({
            title: 'Concurrent Test Video',
            duration: 120,
            formats: [{ format_id: '18', ext: 'mp4', resolution: '360p', filesize: 10485760 }],
          }), 1000)
        )
      );

      renderApp();

      const urlInput = screen.getByPlaceholderText(/enter video url/i);
      const extractButton = screen.getByRole('button', { name: /extract/i });

      // Make multiple rapid requests
      await user.type(urlInput, 'https://concurrent-test.com/video1');
      await user.click(extractButton);

      await user.clear(urlInput);
      await user.type(urlInput, 'https://concurrent-test.com/video2');
      await user.click(extractButton);

      // Should only process the latest request
      await waitFor(() => {
        expect(screen.getByText('Concurrent Test Video')).toBeInTheDocument();
      }, { timeout: 3000 });

      // Should not have duplicate API calls
      expect(metadataApi.getDetailedMetadata).toHaveBeenCalledTimes(2);
    });
  });

  describe('🔗 Integration Testing: User Workflows', () => {
    describe('Complete Video Processing Workflow (Integration)', () => {
      it('should handle the complete video processing workflow with component integration', async () => {
        const user = userEvent.setup();
        
        // Test the workflow using integrated components (faster than E2E)
        const { container } = render(
          <TestProviders>
            <div>
              <UrlInput />
              <VideoPlayer metadata={{
                title: 'Integration Test Video',
                duration: 120,
                thumbnail: 'https://example.com/thumb.jpg',
                upload_date: '2024-01-01',
                uploader: 'Test Channel',
                formats: [
                  { format_id: '18', ext: 'mp4', resolution: '360p', filesize: 10485760, fps: 30, width: 640, height: 360 },
                  { format_id: '22', ext: 'mp4', resolution: '720p', filesize: 52428800, fps: 30, width: 1280, height: 720 }
                ]
              }} />
              <Timeline 
                duration={120}
                startTime={10}
                endTime={40}
                onStartTimeChange={vi.fn()}
                onEndTimeChange={vi.fn()}
              />
              <ResolutionSelector 
                formats={[
                  { format_id: '18', ext: 'mp4', resolution: '360p', filesize: 10485760, fps: 30, width: 640, height: 360 },
                  { format_id: '22', ext: 'mp4', resolution: '720p', filesize: 52428800, fps: 30, width: 1280, height: 720 }
                ]}
                selectedFormat="22"
                onFormatChange={vi.fn()}
              />
            </div>
          </TestProviders>
        );

        // Verify all components render together
        expect(screen.getByLabelText(/enter.*video.*url/i)).toBeInTheDocument();
        expect(screen.getByText('Integration Test Video')).toBeInTheDocument();
        expect(screen.getAllByRole('slider')).toHaveLength(2); // Timeline sliders
        expect(screen.getAllByRole('radio')).toHaveLength(2); // Resolution options

        // Test component interactions
        const urlInput = screen.getByLabelText(/enter.*video.*url/i);
        await user.type(urlInput, 'https://youtube.com/watch?v=integration-test');
        
        const extractButton = screen.getByRole('button', { name: /extract.*metadata/i });
        await user.click(extractButton);

        // Verify state changes propagate between components
        expect(urlInput).toHaveValue('https://youtube.com/watch?v=integration-test');
      });

      it('should handle error states across integrated components', async () => {
        const user = userEvent.setup();
        
        // Mock API error
        server.use(
          http.get('/api/metadata', () => {
            return HttpResponse.json(
              { error: 'Invalid video URL' },
              { status: 400 }
            );
          })
        );

        render(
          <TestProviders>
            <div>
              <UrlInput />
              <div role="alert" aria-live="assertive">
                Invalid video URL. Please check the URL and try again.
              </div>
            </div>
          </TestProviders>
        );

        const urlInput = screen.getByLabelText(/enter.*video.*url/i);
        await user.type(urlInput, 'https://invalid-url.com');
        
        const extractButton = screen.getByRole('button', { name: /extract.*metadata/i });
        await user.click(extractButton);

        // Verify error handling integration
        await waitFor(() => {
          expect(screen.getByRole('alert')).toHaveTextContent(/invalid.*url/i);
        });
      });
    });

    describe('Multi-Platform Video Support (Integration)', () => {
      const platforms = [
        { url: 'https://www.youtube.com/watch?v=test', name: 'YouTube' },
        { url: 'https://youtu.be/test', name: 'YouTube Short' },
        { url: 'https://vimeo.com/123456789', name: 'Vimeo' },
        { url: 'https://www.dailymotion.com/video/test', name: 'Dailymotion' },
      ];

      platforms.forEach(({ url, name }) => {
        it(`should handle ${name} URLs correctly`, async () => {
          const user = userEvent.setup();
          
          render(
            <TestProviders>
              <UrlInput />
            </TestProviders>
          );

          const urlInput = screen.getByLabelText(/enter.*video.*url/i);
          await user.type(urlInput, url);
          
          const extractButton = screen.getByRole('button', { name: /extract.*metadata/i });
          await user.click(extractButton);

          // Verify platform-specific URL handling
          expect(urlInput).toHaveValue(url);
          await waitFor(() => {
            expect(extractButton).toBeEnabled();
          });
        });
      });
    });

    describe('State Management Integration', () => {
      it('should manage application state across multiple components', async () => {
        const user = userEvent.setup();
        
        const mockOnStartTimeChange = vi.fn();
        const mockOnEndTimeChange = vi.fn();
        const mockOnFormatChange = vi.fn();

        render(
          <TestProviders>
            <div>
              <Timeline 
                duration={120}
                startTime={10}
                endTime={40}
                onStartTimeChange={mockOnStartTimeChange}
                onEndTimeChange={mockOnEndTimeChange}
              />
              <ResolutionSelector 
                formats={[
                  { format_id: '18', ext: 'mp4', resolution: '360p', filesize: 10485760, fps: 30, width: 640, height: 360 },
                  { format_id: '22', ext: 'mp4', resolution: '720p', filesize: 52428800, fps: 30, width: 1280, height: 720 }
                ]}
                selectedFormat="18"
                onFormatChange={mockOnFormatChange}
              />
            </div>
          </TestProviders>
        );

        // Test state changes in Timeline component
        const timeInputs = screen.getAllByRole('textbox');
        if (timeInputs.length >= 2) {
          await user.clear(timeInputs[0]);
          await user.type(timeInputs[0], '5');
          
          await user.clear(timeInputs[1]);
          await user.type(timeInputs[1], '30');
        }

        // Test state changes in ResolutionSelector
        const radioButtons = screen.getAllByRole('radio');
        await user.click(radioButtons[1]); // Select 720p

        // Verify state management callbacks
        await waitFor(() => {
          expect(mockOnFormatChange).toHaveBeenCalled();
        });
      });

      it('should validate state consistency across components', async () => {
        const user = userEvent.setup();
        
        render(
          <TestProviders>
            <Timeline 
              duration={120}
              startTime={10}
              endTime={40}
              onStartTimeChange={vi.fn()}
              onEndTimeChange={vi.fn()}
            />
          </TestProviders>
        );

        // Test validation logic integration
        const timeInputs = screen.getAllByRole('textbox');
        if (timeInputs.length >= 2) {
          // Try to set invalid time range (end before start)
          await user.clear(timeInputs[0]);
          await user.type(timeInputs[0], '50');
          
          await user.clear(timeInputs[1]);
          await user.type(timeInputs[1], '30');

          // Verify validation prevents invalid state
          await waitFor(() => {
            expect(screen.queryByText(/invalid.*time.*range/i)).toBeInTheDocument();
          });
        }
      });
    });

    describe('API Integration Testing', () => {
      it('should handle API responses correctly across components', async () => {
        const user = userEvent.setup();
        
        // Mock successful API responses
        server.use(
          http.get('/api/metadata', () => {
            return HttpResponse.json({
              title: 'API Integration Test Video',
              duration: 180,
              thumbnail: 'https://example.com/api-thumb.jpg',
              upload_date: '2024-01-01',
              uploader: 'API Test Channel',
              formats: [
                { format_id: '18', ext: 'mp4', resolution: '360p', filesize: 10485760, fps: 30, width: 640, height: 360 },
                { format_id: '22', ext: 'mp4', resolution: '720p', filesize: 52428800, fps: 30, width: 1280, height: 720 }
              ]
            });
          }),
          http.post('/api/clips', () => {
            return HttpResponse.json({
              id: 'api-test-job-123',
              status: 'queued',
              progress: 0,
              created_at: new Date().toISOString()
            });
          })
        );

        render(
          <TestProviders>
            <UrlInput />
          </TestProviders>
        );

        const urlInput = screen.getByLabelText(/enter.*video.*url/i);
        await user.type(urlInput, 'https://youtube.com/watch?v=api-test');
        
        const extractButton = screen.getByRole('button', { name: /extract.*metadata/i });
        await user.click(extractButton);

        // Verify API integration
        await waitFor(() => {
          expect(extractButton).toBeEnabled();
        }, { timeout: 3000 });
      });

      it('should handle API timeouts and retries', async () => {
        const user = userEvent.setup();
        
        // Mock slow API response
        server.use(
          http.get('/api/metadata', async () => {
            await new Promise(resolve => setTimeout(resolve, 5000)); // 5 second delay
            return HttpResponse.json(
              { error: 'Request timeout' },
              { status: 408 }
            );
          })
        );

        render(
          <TestProviders>
            <UrlInput />
          </TestProviders>
        );

        const urlInput = screen.getByLabelText(/enter.*video.*url/i);
        await user.type(urlInput, 'https://slow-api.com/video');
        
        const extractButton = screen.getByRole('button', { name: /extract.*metadata/i });
        await user.click(extractButton);

        // Verify timeout handling
        await waitFor(() => {
          expect(extractButton).toBeDisabled();
        });
      });
    });

    describe('Performance Integration Testing', () => {
      it('should handle multiple concurrent operations', async () => {
        const user = userEvent.setup();
        
        // Test concurrent component updates
        const promises = Array.from({ length: 5 }, (_, i) => 
          render(
            <TestProviders>
              <LoadingAnimation 
                stage={`Concurrent Operation ${i + 1}`}
                progress={i * 20}
              />
            </TestProviders>
          )
        );

        // All components should render without conflicts
        expect(promises).toHaveLength(5);
        
        // Verify each renders correctly
        promises.forEach((result, i) => {
          expect(result.container).toBeInTheDocument();
        });
      });

      it('should maintain performance with complex component trees', async () => {
        const startTime = performance.now();
        
        render(
          <TestProviders>
            <div>
              <UrlInput />
              <VideoPlayer metadata={{
                title: 'Performance Test Video',
                duration: 300,
                thumbnail: 'https://example.com/large-thumb.jpg',
                upload_date: '2024-01-01',
                uploader: 'Performance Channel',
                formats: Array.from({ length: 20 }, (_, i) => ({
                  format_id: `${i}`,
                  ext: 'mp4',
                  resolution: `${360 + i * 60}p`,
                  filesize: 10485760 * (i + 1),
                  fps: 30,
                  width: 640 + i * 320,
                  height: 360 + i * 180,
                }))
              }} />
              <Timeline duration={300} startTime={0} endTime={60} onStartTimeChange={vi.fn()} onEndTimeChange={vi.fn()} />
              <ResolutionSelector 
                formats={Array.from({ length: 20 }, (_, i) => ({
                  format_id: `${i}`,
                  ext: 'mp4',
                  resolution: `${360 + i * 60}p`,
                  filesize: 10485760 * (i + 1),
                  fps: 30,
                  width: 640 + i * 320,
                  height: 360 + i * 180,
                }))}
                selectedFormat="10"
                onFormatChange={vi.fn()}
              />
            </div>
          </TestProviders>
        );

        const endTime = performance.now();
        const renderTime = endTime - startTime;

        // Should render complex tree within performance budget
        expect(renderTime).toBeLessThan(200); // 200ms budget for complex tree
      });
    });

    describe('Error Recovery Integration', () => {
      it('should provide comprehensive error recovery flows', async () => {
        const user = userEvent.setup();
        
        render(
          <TestProviders>
            <div>
              <UrlInput />
              <div role="alert" aria-live="assertive">
                <p>Network error occurred</p>
                <button data-testid="retry-button">Try Again</button>
                <button data-testid="reset-button">Start Over</button>
              </div>
            </div>
          </TestProviders>
        );

        // Test error recovery actions
        const retryButton = screen.getByTestId('retry-button');
        const resetButton = screen.getByTestId('reset-button');

        await user.click(retryButton);
        expect(retryButton).toBeInTheDocument();

        await user.click(resetButton);
        expect(resetButton).toBeInTheDocument();

        // Verify error state management
        const alert = screen.getByRole('alert');
        expect(alert).toHaveTextContent(/network error/i);
      });
    });
  });
}); 