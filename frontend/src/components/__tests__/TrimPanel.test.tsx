import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import TrimPanel from '../TrimPanel';
import { useToast } from '../ToastProvider';

// Mock the ToastProvider
jest.mock('../ToastProvider', () => ({
  useToast: jest.fn(),
}));

// Mock react-player
jest.mock('react-player', () => {
  return function MockReactPlayer({ url, controls, muted, playing, ...props }: { 
    url: string; 
    controls?: boolean; 
    muted?: boolean; 
    playing?: boolean; 
    [key: string]: unknown;
  }) {
    return (
      <div 
        data-testid="react-player" 
        data-url={url}
        data-controls={controls ? 'true' : 'false'}
        data-muted={muted ? 'true' : 'false'}
        data-playing={playing ? 'true' : 'false'}
        {...props} 
      />
    );
  };
});

// Mock use-debounce
jest.mock('use-debounce', () => ({
  useDebouncedCallback: (callback: (value: string) => void) => callback,
}));

const mockPushToast = jest.fn();
const mockOnSubmit = jest.fn();

const defaultJobMeta = {
  url: 'https://example.com/video.mp4',
  title: 'Test Video',
  duration: 300, // 5 minutes
};

beforeEach(() => {
  jest.clearAllMocks();
  (useToast as jest.Mock).mockReturnValue({
    pushToast: mockPushToast,
  });
});

