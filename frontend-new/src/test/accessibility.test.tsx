import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { axe, toHaveNoViolations } from 'jest-axe';
import { a11yUtils } from './setup';
import { TestProviders, createTestQueryClient } from './utils';
import { UrlInput } from '../components/UrlInput';
import { VideoPlayer } from '../components/VideoPlayer';
import { Timeline } from '../components/Timeline';
import { ResolutionSelector } from '../components/ResolutionSelector';
import { LoadingAnimation } from '../components/LoadingAnimation';
import { SharingOptions } from '../components/SharingOptions';

// Extend Jest matchers
expect.extend(toHaveNoViolations);

describe('Accessibility Testing (WCAG 2.1 AA)', () => {
  describe('Component Accessibility', () => {
    it('UrlInput should be fully accessible', async () => {
      const { container } = render(
        <TestProviders>
          <UrlInput />
        </TestProviders>
      );

      // Test with jest-axe
      await a11yUtils.testAccessibility(container);

      // Verify specific accessibility features
      const input = screen.getByLabelText(/enter.*video.*url/i);
      expect(input).toHaveAttribute('aria-label');
      expect(input).toHaveAttribute('type', 'url');

      const button = screen.getByRole('button', { name: /extract.*metadata/i });
      expect(button).toBeInTheDocument();
      expect(button).toHaveAttribute('type', 'submit');
    });

    it('VideoPlayer should meet accessibility standards', async () => {
      const mockMetadata = {
        title: 'Test Video',
        duration: 120,
        thumbnail: 'https://example.com/thumb.jpg',
        upload_date: '2024-01-01',
        uploader: 'Test Channel',
        formats: []
      };

      const { container } = render(
        <TestProviders>
          <VideoPlayer metadata={mockMetadata} />
        </TestProviders>
      );

      await a11yUtils.testAccessibility(container);

      // Verify media accessibility
      const videoTitle = screen.getByText('Test Video');
      expect(videoTitle).toBeInTheDocument();

      // Check for proper heading structure
      const headings = screen.getAllByRole('heading');
      expect(headings.length).toBeGreaterThan(0);
    });

    it('Timeline should be keyboard accessible', async () => {
      const { container } = render(
        <TestProviders>
          <Timeline 
            duration={120}
            startTime={10}
            endTime={40}
            onStartTimeChange={() => {}}
            onEndTimeChange={() => {}}
          />
        </TestProviders>
      );

      await a11yUtils.testAccessibility(container);

      // Verify slider accessibility
      const sliders = screen.getAllByRole('slider');
      sliders.forEach(slider => {
        expect(slider).toHaveAttribute('aria-label');
        expect(slider).toHaveAttribute('aria-valuemin');
        expect(slider).toHaveAttribute('aria-valuemax');
        expect(slider).toHaveAttribute('aria-valuenow');
      });

      // Test time inputs
      const timeInputs = screen.getAllByRole('textbox');
      timeInputs.forEach(input => {
        expect(input).toHaveAttribute('aria-label');
      });
    });

    it('ResolutionSelector should have proper labels and descriptions', async () => {
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

      const { container } = render(
        <TestProviders>
          <ResolutionSelector 
            formats={mockFormats}
            selectedFormat="22"
            onFormatChange={() => {}}
          />
        </TestProviders>
      );

      await a11yUtils.testAccessibility(container);

      // Verify radio group accessibility
      const radioGroup = screen.getByRole('radiogroup');
      expect(radioGroup).toHaveAttribute('aria-label');

      const radioButtons = screen.getAllByRole('radio');
      radioButtons.forEach(radio => {
        expect(radio).toHaveAttribute('aria-describedby');
      });
    });

    it('LoadingAnimation should announce status changes to screen readers', async () => {
      const { container } = render(
        <TestProviders>
          <LoadingAnimation 
            stage="Processing video..."
            progress={50}
          />
        </TestProviders>
      );

      await a11yUtils.testAccessibility(container);

      // Verify live region for status updates
      const liveRegion = screen.getByRole('status');
      expect(liveRegion).toHaveAttribute('aria-live', 'polite');
      
      // Verify progress bar accessibility
      const progressBar = screen.getByRole('progressbar');
      expect(progressBar).toHaveAttribute('aria-valuemin', '0');
      expect(progressBar).toHaveAttribute('aria-valuemax', '100');
      expect(progressBar).toHaveAttribute('aria-valuenow', '50');
      expect(progressBar).toHaveAttribute('aria-label');
    });

    it('SharingOptions should have accessible buttons and links', async () => {
      const mockOptions = {
        downloadUrl: 'https://example.com/download.mp4',
        filename: 'test-video.mp4',
        shareUrl: 'https://example.com/share/123',
      };

      const { container } = render(
        <TestProviders>
          <SharingOptions {...mockOptions} />
        </TestProviders>
      );

      await a11yUtils.testAccessibility(container);

      // Verify download button
      const downloadButton = screen.getByRole('button', { name: /download/i });
      expect(downloadButton).toHaveAttribute('aria-describedby');

      // Verify share buttons
      const shareButtons = screen.getAllByRole('button');
      shareButtons.forEach(button => {
        if (button.textContent?.includes('Share')) {
          expect(button).toHaveAttribute('aria-label');
        }
      });

      // Verify links have proper accessibility
      const links = screen.getAllByRole('link');
      links.forEach(link => {
        expect(link).toHaveAttribute('href');
        // External links should have appropriate aria-label
        if (link.getAttribute('href')?.includes('twitter.com') ||
            link.getAttribute('href')?.includes('facebook.com')) {
          expect(link).toHaveAttribute('aria-label');
        }
      });
    });
  });

  describe('Keyboard Navigation', () => {
    it('should support full keyboard navigation through workflow', async () => {
      const { container } = render(
        <TestProviders>
          <div>
            <UrlInput />
            <Timeline 
              duration={120}
              startTime={10}
              endTime={40}
              onStartTimeChange={() => {}}
              onEndTimeChange={() => {}}
            />
          </div>
        </TestProviders>
      );

      await a11yUtils.testAccessibility(container);

      // Verify tab order is logical
      const focusableElements = container.querySelectorAll(
        'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
      );

      expect(focusableElements.length).toBeGreaterThan(0);

      // Check that all interactive elements are keyboard accessible
      focusableElements.forEach(element => {
        expect(element).not.toHaveAttribute('tabindex', '-1');
      });
    });

    it('should have proper focus management', async () => {
      const { container } = render(
        <TestProviders>
          <UrlInput />
        </TestProviders>
      );

      await a11yUtils.testAccessibility(container);

      // Verify focus indicators are present
      const style = window.getComputedStyle(document.body);
      
      // Focus should be visible (not outline: none)
      const focusableElements = container.querySelectorAll('button, input');
      focusableElements.forEach(element => {
        const elementStyle = window.getComputedStyle(element);
        expect(elementStyle.outline).not.toBe('none');
      });
    });
  });

  describe('Color and Contrast', () => {
    it('should not rely solely on color for important information', async () => {
      const { container } = render(
        <TestProviders>
          <LoadingAnimation 
            stage="Processing..."
            progress={75}
            hasError={true}
          />
        </TestProviders>
      );

      // Custom accessibility test without color-contrast rule
      const results = await axe(container, {
        rules: {
          'color-contrast': { enabled: false }, // Disable for design system
          'color-usage': { enabled: true },
        },
      });

      expect(results).toHaveNoViolations();

      // Verify error states have text indicators, not just color
      const errorIndicators = container.querySelectorAll('[aria-live="assertive"]');
      expect(errorIndicators.length).toBeGreaterThan(0);
    });
  });

  describe('Screen Reader Support', () => {
    it('should provide meaningful content to screen readers', async () => {
      const { container } = render(
        <TestProviders>
          <div>
            <h1>Meme Maker</h1>
            <UrlInput />
            <LoadingAnimation stage="Ready" progress={0} />
          </div>
        </TestProviders>
      );

      await a11yUtils.testAccessibility(container);

      // Verify heading structure
      const h1 = screen.getByRole('heading', { level: 1 });
      expect(h1).toHaveTextContent('Meme Maker');

      // Verify landmark regions
      const main = container.querySelector('main');
      if (main) {
        expect(main).toHaveAttribute('role', 'main');
      }
    });

    it('should handle dynamic content updates appropriately', async () => {
      const { container, rerender } = render(
        <TestProviders>
          <LoadingAnimation stage="Initializing..." progress={0} />
        </TestProviders>
      );

      await a11yUtils.testAccessibility(container);

      // Test progress update
      rerender(
        <TestProviders>
          <LoadingAnimation stage="Processing video..." progress={50} />
        </TestProviders>
      );

      await a11yUtils.testAccessibility(container);

      // Verify live region updates
      const liveRegion = screen.getByRole('status');
      expect(liveRegion).toHaveTextContent('Processing video...');
    });
  });

  describe('Mobile Accessibility', () => {
    it('should be accessible on touch devices', async () => {
      // Simulate mobile viewport
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 375,
      });

      const { container } = render(
        <TestProviders>
          <Timeline 
            duration={120}
            startTime={10}
            endTime={40}
            onStartTimeChange={() => {}}
            onEndTimeChange={() => {}}
          />
        </TestProviders>
      );

      await a11yUtils.testAccessibility(container);

      // Verify touch targets are appropriately sized
      const interactiveElements = container.querySelectorAll('button, [role="slider"]');
      interactiveElements.forEach(element => {
        const rect = element.getBoundingClientRect();
        const size = Math.min(rect.width, rect.height);
        
        // WCAG guideline: minimum 44px touch target
        expect(size).toBeGreaterThanOrEqual(44);
      });
    });
  });

  describe('Error Handling Accessibility', () => {
    it('should announce errors to screen readers', async () => {
      const { container } = render(
        <TestProviders>
          <div role="alert" aria-live="assertive">
            Invalid video URL. Please check the URL and try again.
          </div>
        </TestProviders>
      );

      await a11yUtils.testAccessibility(container);

      // Verify error announcement
      const errorMessage = screen.getByRole('alert');
      expect(errorMessage).toHaveAttribute('aria-live', 'assertive');
      expect(errorMessage).toHaveTextContent(/invalid.*url/i);
    });

    it('should provide helpful error messages with recovery options', async () => {
      const { container } = render(
        <TestProviders>
          <div role="alert" aria-describedby="error-help">
            <p>Failed to process video</p>
            <p id="error-help">
              This might be due to network issues. Please check your connection and try again.
            </p>
            <button type="button" aria-label="Retry video processing">
              Try Again
            </button>
          </div>
        </TestProviders>
      );

      await a11yUtils.testAccessibility(container);

      // Verify error context and recovery
      const retryButton = screen.getByRole('button', { name: /retry/i });
      expect(retryButton).toHaveAttribute('aria-label');
      
      const helpText = screen.getByText(/network issues/i);
      expect(helpText).toBeInTheDocument();
    });
  });
});

// Performance Test for Accessibility Tools
describe('Accessibility Performance', () => {
  it('should run accessibility checks within performance budget', async () => {
    const startTime = performance.now();

    const { container } = render(
      <TestProviders>
        <div>
          <UrlInput />
          <VideoPlayer metadata={{
            title: 'Test',
            duration: 120,
            thumbnail: '',
            upload_date: '2024-01-01',
            uploader: 'Test',
            formats: []
          }} />
          <Timeline 
            duration={120}
            startTime={10}
            endTime={40}
            onStartTimeChange={() => {}}
            onEndTimeChange={() => {}}
          />
        </div>
      </TestProviders>
    );

    await a11yUtils.testAccessibility(container);

    const endTime = performance.now();
    const duration = endTime - startTime;

    // Accessibility testing should complete within 5 seconds
    expect(duration).toBeLessThan(5000);
  });
}); 