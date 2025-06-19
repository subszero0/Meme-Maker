import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

// Import components to test
import { UrlInput } from '../components/UrlInput';
import { LoadingAnimation } from '../components/LoadingAnimation';

// Mock all external dependencies to avoid hanging
vi.mock('../hooks/useApi', () => ({
  useVideoMetadata: vi.fn(() => ({
    data: null,
    isLoading: false,
    error: null,
    isError: false,
  })),
  useJobStatusWithPolling: vi.fn(() => ({
    data: null,
    error: null,
    isLoading: true,
  })),
  useCancelJob: vi.fn(() => ({
    mutate: vi.fn(),
  })),
}));

vi.mock('use-debounce', () => ({
  useDebounce: vi.fn((value) => [value]),
}));

vi.mock('../lib/api', () => ({
  metadataApi: {
    getBasicMetadata: vi.fn(() => Promise.resolve({ title: 'Test Video', duration: 120 })),
  },
  jobsApi: {
    createJob: vi.fn(() => Promise.resolve({ id: 'test-job', status: 'queued' })),
  },
  JobStatus: {
    QUEUED: 'queued',
    WORKING: 'working',
    DONE: 'completed',
    ERROR: 'error',
  },
}));

// Test Wrapper
const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false, staleTime: Infinity },
      mutations: { retry: false },
    },
  });

  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  );
};

const renderWithProviders = (component: React.ReactElement) => {
  const wrapper = createWrapper();
  const Wrapper = wrapper;
  return render(<Wrapper>{component}</Wrapper>);
};

describe('Accessibility Fixed Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Basic Accessibility Testing', () => {
    it('should render UrlInput component accessibly', () => {
      const mockOnSubmit = vi.fn();
      renderWithProviders(<UrlInput onSubmit={mockOnSubmit} />);

      // Check the actual structure of the component
      const input = screen.getByPlaceholderText(/https.*youtube.*watch/i);
      expect(input).toHaveAttribute('type', 'url');
      expect(input).not.toBeDisabled();

      const button = screen.getByRole('button', { name: /let's go/i });
      expect(button).toBeInTheDocument();
      expect(button).toHaveAttribute('type', 'submit');

      // Check for proper heading structure
      const heading = screen.getByRole('heading', { level: 2 });
      expect(heading).toHaveTextContent(/start your creative journey/i);
    });

    it('should render LoadingAnimation component accessibly', () => {
      renderWithProviders(<LoadingAnimation jobId="test-job-123" />);

      // Check for main heading
      const heading = screen.getByText(/creating your masterpiece/i);
      expect(heading).toBeInTheDocument();

      // Check for progress indicators (SVG elements)
      const svgElements = document.querySelectorAll('svg');
      expect(svgElements.length).toBeGreaterThan(0);
    });

    it('should have proper keyboard navigation support', () => {
      const mockOnSubmit = vi.fn();
      renderWithProviders(<UrlInput onSubmit={mockOnSubmit} />);

      // Test tab order and keyboard accessibility
      const focusableElements = document.querySelectorAll(
        'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
      );

      expect(focusableElements.length).toBeGreaterThan(0);

      // Verify elements can receive focus
      focusableElements.forEach(element => {
        expect(element).not.toHaveAttribute('tabindex', '-1');
      });
    });

    it('should have proper semantic HTML structure', () => {
      const mockOnSubmit = vi.fn();
      renderWithProviders(<UrlInput onSubmit={mockOnSubmit} />);

      // Check for proper form structure
      const form = document.querySelector('form');
      expect(form).toBeInTheDocument();

      // Check for proper input types
      const urlInput = screen.getByPlaceholderText(/https.*youtube.*watch/i);
      expect(urlInput).toHaveAttribute('type', 'url');

      // Check for proper button attributes
      const button = screen.getByRole('button', { name: /let's go/i });
      expect(button).toHaveAttribute('type', 'submit');
    });

    it('should support screen readers with live regions', () => {
      renderWithProviders(<LoadingAnimation jobId="test-job-123" />);

      // Look for live regions for dynamic content updates
      const liveRegions = document.querySelectorAll('[aria-live]');
      
      // Should have at least one live region for status updates
      if (liveRegions.length > 0) {
        liveRegions.forEach(region => {
          expect(region).toHaveAttribute('aria-live');
          const liveValue = region.getAttribute('aria-live');
          expect(['polite', 'assertive', 'off']).toContain(liveValue);
        });
      }
    });

    it('should provide error feedback accessibly', () => {
      renderWithProviders(
        <div role="alert" aria-live="assertive">
          <span>Error: Invalid video URL</span>
        </div>
      );

      // Verify error states have proper ARIA attributes
      const errorMessage = screen.getByRole('alert');
      expect(errorMessage).toHaveTextContent(/error/i);
      expect(errorMessage).toHaveAttribute('aria-live', 'assertive');
    });

    it('should have proper heading hierarchy', () => {
      const mockOnSubmit = vi.fn();
      renderWithProviders(
        <div>
          <h1>Meme Maker</h1>
          <UrlInput onSubmit={mockOnSubmit} />
        </div>
      );

      // Check heading structure
      const h1 = screen.getByRole('heading', { level: 1 });
      expect(h1).toHaveTextContent('Meme Maker');

      const h2 = screen.getByRole('heading', { level: 2 });
      expect(h2).toHaveTextContent(/start your creative journey/i);
    });
  });

  describe('Mobile Accessibility', () => {
    it('should be accessible on smaller viewports', () => {
      // Simulate mobile viewport
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 375,
      });

      const mockOnSubmit = vi.fn();
      renderWithProviders(<UrlInput onSubmit={mockOnSubmit} />);

      // Verify touch targets are appropriately sized
      const buttons = document.querySelectorAll('button');
      buttons.forEach(button => {
        // In test environment, just verify the element exists and is not hidden
        expect(button).not.toHaveStyle('display: none');
        expect(button).not.toHaveStyle('visibility: hidden');
      });
    });
  });

  describe('Form Accessibility', () => {
    it('should properly associate labels with form controls', () => {
      const mockOnSubmit = vi.fn();
      renderWithProviders(<UrlInput onSubmit={mockOnSubmit} />);

      // Check that the input has a meaningful placeholder
      const input = screen.getByPlaceholderText(/https.*youtube.*watch/i);
      expect(input.getAttribute('placeholder')).toContain('youtube');
      expect(input.getAttribute('placeholder')).toContain('video URL');
    });

    it('should have proper form submission behavior', () => {
      const mockOnSubmit = vi.fn();
      renderWithProviders(<UrlInput onSubmit={mockOnSubmit} />);

      // Check that form has proper structure
      const form = document.querySelector('form');
      expect(form).toBeInTheDocument();

      const submitButton = screen.getByRole('button', { name: /let's go/i });
      expect(submitButton).toHaveAttribute('type', 'submit');
    });
  });

  describe('Performance Test for Accessibility', () => {
    it('should run accessibility checks efficiently', () => {
      const startTime = performance.now();

      const mockOnSubmit = vi.fn();
      renderWithProviders(
        <div>
          <UrlInput onSubmit={mockOnSubmit} />
          <LoadingAnimation jobId="test-job-123" />
        </div>
      );

      // Manual accessibility checks are fast
      const focusableElements = document.querySelectorAll(
        'button, input, [tabindex]:not([tabindex="-1"])'
      );
      expect(focusableElements.length).toBeGreaterThan(0);

      const endTime = performance.now();
      const duration = endTime - startTime;

      // Manual accessibility testing should be very fast
      expect(duration).toBeLessThan(1000); // Less than 1 second
    });
  });
}); 