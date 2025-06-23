import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import Home from '../page';
import * as api from '@/lib/api';
import useJobPoller from '@/hooks/useJobPoller';

// Mock ToastProvider
const MockToastProvider = ({ children }: { children: React.ReactNode }) => {
  return <div data-testid="toast-provider">{children}</div>;
};

// Mock all external dependencies
jest.mock('@/lib/api');
jest.mock('@/hooks/useJobPoller', () => jest.fn());
jest.mock('@/components/ToastProvider', () => ({
  useToast: () => ({
    pushToast: jest.fn(),
  }),
}));
jest.mock('@/components/TrimPanel', () => {
  return function MockTrimPanel({ onSubmit }: { onSubmit: (params: { in: number; out: number; rights: boolean }) => void }) {
    return (
      <div data-testid="trim-panel">
        <button
          onClick={() => onSubmit({ in: 10, out: 50, rights: true })}
          data-testid="trim-submit"
        >
          Submit Trim
        </button>
      </div>
    );
  };
});

jest.mock('framer-motion', () => ({
  motion: {
    div: ({ children, ...props }: { children: React.ReactNode; [key: string]: unknown }) => <div {...props}>{children}</div>,
  },
}));

// Get the mocked hook
const mockUseJobPoller = useJobPoller as jest.MockedFunction<typeof useJobPoller>;

const mockFetchVideoMetadata = api.fetchVideoMetadata as jest.MockedFunction<typeof api.fetchVideoMetadata>;
const mockCreateJob = api.createJob as jest.MockedFunction<typeof api.createJob>;

function renderWithToast(component: React.ReactElement) {
  return render(
    <MockToastProvider>
      {component}
    </MockToastProvider>
  );
}

