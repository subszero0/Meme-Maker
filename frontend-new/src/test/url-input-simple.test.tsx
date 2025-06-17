import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { UrlInput } from '../components/UrlInput';

// Mock the hook that was causing issues
vi.mock('../hooks/useApi', () => ({
  useVideoMetadata: vi.fn(() => ({
    data: null,
    isLoading: false,
    error: null,
    isError: false
  }))
}));

const TestWrapper = ({ children }: { children: React.ReactNode }) => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });
  return (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  );
};

describe('UrlInput Simple Test', () => {
  it('should render input field', () => {
    const mockOnSubmit = vi.fn();
    
    render(
      <TestWrapper>
        <UrlInput onSubmit={mockOnSubmit} />
      </TestWrapper>
    );
    
    expect(screen.getByPlaceholderText(/video URL/i)).toBeInTheDocument();
  });
}); 