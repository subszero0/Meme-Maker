describe('Clip Downloader E2E Flow', () => {
  beforeEach(() => {
    // Intercept POST /jobs to return job ID
    cy.intercept('POST', '/api/v1/jobs', { 
      statusCode: 201,
      body: { jobId: 'test123' }
    }).as('createJob');

    // Intercept GET /jobs/test123 with sequential responses
    cy.intercept('GET', '/api/v1/jobs/test123', { 
      statusCode: 200,
      body: { status: 'queued' }
    }).as('poll');

    // Setup sequential responses for polling
    let pollCount = 0;
    cy.intercept('GET', '/api/v1/jobs/test123', (req) => {
      pollCount++;
      if (pollCount === 1) {
        req.reply({ statusCode: 200, body: { status: 'queued' } });
      } else if (pollCount === 2) {
        req.reply({ statusCode: 200, body: { status: 'working', progress: 42 } });
      } else {
        req.reply({ statusCode: 200, body: { status: 'done', download_url: '/fixtures/final.mp4' } });
      }
    }).as('poll');

    // Intercept metadata fetch to return video info
    cy.intercept('POST', '/api/v1/metadata', {
      statusCode: 200,
      body: {
        url: 'https://youtu.be/dQw4w9WgXcQ',
        title: 'Test Video - Never Gonna Give You Up',
        duration: 212 // 3:32 in seconds
      }
    }).as('fetchMetadata');
  });

  it('should complete the full clip downloader flow', () => {
    // 1. Visit the homepage
    cy.visit('/');

    // 2. Type the URL into the input
    cy.get('[data-testid="url-input"]')
      .should('be.visible')
      .realType('https://youtu.be/dQw4w9WgXcQ');

    // 3. Click the Start button
    cy.get('[data-testid="start-button"]')
      .should('be.visible')
      .should('not.be.disabled')
      .click();

    // Wait for metadata fetch
    cy.wait('@fetchMetadata');

    // Should now see the trim panel
    cy.get('[data-testid="start-time"]')
      .should('be.visible');

    // 6. Trim the clip to 0:01 - 0:05 using timestamp inputs
    cy.get('[data-testid="start-time"]')
      .clear()
      .realType('00:01.000');

    cy.get('[data-testid="end-time"]')
      .clear()
      .realType('00:05.000');

    // 7. Tick the rights checkbox
    cy.get('[data-testid="rights-checkbox"]')
      .should('be.visible')
      .check();

    // 8. Click "Clip & Download" button
    cy.get('[data-testid="clip-btn"]')
      .should('be.visible')
      .should('not.be.disabled')
      .click();

    // Wait for job creation
    cy.wait('@createJob');

    // 9. Wait for the 3rd polling response and assert DownloadModal is visible
    cy.wait('@poll'); // 1st call - queued
    cy.wait('@poll'); // 2nd call - working
    cy.wait('@poll'); // 3rd call - done

    // Assert the DownloadModal is visible and has correct download link
    cy.get('[data-testid="download-btn"]')
      .should('be.visible')
      .should('have.attr', 'href', '/fixtures/final.mp4');

    // Verify modal content
    cy.contains('Clip ready!').should('be.visible');
    cy.contains('File will self-destruct after this download.').should('be.visible');
  });

  it('should handle network errors gracefully', () => {
    // Override metadata intercept to simulate error
    cy.intercept('POST', '/api/v1/metadata', {
      statusCode: 500,
      body: { error: 'Server error' }
    }).as('fetchMetadataError');

    cy.visit('/');

    cy.get('[data-testid="url-input"]')
      .realType('https://youtu.be/invalid');

    cy.get('[data-testid="start-button"]').click();

    cy.wait('@fetchMetadataError');

    // Should remain on the input screen
    cy.get('[data-testid="url-input"]').should('be.visible');
  });

  it('should validate clip duration limits', () => {
    cy.visit('/');

    cy.get('[data-testid="url-input"]')
      .realType('https://youtu.be/dQw4w9WgXcQ');

    cy.get('[data-testid="start-button"]').click();

    cy.wait('@fetchMetadata');

    // Try to set a clip longer than 3 minutes
    cy.get('[data-testid="start-time"]')
      .clear()
      .realType('00:00.000');

    cy.get('[data-testid="end-time"]')
      .clear()
      .realType('03:01.000'); // 3 minutes 1 second

    // Should show validation error
    cy.contains('Trim to three minutes or less to proceed.')
      .should('be.visible');

    // Clip button should remain disabled even with rights checked
    cy.get('[data-testid="rights-checkbox"]').check();
    cy.get('[data-testid="clip-btn"]').should('be.disabled');
  });
}); 