describe('Home Page Flow', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockUseJobPoller.mockReturnValue({ status: 'queued' });
  });

  it('renders initial URL input state', () => {
    renderWithToast(<Home />);
    
    expect(screen.getByText('Meme Maker')).toBeInTheDocument();
    expect(screen.getByText(/paste a video url/i)).toBeInTheDocument();
    expect(screen.getByTestId('url-input')).toBeInTheDocument();
  });

  it('transitions from idle to loading-metadata to trim state', async () => {
    const user = userEvent.setup();
    const mockMetadata = {
      url: 'https://youtube.com/watch?v=test',
      title: 'Test Video',
      duration: 120,
    };

    mockFetchVideoMetadata.mockResolvedValue(mockMetadata);

    renderWithToast(<Home />);

    // Enter URL and submit
    const urlInput = screen.getByTestId('url-input');
    const submitBtn = screen.getByTestId('start-button');

    await user.type(urlInput, 'https://youtube.com/watch?v=test');
    await user.click(submitBtn);

    // Should show loading state
    expect(screen.getByText('Loading...')).toBeInTheDocument();

    // Wait for transition to trim state
    await waitFor(() => {
      expect(screen.getByTestId('trim-panel')).toBeInTheDocument();
    });

    expect(mockFetchVideoMetadata).toHaveBeenCalledWith('https://youtube.com/watch?v=test');
  });

  it('handles metadata fetch error and returns to idle', async () => {
    const user = userEvent.setup();
    mockFetchVideoMetadata.mockRejectedValue(new Error('Failed to fetch'));

    renderWithToast(<Home />);

    const urlInput = screen.getByTestId('url-input');
    const submitBtn = screen.getByTestId('start-button');

    await user.type(urlInput, 'https://youtube.com/watch?v=invalid');
    await user.click(submitBtn);

    await waitFor(() => {
      expect(screen.getByTestId('url-input')).toBeInTheDocument();
    });

    // Should be back to idle state (URL input visible)
    expect(screen.queryByTestId('trim-panel')).not.toBeInTheDocument();
  });

  it('transitions from trim to processing state', async () => {
    const user = userEvent.setup();
    const mockMetadata = {
      url: 'https://youtube.com/watch?v=test',
      title: 'Test Video',
      duration: 120,
    };

    mockFetchVideoMetadata.mockResolvedValue(mockMetadata);
    mockCreateJob.mockResolvedValue({ jobId: 'test-job-123' });

    renderWithToast(<Home />);

    // Get to trim state
    const urlInput = screen.getByTestId('url-input');
    await user.type(urlInput, 'https://youtube.com/watch?v=test');
    await user.click(screen.getByTestId('start-button'));

    await waitFor(() => {
      expect(screen.getByTestId('trim-panel')).toBeInTheDocument();
    });

    // Submit trim
    const trimSubmit = screen.getByTestId('trim-submit');
    await user.click(trimSubmit);

    // Should show processing state
    await waitFor(() => {
      expect(screen.getByText('Processing your clip...')).toBeInTheDocument();
      expect(screen.getByText('Test Video')).toBeInTheDocument();
    });

    expect(mockCreateJob).toHaveBeenCalledWith({
      url: 'https://youtube.com/watch?v=test',
      in: 10,
      out: 50,
      rights: true,
    });
  });

  it('shows progress bar during processing', async () => {
    const user = userEvent.setup();
    const mockMetadata = {
      url: 'https://youtube.com/watch?v=test',
      title: 'Test Video',
      duration: 120,
    };

    mockFetchVideoMetadata.mockResolvedValue(mockMetadata);
    mockCreateJob.mockResolvedValue({ jobId: 'test-job-123' });
    mockUseJobPoller.mockReturnValue({ status: 'working', progress: 50 });

    renderWithToast(<Home />);

    // Navigate to processing state
    const urlInput = screen.getByTestId('url-input');
    await user.type(urlInput, 'https://youtube.com/watch?v=test');
    await user.click(screen.getByTestId('start-button'));

    await waitFor(() => {
      expect(screen.getByTestId('trim-panel')).toBeInTheDocument();
    });

    await user.click(screen.getByTestId('trim-submit'));

    await waitFor(() => {
      expect(screen.getByText('Trimming video...')).toBeInTheDocument();
    });

    // Progress bar should be present (we can't easily test the exact progress value)
    const progressContainer = screen.getByText('Processing your clip...').closest('div');
    expect(progressContainer).toBeInTheDocument();
  });

  it('opens download modal when job completes', async () => {
    const user = userEvent.setup();
    const mockMetadata = {
      url: 'https://youtube.com/watch?v=test',
      title: 'Test Video',
      duration: 120,
    };

    mockFetchVideoMetadata.mockResolvedValue(mockMetadata);
    mockCreateJob.mockResolvedValue({ jobId: 'test-job-123' });

    // Start with queued, then simulate completion
    mockUseJobPoller
      .mockReturnValueOnce({ status: 'queued' })
      .mockReturnValue({ status: 'done', url: 'https://s3.aws.com/download-url' });

    renderWithToast(<Home />);

    // Navigate through states to processing
    const urlInput = screen.getByTestId('url-input');
    await user.type(urlInput, 'https://youtube.com/watch?v=test');
    await user.click(screen.getByTestId('start-button'));

    await waitFor(() => {
      expect(screen.getByTestId('trim-panel')).toBeInTheDocument();
    });

    await user.click(screen.getByTestId('trim-submit'));

    // The poller should trigger the download modal
    await waitFor(() => {
      expect(screen.getByText('Clip ready!')).toBeInTheDocument();
      expect(screen.getByTestId('download-btn')).toHaveAttribute('href', 'https://s3.aws.com/download-url');
    });
  });

  it('shows queue full error when job fails with QUEUE_FULL', async () => {
    const user = userEvent.setup();
    const mockMetadata = {
      url: 'https://youtube.com/watch?v=test',
      title: 'Test Video',
      duration: 120,
    };

    mockFetchVideoMetadata.mockResolvedValue(mockMetadata);
    mockCreateJob.mockResolvedValue({ jobId: 'test-job-123' });
    mockUseJobPoller.mockReturnValue({ status: 'error', errorCode: 'QUEUE_FULL' });

    renderWithToast(<Home />);

    // Navigate to processing state
    const urlInput = screen.getByTestId('url-input');
    await user.type(urlInput, 'https://youtube.com/watch?v=test');
    await user.click(screen.getByTestId('start-button'));

    await waitFor(() => {
      expect(screen.getByTestId('trim-panel')).toBeInTheDocument();
    });

    await user.click(screen.getByTestId('trim-submit'));

    // Should show queue full error
    await waitFor(() => {
      expect(screen.getByText('Busy right now. Try again in a minute.')).toBeInTheDocument();
    });
  });

  it('resets to idle state when download modal closes', async () => {
    const user = userEvent.setup();
    const mockMetadata = {
      url: 'https://youtube.com/watch?v=test',
      title: 'Test Video',
      duration: 120,
    };

    mockFetchVideoMetadata.mockResolvedValue(mockMetadata);
    mockCreateJob.mockResolvedValue({ jobId: 'test-job-123' });
    mockUseJobPoller.mockReturnValue({ status: 'done', url: 'https://s3.aws.com/download-url' });

    renderWithToast(<Home />);

    // Navigate to download modal
    const urlInput = screen.getByTestId('url-input');
    await user.type(urlInput, 'https://youtube.com/watch?v=test');
    await user.click(screen.getByTestId('start-button'));

    await waitFor(() => {
      expect(screen.getByTestId('trim-panel')).toBeInTheDocument();
    });

    await user.click(screen.getByTestId('trim-submit'));

    await waitFor(() => {
      expect(screen.getByText('Clip ready!')).toBeInTheDocument();
    });

    // Close the modal
    const cancelBtn = screen.getByText('Cancel');
    await user.click(cancelBtn);

    // Should be back to idle state
    await waitFor(() => {
      expect(screen.getByTestId('url-input')).toBeInTheDocument();
      expect(screen.queryByText('Clip ready!')).not.toBeInTheDocument();
    });
  });

  it('allows canceling from processing state', async () => {
    const user = userEvent.setup();
    const mockMetadata = {
      url: 'https://youtube.com/watch?v=test',
      title: 'Test Video',
      duration: 120,
    };

    mockFetchVideoMetadata.mockResolvedValue(mockMetadata);
    mockCreateJob.mockResolvedValue({ jobId: 'test-job-123' });
    mockUseJobPoller.mockReturnValue({ status: 'working' });

    renderWithToast(<Home />);

    // Get to processing state
    const urlInput = screen.getByTestId('url-input');
    await user.type(urlInput, 'https://youtube.com/watch?v=test');
    await user.click(screen.getByTestId('start-button'));

    await waitFor(() => {
      expect(screen.getByTestId('trim-panel')).toBeInTheDocument();
    });

    await user.click(screen.getByTestId('trim-submit'));

    await waitFor(() => {
      expect(screen.getByText('Processing your clip...')).toBeInTheDocument();
    });

    // Click cancel
    const cancelBtn = screen.getByText('Cancel');
    await user.click(cancelBtn);

    // Should return to idle
    await waitFor(() => {
      expect(screen.getByTestId('url-input')).toBeInTheDocument();
      expect(screen.queryByText('Processing your clip...')).not.toBeInTheDocument();
    });
  });
}); 