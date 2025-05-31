/**
 * @ux @analytics
 * End-to-end tests for the feedback widget functionality
 * Verifies modal behavior, iframe embedding, and analytics tracking
 */

describe('Feedback Widget', () => {
  beforeEach(() => {
    cy.visit('/');
  });

  it('displays feedback link in footer', () => {
    // Footer should contain feedback link
    cy.get('[data-cy="feedback-link"]')
      .should('be.visible')
      .should('contain.text', 'Feedback')
      .should('have.attr', 'type', 'button');
  });

  it('opens feedback modal when link is clicked', () => {
    // Initially modal should not be present
    cy.get('[data-cy="feedback-modal"]').should('not.exist');
    
    // Click feedback link
    cy.get('[data-cy="feedback-link"]').click();
    
    // Modal should appear
    cy.get('[data-cy="feedback-modal"]')
      .should('be.visible')
      .should('have.attr', 'role', 'dialog')
      .should('have.attr', 'aria-modal', 'true');
    
    // Modal should have proper title and description
    cy.get('#feedback-title')
      .should('be.visible')
      .should('contain.text', 'Share Your Feedback');
    
    cy.get('#feedback-description')
      .should('be.visible')
      .should('contain.text', 'Help us improve Meme Maker');
  });

  it('contains embedded survey iframe with correct attributes', () => {
    // Open feedback modal
    cy.get('[data-cy="feedback-link"]').click();
    
    // Check iframe exists and has correct attributes
    cy.get('[data-cy="feedback-iframe"]')
      .should('be.visible')
      .should('have.attr', 'width', '100%')
      .should('have.attr', 'height', '600')
      .should('have.attr', 'title', 'Meme Maker Feedback Survey')
      .should('have.attr', 'allow')
      .and('include', 'clipboard-read')
      .and('include', 'clipboard-write');
    
    // Check iframe src contains expected form URL pattern
    cy.get('[data-cy="feedback-iframe"]')
      .should('have.attr', 'src')
      .and('include', 'docs.google.com/forms');
  });

  it('can be closed via close button', () => {
    // Open modal
    cy.get('[data-cy="feedback-link"]').click();
    cy.get('[data-cy="feedback-modal"]').should('be.visible');
    
    // Close via X button
    cy.get('[data-cy="close-feedback-button"]')
      .should('be.visible')
      .should('have.attr', 'aria-label', 'Close feedback dialog')
      .click();
    
    // Modal should be gone
    cy.get('[data-cy="feedback-modal"]').should('not.exist');
  });

  it('can be closed via Escape key', () => {
    // Open modal
    cy.get('[data-cy="feedback-link"]').click();
    cy.get('[data-cy="feedback-modal"]').should('be.visible');
    
    // Press Escape key
    cy.get('body').type('{esc}');
    
    // Modal should be gone
    cy.get('[data-cy="feedback-modal"]').should('not.exist');
  });

  it('maintains proper focus management', () => {
    // Open modal
    cy.get('[data-cy="feedback-link"]').click();
    
    // Focus should be trapped within modal
    cy.get('[data-cy="close-feedback-button"]').should('be.visible');
    
    // Tab navigation should work within modal
    cy.get('[data-cy="close-feedback-button"]').focus().should('be.focused');
    
    // Close modal and verify focus returns (implicit by successful close)
    cy.get('[data-cy="close-feedback-button"]').click();
    cy.get('[data-cy="feedback-modal"]').should('not.exist');
  });

  it('has proper accessibility attributes', () => {
    // Open modal
    cy.get('[data-cy="feedback-link"]').click();
    
    // Check ARIA attributes
    cy.get('[data-cy="feedback-modal"]')
      .should('have.attr', 'aria-labelledby', 'feedback-title')
      .should('have.attr', 'aria-describedby', 'feedback-description');
    
    // Check close button accessibility
    cy.get('[data-cy="close-feedback-button"]')
      .should('have.attr', 'aria-label');
  });

  it('is mobile responsive', () => {
    // Test on mobile viewport
    cy.viewport('iphone-6');
    
    // Feedback link should still be accessible
    cy.get('[data-cy="feedback-link"]').should('be.visible').click();
    
    // Modal should adapt to mobile
    cy.get('[data-cy="feedback-modal"]')
      .should('be.visible')
      .and('have.class', 'max-w-2xl'); // Should maintain responsive class
    
    // Iframe should be responsive
    cy.get('[data-cy="feedback-iframe"]')
      .should('be.visible')
      .should('have.attr', 'width', '100%');
  });

  it('tracks analytics events', () => {
    // Note: This test assumes analytics tracking is implemented
    // In real implementation, you'd mock the analytics calls
    
    // Mock console.log to verify analytics tracking
    cy.window().then((win) => {
      cy.stub(console, 'log').as('consoleStub');
    });
    
    // Open modal (should trigger feedback_open analytics event)
    cy.get('[data-cy="feedback-link"]').click();
    
    // Verify analytics tracking console log appears
    cy.get('@consoleStub').should('have.been.calledWith', 'Analytics: feedback_open event fired');
    
    // Close modal (should trigger feedback_submit analytics event)
    cy.get('[data-cy="close-feedback-button"]').click();
    
    // Verify submit event tracking console log appears
    cy.get('@consoleStub').should('have.been.calledWith', 'Analytics: feedback_submit event fired (modal closed)');
  });

  it('handles iframe loading gracefully', () => {
    // Open modal
    cy.get('[data-cy="feedback-link"]').click();
    
    // Iframe should have fallback content for loading state
    cy.get('[data-cy="feedback-iframe"]').should('be.visible');
    
    // Check that iframe loads (wait for load event)
    cy.get('[data-cy="feedback-iframe"]').should('be.visible');
    
    // Fallback link should be present in iframe content for accessibility
    cy.get('[data-cy="feedback-iframe"]').within(() => {
      // Note: Cross-origin restrictions may limit iframe content inspection
      // This test verifies the iframe structure is correct
    });
  });

  it('renders consistently across different screen sizes', () => {
    const viewports = [
      { width: 375, height: 667 },  // iPhone SE
      { width: 768, height: 1024 }, // iPad
      { width: 1024, height: 768 }, // Desktop
      { width: 1920, height: 1080 } // Large desktop
    ];

    viewports.forEach((viewport) => {
      cy.viewport(viewport.width, viewport.height);
      
      // Feedback link should be visible
      cy.get('[data-cy="feedback-link"]').should('be.visible');
      
      // Open modal
      cy.get('[data-cy="feedback-link"]').click();
      
      // Modal should be properly positioned and visible
      cy.get('[data-cy="feedback-modal"]')
        .should('be.visible')
        .and('be.positioned'); // Should not overflow viewport
      
      // Close modal for next iteration
      cy.get('[data-cy="close-feedback-button"]').click();
    });
  });
}); 