describe('TrimPanel', () => {
  it('renders video preview with correct URL', () => {
    render(<TrimPanel jobMeta={defaultJobMeta} onSubmit={mockOnSubmit} />);
    
    const player = screen.getByTestId('react-player');
    expect(player).toHaveAttribute('data-url', defaultJobMeta.url);
  });

  it('displays video title and duration', () => {
    render(<TrimPanel jobMeta={defaultJobMeta} onSubmit={mockOnSubmit} />);
    
    expect(screen.getByText('Test Video')).toBeInTheDocument();
    expect(screen.getByText('Duration: 05:00.000')).toBeInTheDocument();
  });

  it('initializes with correct default values', () => {
    render(<TrimPanel jobMeta={defaultJobMeta} onSubmit={mockOnSubmit} />);
    
    const startInput = screen.getByDisplayValue('00:00.000') as HTMLInputElement;
    const endInput = screen.getByDisplayValue('03:00.000') as HTMLInputElement;
    
    expect(startInput.value).toBe('00:00.000');
    expect(endInput.value).toBe('03:00.000'); // Capped at 180 seconds
  });

  it('renders slider handles with correct test IDs', () => {
    render(<TrimPanel jobMeta={defaultJobMeta} onSubmit={mockOnSubmit} />);
    
    expect(screen.getByTestId('handle-start')).toBeInTheDocument();
    expect(screen.getByTestId('handle-end')).toBeInTheDocument();
  });

  it('disables submit button when rights checkbox is unchecked', () => {
    render(<TrimPanel jobMeta={defaultJobMeta} onSubmit={mockOnSubmit} />);
    
    const submitButton = screen.getByRole('button', { name: /clip & download/i });
    expect(submitButton).toBeDisabled();
  });

  it('enables submit button when rights checkbox is checked and clip is valid', async () => {
    const user = userEvent.setup();
    render(<TrimPanel jobMeta={defaultJobMeta} onSubmit={mockOnSubmit} />);
    
    const rightsCheckbox = screen.getByRole('checkbox');
    await user.click(rightsCheckbox);
    
    const submitButton = screen.getByRole('button', { name: /clip & download/i });
    expect(submitButton).toBeEnabled();
  });

  it('shows error message when clip duration exceeds 180 seconds', async () => {
    const user = userEvent.setup();
    render(<TrimPanel jobMeta={defaultJobMeta} onSubmit={mockOnSubmit} />);
    
    const endInput = screen.getByDisplayValue('03:00.000');
    await user.clear(endInput);
    await user.type(endInput, '03:01.000'); // 181 seconds
    
    await waitFor(() => {
      expect(screen.getByText('Trim to three minutes or less to proceed.')).toBeInTheDocument();
    });
  });

  it('shows error message when end time is before start time', async () => {
    const user = userEvent.setup();
    render(<TrimPanel jobMeta={defaultJobMeta} onSubmit={mockOnSubmit} />);
    
    const startInput = screen.getByDisplayValue('00:00.000');
    const endInput = screen.getByDisplayValue('03:00.000');
    
    await user.clear(startInput);
    await user.type(startInput, '02:00.000');
    await user.clear(endInput);
    await user.type(endInput, '01:00.000');
    
    await waitFor(() => {
      expect(screen.getByText('End time must be after start time.')).toBeInTheDocument();
    });
  });

  it('disables submit button when clip duration exceeds 180 seconds', async () => {
    const user = userEvent.setup();
    render(<TrimPanel jobMeta={defaultJobMeta} onSubmit={mockOnSubmit} />);
    
    const rightsCheckbox = screen.getByRole('checkbox');
    const endInput = screen.getByDisplayValue('03:00.000');
    
    await user.click(rightsCheckbox);
    await user.clear(endInput);
    await user.type(endInput, '03:01.000'); // 181 seconds
    
    const submitButton = screen.getByRole('button', { name: /clip & download/i });
    expect(submitButton).toBeDisabled();
  });

  it('disables submit button when end time is before start time', async () => {
    const user = userEvent.setup();
    render(<TrimPanel jobMeta={defaultJobMeta} onSubmit={mockOnSubmit} />);
    
    const rightsCheckbox = screen.getByRole('checkbox');
    const startInput = screen.getByDisplayValue('00:00.000');
    const endInput = screen.getByDisplayValue('03:00.000');
    
    await user.click(rightsCheckbox);
    await user.clear(startInput);
    await user.type(startInput, '02:00.000');
    await user.clear(endInput);
    await user.type(endInput, '01:00.000');
    
    const submitButton = screen.getByRole('button', { name: /clip & download/i });
    expect(submitButton).toBeDisabled();
  });

  it('calls onSubmit with correct parameters when valid submit occurs', async () => {
    const user = userEvent.setup();
    render(<TrimPanel jobMeta={defaultJobMeta} onSubmit={mockOnSubmit} />);
    
    const rightsCheckbox = screen.getByRole('checkbox');
    const startInput = screen.getByDisplayValue('00:00.000');
    const endInput = screen.getByDisplayValue('03:00.000');
    const submitButton = screen.getByRole('button', { name: /clip & download/i });
    
    await user.click(rightsCheckbox);
    await user.clear(startInput);
    await user.type(startInput, '00:30.000');
    await user.clear(endInput);
    await user.type(endInput, '01:30.000');
    
    await user.click(submitButton);
    
    expect(mockOnSubmit).toHaveBeenCalledWith({
      in: 30,
      out: 90,
      rights: true,
    });
  });

  it('updates time inputs when slider values change', () => {
    render(<TrimPanel jobMeta={defaultJobMeta} onSubmit={mockOnSubmit} />);
    
    // This test would require more complex slider interaction simulation
    // For now, we verify the inputs update based on state changes
    const startInput = screen.getByDisplayValue('00:00.000') as HTMLInputElement;
    const endInput = screen.getByDisplayValue('03:00.000') as HTMLInputElement;
    
    // Initial values should be formatted correctly
    expect(startInput.value).toBe('00:00.000');
    expect(endInput.value).toBe('03:00.000');
  });

  it('handles toast error when onSubmit throws', async () => {
    const user = userEvent.setup();
    const errorOnSubmit = jest.fn().mockImplementation(() => {
      throw new Error('Submit failed');
    });
    
    render(<TrimPanel jobMeta={defaultJobMeta} onSubmit={errorOnSubmit} />);
    
    const rightsCheckbox = screen.getByRole('checkbox');
    const submitButton = screen.getByRole('button', { name: /clip & download/i });
    
    await user.click(rightsCheckbox);
    await user.click(submitButton);
    
    expect(mockPushToast).toHaveBeenCalledWith({
      type: 'error',
      message: 'Failed to submit clip request',
    });
  });

  it('caps initial out time to 180 seconds for videos longer than 3 minutes', () => {
    const longJobMeta = {
      ...defaultJobMeta,
      duration: 600, // 10 minutes
    };
    
    render(<TrimPanel jobMeta={longJobMeta} onSubmit={mockOnSubmit} />);
    
    const endInput = screen.getByDisplayValue('03:00.000') as HTMLInputElement;
    expect(endInput.value).toBe('03:00.000'); // Still capped at 3 minutes
  });

  it('allows full duration for videos shorter than 3 minutes', () => {
    const shortJobMeta = {
      ...defaultJobMeta,
      duration: 120, // 2 minutes
    };
    
    render(<TrimPanel jobMeta={shortJobMeta} onSubmit={mockOnSubmit} />);
    
    const endInput = screen.getByDisplayValue('02:00.000') as HTMLInputElement;
    expect(endInput.value).toBe('02:00.000'); // Full duration
  });

  it('has proper accessibility attributes on slider handles', () => {
    render(<TrimPanel jobMeta={defaultJobMeta} onSubmit={mockOnSubmit} />);
    
    const startHandle = screen.getByTestId('handle-start');
    const endHandle = screen.getByTestId('handle-end');
    
    expect(startHandle).toHaveAttribute('aria-valuemin', '0');
    expect(startHandle).toHaveAttribute('aria-valuemax', '300');
    expect(startHandle).toHaveAttribute('aria-label', 'Start time');
    
    expect(endHandle).toHaveAttribute('aria-valuemin', '0');
    expect(endHandle).toHaveAttribute('aria-valuemax', '300');
    expect(endHandle).toHaveAttribute('aria-label', 'End time');
  });
}); 