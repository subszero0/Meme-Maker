describe('Rate Limiting', () => {
  beforeEach(() => {
    cy.visit('/');
  });

  it('should show rate limit notification when 429 error occurs', () => {
    // Intercept metadata request and return 429
    cy.intercept('POST', '/api/v1/metadata', {
      statusCode: 429,
      headers: {
        'Retry-After': '60'
      },
      body: {
        detail: 'Rate limit exceeded. You can make 10 requests per minute. Please try again in 60 seconds.',
        retry_after: 60,
        limit_type: 'global'
      }
    }).as('rateLimitedMetadata');

    // Try to submit URL
    cy.get('[data-testid="url-input"]').type('https://www.youtube.com/watch?v=dQw4w9WgXcQ');
    cy.get('[data-testid="start-button"]').click();

    // Should show rate limit notification
    cy.get('[data-testid="rate-limit-notification"]').should('be.visible');
    cy.get('[data-testid="rate-limit-notification"]').should('contain', 'Rate Limit Exceeded');
    cy.get('[data-testid="rate-limit-notification"]').should('contain', 'Rate limit exceeded');
    
    // Should show countdown timer
    cy.get('[data-testid="rate-limit-notification"]').should('contain', '1m 0s');
    
    // Button should be disabled
    cy.get('[data-testid="start-button"]').should('be.disabled');
  });

  it('should show job creation rate limit notification', () => {
    // First, intercept metadata to succeed
    cy.intercept('POST', '/api/v1/metadata', {
      statusCode: 200,
      body: {
        url: 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
        title: 'Sample Video',
        duration: 120,
        thumbnail_url: 'https://example.com/thumb.jpg',
        resolutions: ['720p', '1080p']
      }
    }).as('successfulMetadata');

    // Then intercept job creation to return 429
    cy.intercept('POST', '/api/v1/jobs', {
      statusCode: 429,
      headers: {
        'Retry-After': '120'
      },
      body: {
        detail: 'Job creation limit exceeded. You can create 3 jobs per hour. Please try again in 120 seconds.',
        retry_after: 120,
        limit_type: 'job_creation'
      }
    }).as('rateLimitedJob');

    // Submit URL successfully
    cy.get('[data-testid="url-input"]').type('https://www.youtube.com/watch?v=dQw4w9WgXcQ');
    cy.get('[data-testid="start-button"]').click();

    // Wait for trim panel to appear
    cy.get('[data-testid="start-time"]').should('be.visible');
    
    // Check rights checkbox
    cy.get('[data-testid="rights-checkbox"]').check();
    
    // Try to create job
    cy.get('[data-testid="clip-btn"]').click();

    // Should show job creation rate limit notification
    cy.get('[data-testid="rate-limit-notification"]').should('be.visible');
    cy.get('[data-testid="rate-limit-notification"]').should('contain', 'Job Creation Limit Reached');
    cy.get('[data-testid="rate-limit-notification"]').should('contain', 'Job creation limit exceeded');
    
    // Should show countdown timer
    cy.get('[data-testid="rate-limit-notification"]').should('contain', '2m 0s');
    
    // Clip button should be disabled
    cy.get('[data-testid="clip-btn"]').should('be.disabled');
  });

  it('should enable retry after countdown expires', () => {
    // Intercept metadata request with short retry time for testing
    cy.intercept('POST', '/api/v1/metadata', {
      statusCode: 429,
      headers: {
        'Retry-After': '2'
      },
      body: {
        detail: 'Rate limit exceeded. You can make 10 requests per minute. Please try again in 2 seconds.',
        retry_after: 2,
        limit_type: 'global'
      }
    }).as('rateLimitedMetadata');

    // Try to submit URL
    cy.get('[data-testid="url-input"]').type('https://www.youtube.com/watch?v=dQw4w9WgXcQ');
    cy.get('[data-testid="start-button"]').click();

    // Should show rate limit notification
    cy.get('[data-testid="rate-limit-notification"]').should('be.visible');
    
    // Button should be disabled initially
    cy.get('[data-testid="start-button"]').should('be.disabled');
    
    // Wait for countdown to expire (3 seconds to be safe)
    cy.wait(3000);
    
    // Notification should disappear and button should be enabled
    cy.get('[data-testid="rate-limit-notification"]').should('not.exist');
    cy.get('[data-testid="start-button"]').should('not.be.disabled');
  });

  it('should allow dismissing the rate limit notification', () => {
    // Intercept metadata request and return 429
    cy.intercept('POST', '/api/v1/metadata', {
      statusCode: 429,
      headers: {
        'Retry-After': '60'
      },
      body: {
        detail: 'Rate limit exceeded. You can make 10 requests per minute. Please try again in 60 seconds.',
        retry_after: 60,
        limit_type: 'global'
      }
    }).as('rateLimitedMetadata');

    // Try to submit URL
    cy.get('[data-testid="url-input"]').type('https://www.youtube.com/watch?v=dQw4w9WgXcQ');
    cy.get('[data-testid="start-button"]').click();

    // Should show rate limit notification
    cy.get('[data-testid="rate-limit-notification"]').should('be.visible');
    
    // Click dismiss button
    cy.get('[data-testid="rate-limit-notification"]').contains('Dismiss').click();
    
    // Notification should disappear
    cy.get('[data-testid="rate-limit-notification"]').should('not.exist');
  });
}); 