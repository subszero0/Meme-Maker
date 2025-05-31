#!/usr/bin/env node

/**
 * Color Contrast Audit Script for Meme Maker
 * 
 * Performs automated accessibility testing focused on color contrast
 * using axe-core to identify WCAG AA violations (3:1 for UI, 4.5:1 for text).
 * 
 * Usage:
 *   node scripts/contrast-audit.js [--format=json|markdown] [--output=file.json]
 */

const { AxePuppeteer } = require('@axe-core/puppeteer');
const puppeteer = require('puppeteer');
const fs = require('fs').promises;
const path = require('path');

// Configuration
const BASE_URL = process.env.BASE_URL || 'http://localhost:3001';
const AUDIT_CONFIG = {
  // Focus only on contrast-related rules
  rules: {
    'color-contrast': { enabled: true },
    'color-contrast-enhanced': { enabled: true },
  },
  // Remove non-contrast rules to focus audit
  disableOtherRules: true,
  tags: ['wcag2a', 'wcag2aa', 'wcag21aa'],
};

// Test scenarios covering all core UI states
const TEST_SCENARIOS = [
  {
    name: 'URL Input Panel - Initial State',
    path: '/',
    description: 'Landing page with URL input form',
    setup: null,
  },
  {
    name: 'URL Input Panel - Error State',
    path: '/',
    description: 'URL input with validation error displayed',
    setup: async (page) => {
      await page.type('[data-cy="url-input"]', 'invalid-url');
      await page.click('[data-cy="start-button"]');
      await new Promise(resolve => setTimeout(resolve, 500)); // Wait for validation
    },
  },
  {
    name: 'URL Input Panel - Loading State',
    path: '/',
    description: 'URL input in loading/disabled state',
    setup: async (page) => {
      // Simulate loading by finding button and checking if we can make it disabled
      await page.type('[data-cy="url-input"]', 'https://www.youtube.com/watch?v=dQw4w9WgXcQ');
      // Note: Would need backend running to test actual loading state
    },
  },
  {
    name: 'Notification - Success Toast',
    path: '/',
    description: 'Success notification toast',
    setup: async (page) => {
      // Inject a success notification
      await page.evaluate(() => {
        const div = document.createElement('div');
        div.innerHTML = `
          <div class="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 text-green-800 dark:text-green-300 p-4 rounded-xl">
            <div class="flex items-start">
              <svg class="w-5 h-5 text-green-600 dark:text-green-400 mr-3" fill="currentColor">
                <path d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"/>
              </svg>
              <div>
                <h4 class="font-medium">Success</h4>
                <p class="text-sm">Operation completed successfully</p>
              </div>
            </div>
          </div>
        `;
        document.body.appendChild(div);
      });
    },
  },
  {
    name: 'Notification - Error Toast',
    path: '/',
    description: 'Error notification toast',
    setup: async (page) => {
      await page.evaluate(() => {
        const div = document.createElement('div');
        div.innerHTML = `
          <div class="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-800 dark:text-red-300 p-4 rounded-xl">
            <div class="flex items-start">
              <svg class="w-5 h-5 text-red-600 dark:text-red-400 mr-3" fill="currentColor">
                <path d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"/>
              </svg>
              <div>
                <h4 class="font-medium">Error</h4>
                <p class="text-sm">Something went wrong</p>
              </div>
            </div>
          </div>
        `;
        document.body.appendChild(div);
      });
    },
  },
  {
    name: 'Notification - Warning Banner',
    path: '/',
    description: 'Warning notification banner',
    setup: async (page) => {
      await page.evaluate(() => {
        const div = document.createElement('div');
        div.innerHTML = `
          <div class="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 text-yellow-800 dark:text-yellow-300 p-4 rounded-xl mb-4">
            <div class="flex items-start">
              <svg class="w-5 h-5 text-yellow-600 dark:text-yellow-400 mr-3" fill="currentColor">
                <path d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z"/>
              </svg>
              <div>
                <h4 class="font-medium">Warning</h4>
                <p class="text-sm">Please review your input</p>
              </div>
            </div>
          </div>
        `;
        document.body.appendChild(div);
      });
    },
  },
  {
    name: 'Modal Placeholder',
    path: '/',
    description: 'Modal dialog with download link',
    setup: async (page) => {
      await page.evaluate(() => {
        const div = document.createElement('div');
        div.innerHTML = `
          <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
            <div class="bg-white dark:bg-gray-800 rounded-xl p-6 max-w-md w-full border dark:border-gray-700">
              <h3 class="text-lg font-semibold mb-4 text-gray-900 dark:text-gray-100">Download Ready</h3>
              <p class="text-gray-600 dark:text-gray-400 mb-4">Your clip is ready for download</p>
              <div class="flex gap-3">
                <button class="flex-1 bg-indigo-600 text-white py-2 px-4 rounded-md hover:bg-indigo-700 focus:ring-2 focus:ring-indigo-500">
                  Download
                </button>
                <button class="bg-gray-200 dark:bg-gray-600 text-gray-800 dark:text-gray-200 py-2 px-4 rounded-md hover:bg-gray-300 dark:hover:bg-gray-500">
                  Cancel
                </button>
              </div>
            </div>
          </div>
        `;
        document.body.appendChild(div);
      });
    },
  },
];

