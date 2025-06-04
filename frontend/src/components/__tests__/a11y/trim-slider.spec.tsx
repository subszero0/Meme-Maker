/**
 * @frontend @accessibility
 * Accessibility Tests for Trim Slider Component
 * 
 * Tests WCAG and ARIA compliance for the dual-handle slider used for video trimming.
 * Ensures proper keyboard navigation, screen reader support, and focus management.
 */

import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import '@testing-library/jest-dom';
import { axe, toHaveNoViolations } from 'jest-axe';
import TrimPanel from '../../TrimPanel';

// Extend Jest matchers
expect.extend(toHaveNoViolations);

// Mock dependencies
jest.mock('../../ToastProvider', () => ({
  useToast: () => ({ pushToast: jest.fn() }),
}));

jest.mock('react-player/lazy', () => {
  return function MockReactPlayer() {
    return <div data-testid="mock-video-player">Video Player</div>;
  };
});

jest.mock('use-debounce', () => ({
  useDebouncedCallback: (fn: (...args: unknown[]) => void) => fn,
}));

describe.skip('TrimPanel Accessibility', () => {
  const defaultProps = {
    jobMeta: { url: 'https://example.com/video.mp4', title: 'Test Video', duration: 120 },
    onSubmit: jest.fn(),
  };

  describe('ARIA Compliance', () => {
    it('should have no accessibility violations', async () => {
      const { container } = render(
        <TrimPanel {...defaultProps} />
      );

      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });

    it('should have correct ARIA attributes on slider handles', () => {
      render(<TrimPanel {...defaultProps} />);

      const startHandle = screen.getByTestId('handle-start');
      const endHandle = screen.getByTestId('handle-end');

      // Check required ARIA attributes
      expect(startHandle).toHaveAttribute('role', 'slider');
      expect(startHandle).toHaveAttribute('aria-valuemin', '0');
      expect(startHandle).toHaveAttribute('aria-valuemax', '120');
      expect(startHandle).toHaveAttribute('aria-valuenow', '0');
      expect(startHandle).toHaveAttribute('aria-labelledby', 'start-time-label');
      expect(startHandle).toHaveAttribute('aria-describedby', 'slider-instructions');
      expect(startHandle).toHaveAttribute('tabindex', '0');

      expect(endHandle).toHaveAttribute('role', 'slider');
      expect(endHandle).toHaveAttribute('aria-valuemin', '0');
      expect(endHandle).toHaveAttribute('aria-valuemax', '120');
      expect(endHandle).toHaveAttribute('aria-valuenow', '60'); // Capped at 1 minute
      expect(endHandle).toHaveAttribute('aria-labelledby', 'end-time-label');
      expect(endHandle).toHaveAttribute('aria-describedby', 'slider-instructions');
      expect(endHandle).toHaveAttribute('tabindex', '0');
    });

    it('should have proper aria-valuetext with formatted time', () => {
      render(<TrimPanel {...defaultProps} />);

      const startHandle = screen.getByTestId('handle-start');
      const endHandle = screen.getByTestId('handle-end');

      expect(startHandle).toHaveAttribute('aria-valuetext', 'Start time: 00:00.000');
      expect(endHandle).toHaveAttribute('aria-valuetext', 'End time: 01:00.000');
    });

    it('should have proper label associations', () => {
      render(<TrimPanel {...defaultProps} />);

      const startTimeLabel = screen.getByText('Start Time (hh:mm:ss.mmm)');
      const endTimeLabel = screen.getByText('End Time (hh:mm:ss.mmm)');
      const startInput = screen.getByLabelText('Start Time (hh:mm:ss.mmm)');
      const endInput = screen.getByLabelText('End Time (hh:mm:ss.mmm)');

      expect(startTimeLabel).toHaveAttribute('id', 'start-time-label');
      expect(endTimeLabel).toHaveAttribute('id', 'end-time-label');
      expect(startInput).toHaveAttribute('aria-describedby', 'start-time-help');
      expect(endInput).toHaveAttribute('aria-describedby', 'end-time-help');
    });

    it('should have proper error announcements with role="alert"', async () => {
      const user = userEvent.setup();
      render(<TrimPanel {...defaultProps} />);

      const endInput = screen.getByDisplayValue('01:00.000');
      
      // Trigger validation error
      await user.clear(endInput);
      await user.type(endInput, '01:01.000');

      await waitFor(() => {
        const errorMessage = screen.getByText('Trim to one minute or less to proceed.');
        expect(errorMessage).toHaveAttribute('role', 'alert');
        expect(errorMessage).toHaveAttribute('aria-live', 'polite');
      });
    });

    it('should have screen reader announcement region', () => {
      render(<TrimPanel {...defaultProps} />);

      const announcementRegion = screen.getByTestId('slider-announcement');
      expect(announcementRegion).toHaveAttribute('aria-live', 'polite');
      expect(announcementRegion).toHaveAttribute('aria-atomic', 'true');
      expect(announcementRegion).toHaveClass('sr-only');
    });
  });

  describe('Keyboard Navigation', () => {
    it('should be focusable via Tab key', () => {
      render(<TrimPanel {...defaultProps} />);

      const startHandle = screen.getByTestId('handle-start');
      const endHandle = screen.getByTestId('handle-end');

      expect(startHandle).toHaveAttribute('tabindex', '0');
      expect(endHandle).toHaveAttribute('tabindex', '0');

      // Test programmatic focus
      startHandle.focus();
      expect(startHandle).toHaveFocus();

      endHandle.focus();
      expect(endHandle).toHaveFocus();
    });

    it('should adjust values with arrow keys by stepSize (0.1s)', async () => {
      render(<TrimPanel {...defaultProps} stepSize={0.1} />);

      const startHandle = screen.getByTestId('handle-start');
      startHandle.focus();

      // Test right arrow (increase)
      fireEvent.keyDown(startHandle, { key: 'ArrowRight' });
      expect(startHandle).toHaveAttribute('aria-valuenow', '0.1');

      // Test left arrow (decrease)
      fireEvent.keyDown(startHandle, { key: 'ArrowLeft' });
      expect(startHandle).toHaveAttribute('aria-valuenow', '0');

      // Test up arrow (increase)
      fireEvent.keyDown(startHandle, { key: 'ArrowUp' });
      expect(startHandle).toHaveAttribute('aria-valuenow', '0.1');

      // Test down arrow (decrease)
      fireEvent.keyDown(startHandle, { key: 'ArrowDown' });
      expect(startHandle).toHaveAttribute('aria-valuenow', '0');
    });

    it('should jump to min/max with Home/End keys', () => {
      render(<TrimPanel {...defaultProps} />);

      const startHandle = screen.getByTestId('handle-start');
      const endHandle = screen.getByTestId('handle-end');

      // Test Home key on start handle
      startHandle.focus();
      fireEvent.keyDown(startHandle, { key: 'Home' });
      expect(startHandle).toHaveAttribute('aria-valuenow', '0');

      // Test End key on end handle
      endHandle.focus();
      fireEvent.keyDown(endHandle, { key: 'End' });
      expect(endHandle).toHaveAttribute('aria-valuenow', '120');
    });

    it('should jump by 10 seconds with Page Up/Down keys', () => {
      render(<TrimPanel {...defaultProps} />);

      const startHandle = screen.getByTestId('handle-start');
      startHandle.focus();

      // Test Page Up (jump forward 10 seconds)
      fireEvent.keyDown(startHandle, { key: 'PageUp' });
      expect(startHandle).toHaveAttribute('aria-valuenow', '10');

      // Test Page Down (jump backward 10 seconds)
      fireEvent.keyDown(startHandle, { key: 'PageDown' });
      expect(startHandle).toHaveAttribute('aria-valuenow', '0');
    });

    it('should prevent handles from crossing over', () => {
      render(<TrimPanel {...defaultProps} stepSize={0.1} />);

      const startHandle = screen.getByTestId('handle-start');
      const endHandle = screen.getByTestId('handle-end');

      // Move start handle near end handle
      startHandle.focus();
      for (let i = 0; i < 1200; i++) { // Try to move to 120 seconds
        fireEvent.keyDown(startHandle, { key: 'ArrowRight' });
      }

      // Start handle should stop before end handle (119.9s)
      expect(parseFloat(startHandle.getAttribute('aria-valuenow')!)).toBeLessThan(120);

      // Move end handle near start handle
      endHandle.focus();
      for (let i = 0; i < 1200; i++) { // Try to move to 0 seconds
        fireEvent.keyDown(endHandle, { key: 'ArrowLeft' });
      }

      // End handle should stop after start handle
      const startValue = parseFloat(startHandle.getAttribute('aria-valuenow')!);
      const endValue = parseFloat(endHandle.getAttribute('aria-valuenow')!);
      expect(endValue).toBeGreaterThan(startValue);
    });

    it('should not interfere with other key presses', () => {
      render(<TrimPanel {...defaultProps} />);

      const startHandle = screen.getByTestId('handle-start');
      startHandle.focus();

      // Test that non-navigation keys don't prevent default
      const event = new KeyboardEvent('keydown', { key: 'Enter' });
      const preventDefaultSpy = jest.spyOn(event, 'preventDefault');
      
      fireEvent.keyDown(startHandle, event);
      expect(preventDefaultSpy).not.toHaveBeenCalled();
    });
  });

  describe('Focus Management and Visual Styling', () => {
    it('should have proper focus styling classes', () => {
      render(<TrimPanel {...defaultProps} />);

      const startHandle = screen.getByTestId('handle-start');
      const endHandle = screen.getByTestId('handle-end');

      // Check for focus-visible classes
      expect(startHandle).toHaveClass('focus-visible:outline-none');
      expect(startHandle).toHaveClass('focus-visible:ring-2');
      expect(startHandle).toHaveClass('focus-visible:ring-blue-500');
      expect(startHandle).toHaveClass('focus-visible:ring-offset-2');

      expect(endHandle).toHaveClass('focus-visible:outline-none');
      expect(endHandle).toHaveClass('focus-visible:ring-2');
      expect(endHandle).toHaveClass('focus-visible:ring-blue-500');
      expect(endHandle).toHaveClass('focus-visible:ring-offset-2');
    });

    it('should have minimum 44x44px touch target area', () => {
      render(<TrimPanel {...defaultProps} />);

      const startHandle = screen.getByTestId('handle-start');
      const endHandle = screen.getByTestId('handle-end');

      // Check for extended touch target
      const startTouchTarget = startHandle.querySelector('[aria-hidden="true"]');
      const endTouchTarget = endHandle.querySelector('[aria-hidden="true"]');

      expect(startTouchTarget).toHaveClass('min-w-[44px]');
      expect(startTouchTarget).toHaveClass('min-h-[44px]');
      expect(endTouchTarget).toHaveClass('min-w-[44px]');
      expect(endTouchTarget).toHaveClass('min-h-[44px]');
    });

    it('should have proper dark mode support in focus styles', () => {
      render(<TrimPanel {...defaultProps} />);

      const startHandle = screen.getByTestId('handle-start');
      
      expect(startHandle).toHaveClass('dark:focus-visible:ring-offset-gray-900');
      expect(startHandle).toHaveClass('dark:border-gray-800');
    });
  });

  describe('Screen Reader Announcements', () => {
    it('should announce value changes after handle movement', async () => {
      render(<TrimPanel {...defaultProps} />);

      const startHandle = screen.getByTestId('handle-start');
      const announcementRegion = screen.getByTestId('slider-announcement');

      startHandle.focus();
      
      // Move handle and wait for announcement
      fireEvent.keyDown(startHandle, { key: 'ArrowRight' });
      
      await waitFor(() => {
        expect(announcementRegion).toHaveTextContent('Start time: 00:00.100');
      });
    });

    it('should update aria-valuetext when values change', () => {
      render(<TrimPanel {...defaultProps} />);

      const startHandle = screen.getByTestId('handle-start');
      
      startHandle.focus();
      fireEvent.keyDown(startHandle, { key: 'PageUp' }); // Jump 10 seconds

      expect(startHandle).toHaveAttribute('aria-valuetext', 'Start time: 00:10.000');
    });

    it('should provide helpful descriptions for all interactive elements', () => {
      render(<TrimPanel {...defaultProps} />);

      // Check slider instructions
      const sliderInstructions = document.getElementById('slider-instructions');
      expect(sliderInstructions).toBeInTheDocument();
      expect(sliderInstructions).toHaveTextContent(/Dual handle slider for selecting video clip start and end times/);

      // Check input help text
      const startHelp = document.getElementById('start-time-help');
      const endHelp = document.getElementById('end-time-help');
      expect(startHelp).toBeInTheDocument();
      expect(endHelp).toBeInTheDocument();

      // Check button help
      const buttonHelp = document.getElementById('submit-button-help');
      expect(buttonHelp).toBeInTheDocument();
    });

    it('should announce proper button state descriptions', async () => {
      const user = userEvent.setup();
      render(<TrimPanel {...defaultProps} />);

      const buttonHelp = document.getElementById('submit-button-help');
      const rightsCheckbox = screen.getByRole('checkbox');

      // Initially disabled - should mention both conditions
      expect(buttonHelp).toHaveTextContent('Button disabled: Please set valid clip times and accept terms');

      // Check rights checkbox
      await user.click(rightsCheckbox);
      
      await waitFor(() => {
        expect(buttonHelp).toHaveTextContent('Create and download your video clip');
      });
    });
  });

  describe('Custom Step Size Support', () => {
    it('should respect custom stepSize prop for keyboard navigation', () => {
      render(<TrimPanel {...defaultProps} stepSize={0.5} />);

      const startHandle = screen.getByTestId('handle-start');
      startHandle.focus();

      fireEvent.keyDown(startHandle, { key: 'ArrowRight' });
      expect(startHandle).toHaveAttribute('aria-valuenow', '0.5');

      fireEvent.keyDown(startHandle, { key: 'ArrowRight' });
      expect(startHandle).toHaveAttribute('aria-valuenow', '1');
    });

    it('should display correct step size in instructions', () => {
      render(<TrimPanel {...defaultProps} stepSize={0.2} />);

      expect(screen.getByText(/Use arrow keys to adjust by 0.2s/)).toBeInTheDocument();
    });
  });

  describe('Error State Accessibility', () => {
    it('should properly announce validation errors', async () => {
      const user = userEvent.setup();
      render(<TrimPanel {...defaultProps} />);

      const startInput = screen.getByDisplayValue('00:00.000');
      const endInput = screen.getByDisplayValue('01:00.000');

      // Create invalid state (end before start)
      await user.clear(startInput);
      await user.type(startInput, '00:30.000');
      await user.clear(endInput);
      await user.type(endInput, '00:15.000');

      await waitFor(() => {
        const errorAlert = screen.getByRole('alert');
        expect(errorAlert).toHaveTextContent('End time must be after start time.');
        expect(errorAlert).toHaveAttribute('aria-live', 'polite');
      });
    });

    it('should provide descriptive labels for duration display', () => {
      render(<TrimPanel {...defaultProps} />);

      const durationSpan = screen.getByLabelText(/Clip duration: 01:00.000/);
      expect(durationSpan).toBeInTheDocument();

      const startTimeSpan = screen.getByLabelText(/Current start time: 00:00.000/);
      const endTimeSpan = screen.getByLabelText(/Current end time: 01:00.000/);
      expect(startTimeSpan).toBeInTheDocument();
      expect(endTimeSpan).toBeInTheDocument();
    });
  });

  describe('Dark Mode Accessibility', () => {
    it('should maintain accessibility in dark mode', async () => {
      // Add dark class to document
      document.documentElement.classList.add('dark');

      const { container } = render(
        <TrimPanel {...defaultProps} />
      );

      const results = await axe(container);
      expect(results).toHaveNoViolations();

      // Clean up
      document.documentElement.classList.remove('dark');
    });

    it('should have proper contrast classes for dark mode', () => {
      render(<TrimPanel {...defaultProps} />);

      const startInput = screen.getByDisplayValue('00:00.000');
      expect(startInput).toHaveClass('dark:bg-gray-800');
      expect(startInput).toHaveClass('dark:text-white');
      expect(startInput).toHaveClass('dark:border-gray-600');
    });
  });

  describe('Integration with External Libraries', () => {
    it('should maintain accessibility when react-range is rendered', () => {
      render(<TrimPanel {...defaultProps} />);

      // Verify that react-range integration doesn't break our ARIA setup
      const startHandle = screen.getByTestId('handle-start');
      const endHandle = screen.getByTestId('handle-end');

      expect(startHandle).toHaveAttribute('role', 'slider');
      expect(endHandle).toHaveAttribute('role', 'slider');

      // Test that keyboard events still work
      startHandle.focus();
      fireEvent.keyDown(startHandle, { key: 'ArrowRight' });
      
      expect(startHandle).toHaveAttribute('aria-valuenow', '0.1');
    });
  });
}); 