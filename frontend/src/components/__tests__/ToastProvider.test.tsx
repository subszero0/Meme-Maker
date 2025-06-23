import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import '@testing-library/jest-dom';
import ToastProvider, { useToast } from '../ToastProvider';

// Mock framer-motion to avoid animation issues in tests
jest.mock('framer-motion', () => ({
  motion: {
    div: ({ children, ...props }: { children: React.ReactNode; [key: string]: unknown }) => <div {...props}>{children}</div>
  },
  AnimatePresence: ({ children }: { children: React.ReactNode }) => children
}));

// Test component that uses the toast hook
function TestComponent() {
  const { pushToast } = useToast();

  return (
    <div>
      <button
        onClick={() => pushToast({ type: 'success', message: 'Success message' })}
        data-testid="success-button"
      >
        Success Toast
      </button>
      <button
        onClick={() => pushToast({ type: 'error', message: 'Error message' })}
        data-testid="error-button"
      >
        Error Toast
      </button>
      <button
        onClick={() => pushToast({ type: 'info', message: 'Info message' })}
        data-testid="info-button"
      >
        Info Toast
      </button>
      <button
        onClick={() => pushToast({ type: 'success', message: 'Duplicate message' })}
        data-testid="duplicate-button"
      >
        Duplicate Toast
      </button>
    </div>
  );
}

function renderWithProvider() {
  return render(
    <ToastProvider>
      <TestComponent />
    </ToastProvider>
  );
}

describe('ToastProvider', () => {
  beforeEach(() => {
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.runOnlyPendingTimers();
    jest.useRealTimers();
  });

  it('renders children without crashing', () => {
    renderWithProvider();
    expect(screen.getByTestId('success-button')).toBeInTheDocument();
  });

  it('throws error when useToast is used outside provider', () => {
    const consoleSpy = jest.spyOn(console, 'error').mockImplementation(() => {});
    
    expect(() => {
      render(<TestComponent />);
    }).toThrow('useToast must be used within a ToastProvider');

    consoleSpy.mockRestore();
  });

  it('pushes and displays a success toast', async () => {
    renderWithProvider();
    
    const successButton = screen.getByTestId('success-button');
    fireEvent.click(successButton);

    await waitFor(() => {
      expect(screen.getByTestId('toast')).toBeInTheDocument();
      expect(screen.getByText('Success message')).toBeInTheDocument();
      expect(screen.getByText('✓')).toBeInTheDocument();
    });
  });

  it('pushes and displays an error toast', async () => {
    renderWithProvider();
    
    const errorButton = screen.getByTestId('error-button');
    fireEvent.click(errorButton);

    await waitFor(() => {
      expect(screen.getByTestId('toast')).toBeInTheDocument();
      expect(screen.getByText('Error message')).toBeInTheDocument();
      expect(screen.getByText('✕')).toBeInTheDocument();
    });
  });

  it('pushes and displays an info toast', async () => {
    renderWithProvider();
    
    const infoButton = screen.getByTestId('info-button');
    fireEvent.click(infoButton);

    await waitFor(() => {
      expect(screen.getByTestId('toast')).toBeInTheDocument();
      expect(screen.getByText('Info message')).toBeInTheDocument();
      expect(screen.getByText('ℹ')).toBeInTheDocument();
    });
  });

  it('auto-dismisses toast after 4 seconds', async () => {
    renderWithProvider();
    
    const successButton = screen.getByTestId('success-button');
    fireEvent.click(successButton);

    await waitFor(() => {
      expect(screen.getByTestId('toast')).toBeInTheDocument();
    });

    // Fast-forward time by 4 seconds
    act(() => {
      jest.advanceTimersByTime(4000);
    });

    await waitFor(() => {
      expect(screen.queryByTestId('toast')).not.toBeInTheDocument();
    });
  });

  it('allows manual dismissal of toast', async () => {
    renderWithProvider();
    
    const successButton = screen.getByTestId('success-button');
    fireEvent.click(successButton);

    await waitFor(() => {
      expect(screen.getByTestId('toast')).toBeInTheDocument();
    });

    const dismissButton = screen.getByLabelText('Dismiss notification');
    fireEvent.click(dismissButton);

    await waitFor(() => {
      expect(screen.queryByTestId('toast')).not.toBeInTheDocument();
    });
  });

  it('debounces duplicate messages within 1 second', async () => {
    renderWithProvider();
    
    const duplicateButton = screen.getByTestId('duplicate-button');
    
    // Click twice rapidly
    fireEvent.click(duplicateButton);
    fireEvent.click(duplicateButton);

    await waitFor(() => {
      expect(screen.getAllByTestId('toast')).toHaveLength(1);
    });

    // Fast-forward by 1 second and click again
    act(() => {
      jest.advanceTimersByTime(1000);
    });

    fireEvent.click(duplicateButton);

    await waitFor(() => {
      expect(screen.getAllByTestId('toast')).toHaveLength(2);
    });
  });

  it('stacks multiple different toasts', async () => {
    renderWithProvider();
    
    const successButton = screen.getByTestId('success-button');
    const errorButton = screen.getByTestId('error-button');
    const infoButton = screen.getByTestId('info-button');

    fireEvent.click(successButton);
    fireEvent.click(errorButton);
    fireEvent.click(infoButton);

    await waitFor(() => {
      const toasts = screen.getAllByTestId('toast');
      expect(toasts).toHaveLength(3);
      expect(screen.getByText('Success message')).toBeInTheDocument();
      expect(screen.getByText('Error message')).toBeInTheDocument();
      expect(screen.getByText('Info message')).toBeInTheDocument();
    });
  });

  it('has proper accessibility attributes', async () => {
    renderWithProvider();
    
    const successButton = screen.getByTestId('success-button');
    fireEvent.click(successButton);

    await waitFor(() => {
      const toast = screen.getByTestId('toast');
      expect(toast).toHaveAttribute('role', 'status');
      expect(toast).toHaveAttribute('aria-live', 'polite');
    });
  });
}); 