describe('🚀 Smoke Test - Critical User Flows', () => {
  const TEST_YOUTUBE_URL = 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'; // Rick Roll - short and reliable
  const INVALID_URL = 'https://example.com/not-a-video';
  const PRIVATE_VIDEO_URL = 'https://www.youtube.com/watch?v=invalid-private-video';

  beforeEach(() => {
    // Start from homepage
    cy.visit('/');
    
    // Ensure API is healthy before running tests
    cy.request('GET', 'http://localhost:8000/health').then((response) => {
      expect(response.status).to.eq(200);
    });
  });

  describe('✅ Happy Path - Complete Video Clip Flow', () => {
    it('should successfully clip a YouTube video from start to finish', () => {
      // Step 1: Paste URL and get metadata
      cy.get('[data-testid="url-input"]')
        .type(TEST_YOUTUBE_URL)
        .should('have.value', TEST_YOUTUBE_URL);

      cy.get('[data-testid="analyze-button"]')
        .click();

      // Wait for metadata to load
      cy.get('[data-testid="video-metadata"]', { timeout: 10000 })
        .should('be.visible');

      cy.get('[data-testid="video-title"]')
        .should('contain.text', 'Rick Astley');

      // Step 2: Set trim points (5 seconds clip)
      cy.get('[data-testid="start-time-input"]')
        .clear()
        .type('00:00:05');

      cy.get('[data-testid="end-time-input"]')
        .clear()
        .type('00:00:10');

      // Verify duration is calculated correctly
      cy.get('[data-testid="clip-duration"]')
        .should('contain.text', '5 seconds');

      // Step 3: Accept terms and create job
      cy.get('[data-testid="terms-checkbox"]')
        .check()
        .should('be.checked');

      cy.get('[data-testid="create-clip-button"]')
        .click();

      // Step 4: Wait for job completion and download
      cy.get('[data-testid="job-status"]', { timeout: 30000 })
        .should('contain.text', 'ready');

      cy.get('[data-testid="download-button"]')
        .should('be.visible')
        .and('not.be.disabled');

      // Verify download link functionality
      cy.get('[data-testid="download-button"]')
        .invoke('attr', 'href')
        .should('contain', '.mp4');

      // Test the download (verify it's a valid presigned URL)
      cy.get('[data-testid="download-button"]')
        .invoke('attr', 'href')
        .then((downloadUrl) => {
          cy.request('HEAD', downloadUrl as string).then((response) => {
            expect(response.status).to.eq(200);
            expect(response.headers['content-type']).to.contain('video');
          });
        });

      // Verify auto-copy functionality
      cy.get('[data-testid="copy-feedback"]')
        .should('contain.text', 'Copied to clipboard');
    });

    it('should handle slider-based trimming correctly', () => {
      // Navigate to trim page with URL
      cy.visit(`/trim?url=${encodeURIComponent(TEST_YOUTUBE_URL)}`);
      
      // Wait for video to load
      cy.get('[data-testid="video-player"]', { timeout: 10000 })
        .should('be.visible');

      // Test slider interaction
      cy.get('[data-testid="timeline-slider"]')
        .should('be.visible');

      // Simulate dragging start handle
      cy.get('[data-testid="start-handle"]')
        .trigger('mousedown', { which: 1 })
        .trigger('mousemove', { clientX: 100 })
        .trigger('mouseup');

      // Simulate dragging end handle  
      cy.get('[data-testid="end-handle"]')
        .trigger('mousedown', { which: 1 })
        .trigger('mousemove', { clientX: 200 })
        .trigger('mouseup');

      // Verify time inputs update
      cy.get('[data-testid="start-time-input"]')
        .should('not.have.value', '00:00:00');

      cy.get('[data-testid="end-time-input"]')
        .should('not.have.value', '00:00:00');
    });
  });

  describe('❌ Error State Validation', () => {
    it('should reject clips longer than 30 minutes', () => {
      // Navigate with a longer video URL
      cy.visit(`/trim?url=${encodeURIComponent(TEST_YOUTUBE_URL)}`);
      
      cy.get('[data-testid="video-metadata"]', { timeout: 10000 })
        .should('be.visible');

      // Try to set a 31-minute clip
      cy.get('[data-testid="start-time-input"]')
        .clear()
        .type('00:00:00');

      cy.get('[data-testid="end-time-input"]')
        .clear()
        .type('00:31:00');

      // Should show error message
      cy.get('[data-testid="duration-error"]')
        .should('be.visible')
        .and('contain.text', 'thirty minutes');

      // Create button should be disabled
      cy.get('[data-testid="create-clip-button"]')
        .should('be.disabled');
    });

    it('should handle invalid URLs gracefully', () => {
      cy.get('[data-testid="url-input"]')
        .type(INVALID_URL);

      cy.get('[data-testid="analyze-button"]')
        .click();

      // Should show error message
      cy.get('[data-testid="url-error"]', { timeout: 10000 })
        .should('be.visible')
        .and('contain.text', 'valid video URL');
    });

    it('should enforce terms acceptance', () => {
      cy.visit(`/trim?url=${encodeURIComponent(TEST_YOUTUBE_URL)}`);
      
      cy.get('[data-testid="video-metadata"]', { timeout: 10000 })
        .should('be.visible');

      // Set valid trim points
      cy.get('[data-testid="start-time-input"]')
        .clear()
        .type('00:00:05');

      cy.get('[data-testid="end-time-input"]')
        .clear()
        .type('00:00:10');

      // Don't check terms checkbox
      cy.get('[data-testid="terms-checkbox"]')
        .should('not.be.checked');

      // Button should be disabled
      cy.get('[data-testid="create-clip-button"]')
        .should('be.disabled');

      // Show error message
      cy.get('[data-testid="terms-error"]')
        .should('contain.text', 'accept the terms');
    });

    it('should handle queue full scenario', () => {
      // Mock queue full response
      cy.intercept('POST', '/api/v1/jobs', {
        statusCode: 429,
        body: { detail: 'Queue is full. Please try again later.' }
      }).as('queueFull');

      cy.visit(`/trim?url=${encodeURIComponent(TEST_YOUTUBE_URL)}`);
      
      cy.get('[data-testid="video-metadata"]', { timeout: 10000 })
        .should('be.visible');

      // Set valid clip and accept terms
      cy.get('[data-testid="start-time-input"]')
        .clear()
        .type('00:00:05');

      cy.get('[data-testid="end-time-input"]')
        .clear()
        .type('00:00:10');

      cy.get('[data-testid="terms-checkbox"]')
        .check();

      cy.get('[data-testid="create-clip-button"]')
        .click();

      cy.wait('@queueFull');

      // Should show queue full error
      cy.get('[data-testid="queue-error"]')
        .should('be.visible')
        .and('contain.text', 'Try again in a minute');
    });
  });

  describe('📱 Mobile Responsiveness', () => {
    beforeEach(() => {
      // Test on mobile viewport
      cy.viewport(360, 640);
    });

    it('should have touch-friendly controls on mobile', () => {
      cy.visit(`/trim?url=${encodeURIComponent(TEST_YOUTUBE_URL)}`);
      
      cy.get('[data-testid="video-metadata"]', { timeout: 10000 })
        .should('be.visible');

      // Slider handles should be large enough for touch
      cy.get('[data-testid="start-handle"]')
        .should('have.css', 'width')
        .and('match', /^(4[4-9]|[5-9]\d|\d{3,})px$/); // >= 44px

      cy.get('[data-testid="end-handle"]')
        .should('have.css', 'height')
        .and('match', /^(4[4-9]|[5-9]\d|\d{3,})px$/); // >= 44px

      // Buttons should be touch-friendly
      cy.get('[data-testid="create-clip-button"]')
        .should('have.css', 'min-height')
        .and('match', /^(4[4-9]|[5-9]\d|\d{3,})px$/); // >= 44px
    });

    it('should handle mobile layout correctly', () => {
      cy.visit('/');

      // Main container should not overflow
      cy.get('body')
        .should('have.css', 'overflow-x', 'hidden');

      // Navigation should be responsive
      cy.get('[data-testid="main-nav"]')
        .should('be.visible');

      // Form elements should be properly sized
      cy.get('[data-testid="url-input"]')
        .should('be.visible')
        .and('have.css', 'width')
        .and('not.eq', '0px');
    });
  });

  describe('♿ Accessibility Validation', () => {
    it('should have proper focus management', () => {
      cy.visit('/');

      // Tab through key elements using keyboard commands
      cy.get('[data-testid="url-input"]').focus();
      cy.focused().should('have.attr', 'data-testid', 'url-input');

      cy.focused().type('{tab}');
      cy.focused().should('have.attr', 'data-testid', 'analyze-button');

      // Focus should be visible (check for outline or box-shadow)
      cy.focused().then(($el) => {
        const outlineStyle = $el.css('outline-style');
        const boxShadow = $el.css('box-shadow');
        expect(outlineStyle !== 'none' || boxShadow !== 'none').to.be.true;
      });
    });

    it('should have proper ARIA labels', () => {
      cy.visit(`/trim?url=${encodeURIComponent(TEST_YOUTUBE_URL)}`);
      
      cy.get('[data-testid="video-metadata"]', { timeout: 10000 })
        .should('be.visible');

      // Slider should have proper ARIA attributes
      cy.get('[data-testid="timeline-slider"]')
        .should('have.attr', 'role', 'slider')
        .and('have.attr', 'aria-label');

      // Form controls should be properly labeled
      cy.get('[data-testid="start-time-input"]').then(($el) => {
        expect($el.attr('aria-label') || $el.attr('aria-labelledby')).to.exist;
      });

      cy.get('[data-testid="terms-checkbox"]')
        .should('have.attr', 'aria-describedby');
    });
  });

  describe('🔗 Link Sharing & Deep Links', () => {
    it('should handle direct navigation to trim page', () => {
      const testUrl = encodeURIComponent(TEST_YOUTUBE_URL);
      cy.visit(`/trim?url=${testUrl}&start=5&end=10`);

      // Should automatically load video metadata
      cy.get('[data-testid="video-metadata"]', { timeout: 10000 })
        .should('be.visible');

      // Should pre-populate trim points from URL params
      cy.get('[data-testid="start-time-input"]')
        .should('have.value', '00:00:05');

      cy.get('[data-testid="end-time-input"]')
        .should('have.value', '00:00:10');
    });

    it('should update URL when trim points change', () => {
      cy.visit(`/trim?url=${encodeURIComponent(TEST_YOUTUBE_URL)}`);
      
      cy.get('[data-testid="video-metadata"]', { timeout: 10000 })
        .should('be.visible');

      cy.get('[data-testid="start-time-input"]')
        .clear()
        .type('00:00:15');

      // URL should update with new start time
      cy.url().should('include', 'start=15');
    });
  });

  describe('⚡ Performance Validation', () => {
    it('should load initial page quickly', () => {
      const startTime = Date.now();
      
      cy.visit('/').then(() => {
        const loadTime = Date.now() - startTime;
        expect(loadTime).to.be.lessThan(3000); // 3 second threshold
      });

      // Critical content should be visible quickly
      cy.get('[data-testid="url-input"]', { timeout: 2000 })
        .should('be.visible');
    });

    it('should handle multiple rapid interactions', () => {
      cy.visit(`/trim?url=${encodeURIComponent(TEST_YOUTUBE_URL)}`);
      
      cy.get('[data-testid="video-metadata"]', { timeout: 10000 })
        .should('be.visible');

      // Rapidly change trim points
      for (let i = 5; i < 15; i++) {
        cy.get('[data-testid="start-time-input"]')
          .clear()
          .type(`00:00:${i.toString().padStart(2, '0')}`);
      }

      // Should handle all updates without errors
      cy.get('[data-testid="clip-duration"]')
        .should('be.visible');
    });
  });
}); 