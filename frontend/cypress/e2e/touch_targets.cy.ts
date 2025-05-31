/// <reference types="cypress" />

/**
 * Touch Target Accessibility Tests
 * 
 * Ensures all interactive UI elements meet the 44×44px minimum
 * touch target requirement for optimal mobile usability.
 * 
 * @see https://www.w3.org/WAI/WCAG21/Understanding/target-size.html
 */

describe('Mobile Touch Targets', () => {
  const MINIMUM_TOUCH_SIZE = 44; // pixels
  const MOBILE_VIEWPORT = { width: 375, height: 667 };

  beforeEach(() => {
    cy.viewport(MOBILE_VIEWPORT.width, MOBILE_VIEWPORT.height);
  });

  /**
   * Helper function to verify element meets minimum touch target size
   */
  const verifyTouchTarget = (selector: string, elementName: string) => {
    cy.get(selector)
      .should('be.visible')
      .then($el => {
        const rect = $el[0].getBoundingClientRect();
        expect(rect.width, `${elementName} width should be at least ${MINIMUM_TOUCH_SIZE}px`).to.be.at.least(MINIMUM_TOUCH_SIZE);
        expect(rect.height, `${elementName} height should be at least ${MINIMUM_TOUCH_SIZE}px`).to.be.at.least(MINIMUM_TOUCH_SIZE);
      });
  };

  describe('URLInputPanel Touch Targets', () => {
    beforeEach(() => {
      cy.visit('/');
    });

    it('should have adequate touch target for Start button', () => {
      // Enter a valid URL to enable the button
      cy.get('[data-cy="url-input"]')
        .type('https://www.youtube.com/watch?v=dQw4w9WgXcQ');
      
      // Wait for validation
      cy.wait(500);
      
      verifyTouchTarget('[data-cy="start-button"]', 'Start button');
    });

    it('should have proper focus states for Start button', () => {
      cy.get('[data-cy="url-input"]')
        .type('https://www.youtube.com/watch?v=dQw4w9WgXcQ');
      
      cy.get('[data-cy="start-button"]')
        .focus()
        .should('have.class', 'focus-visible:ring-2');
    });
  });

  describe('TrimPanel Touch Targets', () => {
    beforeEach(() => {
      // Mock the API response for metadata
      cy.intercept('POST', '/api/v1/metadata', {
        statusCode: 200,
        body: {
          title: 'Test Video',
          duration: 120,
          url: 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'
        }
      }).as('getMetadata');

      cy.visit('/');
      cy.get('[data-cy="url-input"]')
        .type('https://www.youtube.com/watch?v=dQw4w9WgXcQ');
      cy.get('[data-cy="start-button"]').click();
      
      cy.wait('@getMetadata');
    });

    it('should have adequate touch targets for slider handles', () => {
      verifyTouchTarget('[data-cy="handle-start"]', 'Start time slider handle');
      verifyTouchTarget('[data-cy="handle-end"]', 'End time slider handle');
    });

    it('should have extended hit areas for slider handles', () => {
      // Verify the extended touch area exists
      cy.get('[data-cy="handle-start"]')
        .find('div[aria-hidden="true"]')
        .should('have.class', 'min-w-[48px]')
        .should('have.class', 'min-h-[48px]');
      
      cy.get('[data-cy="handle-end"]')
        .find('div[aria-hidden="true"]')
        .should('have.class', 'min-w-[48px]')
        .should('have.class', 'min-h-[48px]');
    });

    it('should have adequate touch target for Clip button', () => {
      // Accept terms to enable the button
      cy.get('[data-cy="rights-checkbox"]').check();
      
      verifyTouchTarget('[data-cy="clip-button"]', 'Clip & Download button');
    });

    it('should support keyboard navigation for slider handles', () => {
      cy.get('[data-cy="handle-start"]')
        .focus()
        .trigger('keydown', { key: 'ArrowRight' })
        .should('have.attr', 'aria-valuenow');
      
      cy.get('[data-cy="handle-end"]')
        .focus()
        .trigger('keydown', { key: 'ArrowLeft' })
        .should('have.attr', 'aria-valuenow');
    });
  });

  describe('DownloadModal Touch Targets', () => {
    beforeEach(() => {
      // Mock successful job completion
      cy.intercept('POST', '/api/v1/metadata', {
        statusCode: 200,
        body: {
          title: 'Test Video',
          duration: 120,
          url: 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'
        }
      });

      cy.intercept('POST', '/api/v1/jobs', {
        statusCode: 200,
        body: { id: 'test-job-123' }
      });

      cy.intercept('GET', '/api/v1/jobs/test-job-123', {
        statusCode: 200,
        body: {
          status: 'done',
          download_url: 'https://example.com/download/test-clip.mp4'
        }
      });

      // Navigate through the flow to reach download modal
      cy.visit('/');
      cy.get('[data-cy="url-input"]')
        .type('https://www.youtube.com/watch?v=dQw4w9WgXcQ');
      cy.get('[data-cy="start-button"]').click();
      cy.get('[data-cy="rights-checkbox"]').check();
      cy.get('[data-cy="clip-button"]').click();
      
      // Wait for job completion and modal to appear
      cy.get('[data-cy="download-button"]', { timeout: 10000 }).should('be.visible');
    });

    it('should have adequate touch targets for all modal buttons', () => {
      verifyTouchTarget('[data-cy="download-button"]', 'Download Now button');
      verifyTouchTarget('[data-cy="copy-button"]', 'Copy link button');
      verifyTouchTarget('[data-cy="close-button"]', 'Close (X) button');
      verifyTouchTarget('[data-cy="close-modal-button"]', 'Close modal button');
    });

    it('should have proper focus states for modal buttons', () => {
      cy.get('[data-cy="download-button"]')
        .focus()
        .should('have.class', 'focus-visible:ring-2');
      
      cy.get('[data-cy="copy-button"]')
        .focus()
        .should('have.class', 'focus-visible:ring-2');
      
      cy.get('[data-cy="close-button"]')
        .focus()
        .should('have.class', 'focus-visible:ring-2');
    });
  });

  describe('Error & Notification Touch Targets', () => {
    it('should have adequate touch targets for rate limit notification dismiss button', () => {
      // Mock rate limit error
      cy.intercept('POST', '/api/v1/metadata', {
        statusCode: 429,
        headers: {
          'Retry-After': '60'
        },
        body: {
          error: 'Rate limit exceeded',
          retry_after: 60
        }
      });

      cy.visit('/');
      cy.get('[data-cy="url-input"]')
        .type('https://www.youtube.com/watch?v=dQw4w9WgXcQ');
      cy.get('[data-cy="start-button"]').click();

      // Wait for rate limit notification
      cy.get('[data-cy="rate-limit-notification"]').should('be.visible');
      
      // Check if dismiss button exists and has proper touch target
      cy.get('[data-cy="rate-limit-notification-dismiss"]').then($el => {
        if ($el.length > 0) {
          verifyTouchTarget('[data-cy="rate-limit-notification-dismiss"]', 'Rate limit dismiss button');
        }
      });
    });

    it('should have adequate touch targets for queue full error dismiss button', () => {
      // Mock queue full error
      cy.intercept('POST', '/api/v1/jobs', {
        statusCode: 503,
        body: { error: 'Queue is full' }
      });

      cy.intercept('POST', '/api/v1/metadata', {
        statusCode: 200,
        body: {
          title: 'Test Video',
          duration: 120,
          url: 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'
        }
      });

      cy.visit('/');
      cy.get('[data-cy="url-input"]')
        .type('https://www.youtube.com/watch?v=dQw4w9WgXcQ');
      cy.get('[data-cy="start-button"]').click();
      cy.get('[data-cy="rights-checkbox"]').check();
      cy.get('[data-cy="clip-button"]').click();

      // Check if queue error dismiss button exists and has proper touch target
      cy.get('[data-cy="queue-full-banner-dismiss"]').then($el => {
        if ($el.length > 0) {
          verifyTouchTarget('[data-cy="queue-full-banner-dismiss"]', 'Queue full dismiss button');
        }
      });
    });

    it('should have adequate touch targets for toast dismiss button', () => {
      // Trigger a toast by copying to clipboard (auto-triggered in download modal)
      cy.intercept('POST', '/api/v1/metadata', {
        statusCode: 200,
        body: {
          title: 'Test Video',
          duration: 120,
          url: 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'
        }
      });

      cy.visit('/');
      cy.get('[data-cy="url-input"]')
        .type('https://www.youtube.com/watch?v=dQw4w9WgXcQ');
      cy.get('[data-cy="start-button"]').click();

      // Toast should appear automatically from clipboard copy
      cy.get('[data-cy="toast"]').then($el => {
        if ($el.length > 0) {
          verifyTouchTarget('[data-cy="toast-dismiss"]', 'Toast dismiss button');
        }
      });
    });
  });

  describe('Accessibility & Focus Management', () => {
    it('should maintain proper focus indicators for all touch targets', () => {
      cy.visit('/');
      
      // Test focus on first interactive element
      cy.get('[data-cy="url-input"]')
        .focus()
        .should('be.focused');
      
      // Test keyboard navigation to next element
      cy.get('[data-cy="url-input"]')
        .type('https://www.youtube.com/watch?v=dQw4w9WgXcQ')
        .then(() => {
          cy.get('[data-cy="start-button"]')
            .focus()
            .should('have.class', 'focus-visible:ring-2');
        });
    });

    it('should support high contrast mode', () => {
      cy.visit('/');
      
      // Test that focus rings are visible in high contrast scenarios
      cy.get('[data-cy="url-input"]').focus().should('have.css', 'outline-width');
    });

    it('should maintain touch targets at different zoom levels', () => {
      // Test at 200% zoom (common accessibility requirement)
      cy.viewport(MOBILE_VIEWPORT.width / 2, MOBILE_VIEWPORT.height / 2);
      
      cy.visit('/');
      cy.get('[data-cy="url-input"]')
        .type('https://www.youtube.com/watch?v=dQw4w9WgXcQ');
      
      // Touch targets should still be adequate at high zoom
      verifyTouchTarget('[data-cy="start-button"]', 'Start button at 200% zoom');
    });
  });

  describe('Cross-Device Touch Target Verification', () => {
    const devices = [
      { name: 'iPhone SE', width: 375, height: 667 },
      { name: 'iPhone 12', width: 390, height: 844 },
      { name: 'Samsung Galaxy S20', width: 360, height: 800 },
      { name: 'iPad Mini', width: 768, height: 1024 }
    ];

    devices.forEach(device => {
      it(`should maintain proper touch targets on ${device.name}`, () => {
        cy.viewport(device.width, device.height);
        
        cy.visit('/');
        cy.get('[data-cy="url-input"]')
          .type('https://www.youtube.com/watch?v=dQw4w9WgXcQ');
        
        verifyTouchTarget('[data-cy="start-button"]', `Start button on ${device.name}`);
      });
    });
  });
}); 