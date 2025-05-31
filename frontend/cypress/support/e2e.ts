import 'cypress-real-events';
import '@percy/cypress';

// Extend Cypress types to include Percy commands
declare global {
  namespace Cypress {
    interface Chainable {
      percySnapshot(name: string, options?: { widths?: number[] }): void;
    }
  }
} 