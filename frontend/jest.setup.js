import '@testing-library/jest-dom';
import { toHaveNoViolations } from 'jest-axe';

// Extend Jest matchers to include jest-axe accessibility matchers
expect.extend(toHaveNoViolations);

// Configure jest-axe for consistent testing
import { configureAxe } from 'jest-axe';

// Configure axe with project-specific rules
const axe = configureAxe({
  rules: {
    // Enable additional accessibility rules
    'color-contrast-enhanced': { enabled: true },
    'focus-order-semantics': { enabled: true },
    'hidden-content': { enabled: true },
    'landmark-no-duplicate-banner': { enabled: true },
    'landmark-no-duplicate-contentinfo': { enabled: true },
    'region': { enabled: true },
  },
  tags: ['wcag2a', 'wcag2aa', 'wcag21aa', 'best-practice'],
  // Ignore violations from third-party components we can't control
  exclude: [
    '[data-testid="react-player"]', // React Player component
  ],
});

// Make axe available globally for tests
global.axe = axe; 