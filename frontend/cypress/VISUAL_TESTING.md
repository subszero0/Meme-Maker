# Visual Regression Testing with Percy

This document explains how to set up and run visual regression tests for the Meme Maker application using Percy and Cypress.

## Overview

Visual regression tests capture screenshots of the application in various states and compare them against baseline images to detect unintended visual changes. This helps catch UI regressions before they reach production.

## Test Coverage

The visual regression test suite covers these core user flows:

### 📸 **Screenshot Scenarios**

1. **URL Input Screen – Empty State**: Clean landing page with input field
2. **URL Input Screen – Loading State**: Input field with loading spinner
3. **Trim Panel – Default State**: Video player with default trim handles
4. **Trim Panel – Custom Selection**: Modified trim times and checked rights
5. **Processing State – Progress Bar**: Job processing with progress indicator
6. **Download Modal – Success State**: Completed job with download link
7. **Validation Error – Clip Too Long**: Error message for clips > 3 minutes
8. **Queue Full Error State**: Error banner when worker queue is full
9. **Rate Limit Notification**: Rate limiting warning with countdown
10. **Mobile Responsive States**: Mobile layouts for key screens
11. **Dark Mode States**: Dark theme variations

### 📱 **Viewport Testing**

Screenshots are captured at multiple viewport sizes:
- **Mobile**: 375px (iPhone SE)
- **Tablet**: 768px (iPad)
- **Desktop**: 1280px (Standard desktop)

## Setup

### 1. Install Dependencies

```bash
cd frontend
npm install @percy/cypress --save-dev
```

### 2. Percy Account Setup

1. Create a [Percy account](https://percy.io)
2. Create a new project named "meme-maker"
3. Get your project token from the Percy dashboard

### 3. Environment Variables

Add your Percy token to the environment:

```bash
# Local development
export PERCY_TOKEN=your-percy-token-here

# GitHub Actions (add as repository secret)
PERCY_TOKEN=your-percy-token-here
```

## Running Tests

### Local Development

```bash
# First time: Create baseline snapshots
npm run visual:baseline

# Subsequent runs: Compare against baseline
npm run visual:test

# Run without Percy (regular Cypress tests)
npm run cypress:run -- --spec 'cypress/e2e/visual_regression.cy.ts'
```

### GitHub Actions

Visual regression tests run automatically on:
- Pull requests to `main` or `develop` branches
- Pushes to `main` branch

The workflow:
1. Builds the frontend
2. Starts the backend server
3. Runs Cypress tests with Percy
4. Uploads results to Percy dashboard

## Configuration

### Percy Configuration (`.percy.yml`)

```yaml
version: 2
project: meme-maker
snapshot:
  widths: [375, 768, 1280]
  min-height: 768
  percy-css: |
    /* Hide dynamic elements that cause flakiness */
    .react-player video {
      background: #000 !important;
    }
```

### Test Configuration

Tests use consistent mocking to ensure stable visual states:

- **API Responses**: All network requests are mocked with predictable data
- **Timing**: Tests wait for UI to stabilize before taking screenshots
- **Viewport**: Consistent viewport sizes across test runs

## Best Practices

### ✅ Do's

- **Wait for stability**: Always wait for loading states to complete
- **Mock dynamic data**: Use consistent test data for predictable visuals
- **Test multiple viewports**: Ensure responsive design works correctly
- **Descriptive names**: Use clear, descriptive snapshot names
- **Group related tests**: Organize tests by user flow or component

### ❌ Don'ts

- **Don't test animations**: Pause or disable animations for consistent captures
- **Don't rely on external content**: Mock video content and metadata
- **Don't test time-dependent content**: Mock timestamps and progress indicators
- **Don't skip stabilization**: Always wait for UI to finish loading

## Troubleshooting

### Common Issues

**Flaky screenshots**: 
- Increase wait times in tests
- Mock more dynamic content
- Check for animations or loading states

**Percy token issues**:
- Verify token is correctly set in environment
- Check project name matches Percy dashboard

**Backend not starting**:
- Ensure Redis is running
- Check backend health endpoint
- Review CI logs for startup errors

### Debug Commands

```bash
# Run tests with browser visible (for debugging)
cd frontend
npx cypress open

# Run specific test file
npx cypress run --spec 'cypress/e2e/visual_regression.cy.ts'

# Skip Percy (faster for debugging)
npx cypress run --spec 'cypress/e2e/visual_regression.cy.ts' --config baseUrl=http://localhost:3000
```

## Workflow Integration

### Pull Request Process

1. **Developer creates PR**: Tests run automatically
2. **Percy compares**: Screenshots compared against main branch baseline
3. **Review differences**: Team reviews visual changes in Percy dashboard
4. **Approve/reject**: Approve if changes are intentional, reject if regressions

### Baseline Updates

When visual changes are intentional:

1. **Merge to main**: Approved changes become new baseline
2. **Auto-update**: Percy updates baseline screenshots
3. **Future comparisons**: New PRs compare against updated baseline

## Links

- [Percy Dashboard](https://percy.io/projects/meme-maker)
- [Cypress Documentation](https://docs.cypress.io/)
- [Percy/Cypress Integration](https://docs.percy.io/docs/cypress) 