/**
 * Parse command line arguments
 */
function parseArgs() {
  const args = process.argv.slice(2);
  const config = {
    format: 'markdown',
    output: null,
    verbose: false,
  };

  args.forEach(arg => {
    if (arg.startsWith('--format=')) {
      config.format = arg.split('=')[1];
    } else if (arg.startsWith('--output=')) {
      config.output = arg.split('=')[1];
    } else if (arg === '--verbose' || arg === '-v') {
      config.verbose = true;
    }
  });

  return config;
}

/**
 * Run axe audit on a specific page/scenario
 */
async function runAuditForScenario(page, scenario) {
  console.log(`🔍 Auditing: ${scenario.name}`);
  
  try {
    // Navigate to the page
    await page.goto(`${BASE_URL}${scenario.path}`, { 
      waitUntil: 'domcontentloaded',
      timeout: 10000,
    });

    // Wait for page to be ready
    await new Promise(resolve => setTimeout(resolve, 1000));

    // Run scenario-specific setup
    if (scenario.setup) {
      await scenario.setup(page);
      await new Promise(resolve => setTimeout(resolve, 500)); // Let DOM settle
    }

    // Run axe audit
    const results = await new AxePuppeteer(page)
      .configure({
        rules: [
          { id: 'color-contrast', enabled: true },
          { id: 'color-contrast-enhanced', enabled: true },
        ]
      })
      .analyze();

    // Filter for contrast violations only
    const contrastViolations = results.violations.filter(violation => 
      violation.id === 'color-contrast' || violation.id === 'color-contrast-enhanced'
    );

    return {
      scenario: scenario.name,
      description: scenario.description,
      url: `${BASE_URL}${scenario.path}`,
      violations: contrastViolations,
      timestamp: new Date().toISOString(),
    };

  } catch (error) {
    console.error(`❌ Error auditing ${scenario.name}:`, error.message);
    return {
      scenario: scenario.name,
      description: scenario.description,
      url: `${BASE_URL}${scenario.path}`,
      error: error.message,
      violations: [],
      timestamp: new Date().toISOString(),
    };
  }
}

/**
 * Test both light and dark modes
 */
async function runFullAudit(page) {
  const results = [];

  console.log('\n🌞 Testing Light Mode');
  console.log('=' .repeat(50));

  // Test light mode
  await page.emulateMediaFeatures([{ name: 'prefers-color-scheme', value: 'light' }]);
  
  for (const scenario of TEST_SCENARIOS) {
    const result = await runAuditForScenario(page, scenario);
    result.colorScheme = 'light';
    results.push(result);
  }

  console.log('\n🌙 Testing Dark Mode');
  console.log('=' .repeat(50));

  // Test dark mode
  await page.emulateMediaFeatures([{ name: 'prefers-color-scheme', value: 'dark' }]);
  
  for (const scenario of TEST_SCENARIOS) {
    const result = await runAuditForScenario(page, scenario);
    result.colorScheme = 'dark';
    results.push(result);
  }

  return results;
}

/**
 * Generate detailed contrast report
 */
function generateReport(results, format = 'markdown') {
  const totalScenarios = results.length;
  const scenariosWithViolations = results.filter(r => r.violations && r.violations.length > 0).length;
  const totalViolations = results.reduce((sum, r) => sum + (r.violations ? r.violations.length : 0), 0);

  if (format === 'json') {
    return JSON.stringify({
      summary: {
        totalScenarios,
        scenariosWithViolations,
        totalViolations,
        auditDate: new Date().toISOString(),
      },
      results,
    }, null, 2);
  }

  // Markdown format
  let report = `# Color Contrast Audit Report

**Audit Date:** ${new Date().toLocaleDateString()}  
**Total Scenarios:** ${totalScenarios}  
**Scenarios with Violations:** ${scenariosWithViolations}  
**Total Violations:** ${totalViolations}

## Summary

`;

  if (totalViolations === 0) {
    report += `✅ **All scenarios passed!** No contrast violations found.\n\n`;
  } else {
    report += `❌ **${totalViolations} contrast violation(s) found** across ${scenariosWithViolations} scenario(s).\n\n`;
  }

  report += `## Detailed Results\n\n`;

  results.forEach(result => {
    const status = result.violations && result.violations.length > 0 ? '❌' : '✅';
    const violationCount = result.violations ? result.violations.length : 0;
    
    report += `### ${status} ${result.scenario} (${result.colorScheme})\n\n`;
    report += `- **Description:** ${result.description}\n`;
    report += `- **URL:** ${result.url}\n`;
    report += `- **Violations:** ${violationCount}\n\n`;

    if (result.error) {
      report += `⚠️ **Error:** ${result.error}\n\n`;
    }

    if (result.violations && result.violations.length > 0) {
      result.violations.forEach((violation, index) => {
        report += `#### Violation ${index + 1}: ${violation.id}\n\n`;
        report += `**Description:** ${violation.description}\n\n`;
        report += `**Impact:** ${violation.impact}\n\n`;
        report += `**Help:** ${violation.help}\n\n`;

        if (violation.nodes && violation.nodes.length > 0) {
          report += `**Affected Elements:**\n\n`;
          violation.nodes.forEach((node, nodeIndex) => {
            report += `${nodeIndex + 1}. **Selector:** \`${node.target.join(' ')}\`\n`;
            if (node.html) {
              report += `   **HTML:** \`${node.html.substring(0, 100)}${node.html.length > 100 ? '...' : ''}\`\n`;
            }
            if (node.any && node.any[0] && node.any[0].message) {
              report += `   **Issue:** ${node.any[0].message}\n`;
            }
            report += `\n`;
          });
        }

        report += `---\n\n`;
      });
    }
  });

  return report;
}

/**
 * Main audit function
 */
async function runContrastAudit() {
  const config = parseArgs();
  
  console.log('🧪 Meme Maker Color Contrast Audit');
  console.log('=' .repeat(50));
  console.log(`📍 Base URL: ${BASE_URL}`);
  console.log(`📊 Format: ${config.format}`);
  console.log(`📁 Output: ${config.output || 'stdout'}`);
  console.log('');

  let browser;
  
  try {
    // Launch browser
    browser = await puppeteer.launch({ 
      headless: 'new',
      args: ['--no-sandbox', '--disable-setuid-sandbox']
    });
    
    const page = await browser.newPage();
    
    // Set viewport for consistent testing
    await page.setViewport({ width: 1200, height: 800 });

    // Test if the application is running
    try {
      console.log(`🔍 Testing connection to ${BASE_URL}...`);
      await page.goto(BASE_URL, { timeout: 5000 });
      console.log('✅ Application is reachable\n');
    } catch (error) {
      console.error(`❌ Application is not reachable. Make sure the frontend is running on ${BASE_URL}`);
      console.error('Error details:', error.message);
      process.exit(1);
    }

    // Run full audit
    const results = await runFullAudit(page);

    // Generate report
    const report = generateReport(results, config.format);

    // Output results
    if (config.output) {
      await fs.writeFile(config.output, report, 'utf8');
      console.log(`\n📁 Report saved to: ${config.output}`);
    } else {
      console.log('\n' + report);
    }

    // Exit with appropriate code
    const hasViolations = results.some(r => r.violations && r.violations.length > 0);
    process.exit(hasViolations ? 1 : 0);

  } catch (error) {
    console.error('❌ Audit failed:', error);
    process.exit(1);
  } finally {
    if (browser) {
      await browser.close();
    }
  }
}

// Handle unhandled rejections
process.on('unhandledRejection', (reason, promise) => {
  console.error('Unhandled Rejection at:', promise, 'reason:', reason);
  process.exit(1);
});

// Run audit if called directly
if (require.main === module) {
  runContrastAudit();
}

module.exports = { runContrastAudit, generateReport }; 