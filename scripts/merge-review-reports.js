#!/usr/bin/env node

const fs = require('fs');
const path = require('path');

// Helper functions
const exists = (filePath) => fs.existsSync(filePath);
const readFile = (filePath) => exists(filePath) ? fs.readFileSync(filePath, 'utf8') : null;
const readJSON = (filePath) => {
  try {
    return exists(filePath) ? JSON.parse(fs.readFileSync(filePath, 'utf8')) : null;
  } catch (e) {
    return null;
  }
};

// Get git info
const getGitInfo = () => {
  try {
    const { execSync } = require('child_process');
    const sha = execSync('git rev-parse HEAD', { encoding: 'utf8' }).trim();
    const branch = execSync('git rev-parse --abbrev-ref HEAD', { encoding: 'utf8' }).trim();
    const date = new Date().toISOString();
    return { sha: sha.substring(0, 7), branch, date };
  } catch (e) {
    return { sha: 'unknown', branch: 'unknown', date: new Date().toISOString() };
  }
};

// Parse Lighthouse results
const parseLighthouse = () => {
  const lhDir = 'reports/lighthouse';
  if (!exists(lhDir)) return null;
  
  try {
    const files = fs.readdirSync(lhDir).filter(f => f.endsWith('.json'));
    if (files.length === 0) return null;
    
    const results = [];
    for (const file of files) {
      const data = readJSON(path.join(lhDir, file));
      if (data && data.lhr) {
        const { categories, finalUrl } = data.lhr;
        results.push({
          url: finalUrl,
          performance: Math.round(categories.performance?.score * 100 || 0),
          accessibility: Math.round(categories.accessibility?.score * 100 || 0),
          bestPractices: Math.round(categories['best-practices']?.score * 100 || 0),
          seo: Math.round(categories.seo?.score * 100 || 0),
        });
      }
    }
    return results;
  } catch (e) {
    return null;
  }
};

// Parse axe results
const parseAxe = () => {
  const axeData = readJSON('reports/axe.json');
  if (!axeData || !Array.isArray(axeData)) return null;
  
  const violations = axeData.reduce((acc, result) => {
    if (result.violations) {
      acc.push(...result.violations);
    }
    return acc;
  }, []);
  
  const summary = {
    total: violations.length,
    serious: violations.filter(v => v.impact === 'serious').length,
    critical: violations.filter(v => v.impact === 'critical').length,
    moderate: violations.filter(v => v.impact === 'moderate').length,
    minor: violations.filter(v => v.impact === 'minor').length,
  };
  
  return { summary, violations };
};

// Parse bundle audit
const parseBundle = () => {
  const bundleLog = readFile('reports/bundle-audit.log');
  if (!bundleLog) return null;
  
  const lines = bundleLog.split('\n');
  const totalSizeMatch = bundleLog.match(/Total bundle size: ([\d.]+)\s*KB/);
  const gzipSizeMatch = bundleLog.match(/Total gzipped size: ([\d.]+)\s*KB/);
  const largestChunkMatch = bundleLog.match(/Largest chunk: ([\d.]+)\s*KB/);
  
  return {
    totalSize: totalSizeMatch ? parseFloat(totalSizeMatch[1]) : null,
    gzipSize: gzipSizeMatch ? parseFloat(gzipSizeMatch[1]) : null,
    largestChunk: largestChunkMatch ? parseFloat(largestChunkMatch[1]) : null,
    passed: bundleLog.includes('✅') || bundleLog.includes('PASS'),
  };
};

// Parse API performance
const parseApiPerformance = () => {
  const apiData = readJSON('reports/api-health.json');
  const perfLog = readFile('reports/api-performance.log');
  
  return {
    health: apiData,
    responseTime: perfLog ? parseFloat(perfLog.match(/time_total":\s*([\d.]+)/)?.[1]) : null,
  };
};

// Parse Cypress results
const parseCypress = () => {
  const cypressLog = readFile('reports/cypress-chrome.log');
  if (!cypressLog) return null;
  
  const passedMatch = cypressLog.match(/✓ (\d+) passing/);
  const failedMatch = cypressLog.match(/✗ (\d+) failing/);
  
  return {
    passed: passedMatch ? parseInt(passedMatch[1]) : 0,
    failed: failedMatch ? parseInt(failedMatch[1]) : 0,
    success: !cypressLog.includes('failing'),
  };
};

// Generate status emoji
const getStatus = (condition) => condition ? '🟢' : '🔴';
const getScoreStatus = (score, threshold) => score >= threshold ? '🟢' : '🔴';

// Main report generation
const generateReport = () => {
  const git = getGitInfo();
  const lighthouse = parseLighthouse();
  const axe = parseAxe();
  const bundle = parseBundle();
  const api = parseApiPerformance();
  const cypress = parseCypress();
  
  // Calculate overall pass/fail
  const checks = [
    lighthouse && lighthouse.every(r => r.performance >= 90 && r.accessibility >= 95 && r.bestPractices >= 90),
    axe && axe.summary.serious === 0 && axe.summary.critical === 0,
    bundle && bundle.gzipSize <= 250 && bundle.largestChunk <= 100,
    api && api.responseTime < 1.0,
    cypress && cypress.success,
  ];
  
  const allPassed = checks.every(check => check === true);
  
  return `# 🚀 Final Pre-Launch Review Report

**Generated:** ${git.date}  
**Git SHA:** \`${git.sha}\`  
**Branch:** \`${git.branch}\`

---

## 📊 Executive Summary

${allPassed ? '🟢 **GO FOR LAUNCH**' : '🔴 **NO-GO FOR LAUNCH**'}

${allPassed 
  ? 'All quality gates have been met. The application is ready for production deployment.'
  : 'One or more quality gates have failed. Review the detailed findings below before proceeding.'
}

---

## 🚀 Lighthouse Performance

${lighthouse ? lighthouse.map(result => `
### ${result.url}

| Metric | Score | Status | Target |
|--------|-------|--------|--------|
| Performance | ${result.performance}% | ${getScoreStatus(result.performance, 90)} | ≥ 90% |
| Accessibility | ${result.accessibility}% | ${getScoreStatus(result.accessibility, 95)} | ≥ 95% |
| Best Practices | ${result.bestPractices}% | ${getScoreStatus(result.bestPractices, 90)} | ≥ 90% |
| SEO | ${result.seo}% | ${getScoreStatus(result.seo, 90)} | ≥ 90% |
`).join('\n') : '❌ Lighthouse data not available'}

---

## ♿ Accessibility (WCAG 2.1 AA)

${axe ? `
| Severity | Count | Status |
|----------|-------|--------|
| Critical | ${axe.summary.critical} | ${getStatus(axe.summary.critical === 0)} |
| Serious | ${axe.summary.serious} | ${getStatus(axe.summary.serious === 0)} |
| Moderate | ${axe.summary.moderate} | ${getStatus(axe.summary.moderate === 0)} |
| Minor | ${axe.summary.minor} | ${getStatus(axe.summary.minor === 0)} |

**Total Violations:** ${axe.summary.total}

${axe.violations.length > 0 ? `
### ⚠️ Violations Found

${axe.violations.slice(0, 5).map(v => `
- **${v.impact?.toUpperCase()}**: ${v.description}
  - Rule: \`${v.id}\`
  - Nodes affected: ${v.nodes?.length || 0}
`).join('\n')}

${axe.violations.length > 5 ? `\n*... and ${axe.violations.length - 5} more violations*` : ''}
` : '✅ No accessibility violations found'}
` : '❌ Accessibility data not available'}

---

## 📦 Bundle Size Analysis

${bundle ? `
| Metric | Value | Status | Limit |
|--------|-------|--------|-------|
| Total Gzipped | ${bundle.gzipSize}KB | ${getStatus(bundle.gzipSize <= 250)} | ≤ 250KB |
| Largest Chunk | ${bundle.largestChunk}KB | ${getStatus(bundle.largestChunk <= 100)} | ≤ 100KB |
| Total Uncompressed | ${bundle.totalSize}KB | ℹ️ | - |

${bundle.passed ? '✅ Bundle size requirements met' : '❌ Bundle size requirements not met'}
` : '❌ Bundle data not available'}

---

## ⚡ API Performance

${api ? `
| Metric | Value | Status | Target |
|--------|-------|--------|--------|
| Health Check Response | ${api.responseTime ? `${api.responseTime}s` : 'N/A'} | ${getStatus(api.responseTime < 1.0)} | < 1.0s |
| API Status | ${api.health ? 'Healthy' : 'Unknown'} | ${getStatus(!!api.health)} | Healthy |
` : '❌ API performance data not available'}

---

## 🌐 Cross-Browser Compatibility

${cypress ? `
| Browser | Tests Passed | Tests Failed | Status |
|---------|-------------|--------------|--------|
| Chrome | ${cypress.passed} | ${cypress.failed} | ${getStatus(cypress.success)} |

${cypress.success ? '✅ All tests passed' : `❌ ${cypress.failed} test(s) failed`}
` : '❌ Cross-browser test data not available'}

---

## 🔍 Detailed Findings

### Security Headers
${exists('reports/security-headers.log') ? '✅ Security headers check completed' : '❌ Security headers check failed'}

### Performance Metrics
- Core Web Vitals: ${lighthouse ? '✅ Measured' : '❌ Not measured'}
- Bundle optimization: ${bundle ? '✅ Analyzed' : '❌ Not analyzed'}
- API response times: ${api ? '✅ Measured' : '❌ Not measured'}

---

## 🎯 Action Items

${!allPassed ? `
### 🔴 Critical Issues (Must Fix)

${checks.map((passed, index) => {
  const issues = [
    'Lighthouse scores below target (Performance ≥90%, Accessibility ≥95%, Best Practices ≥90%)',
    'Critical or serious accessibility violations found',
    'Bundle size exceeds limits (≤250KB gzipped, ≤100KB per chunk)',
    'API response time exceeds 1 second',
    'Cross-browser tests failing'
  ];
  return !passed ? `- [ ] ${issues[index]}` : null;
}).filter(Boolean).join('\n')}

### 🟡 Recommendations

- [ ] Review bundle size optimization opportunities
- [ ] Verify manual accessibility testing with screen readers
- [ ] Test on additional browsers and devices
- [ ] Monitor performance in production
` : `
### 🟢 All Quality Gates Passed!

The application meets all pre-launch criteria:
- ✅ Performance scores meet targets
- ✅ No critical accessibility issues
- ✅ Bundle size within limits
- ✅ API performance acceptable
- ✅ Cross-browser tests passing
`}

---

## 📋 Sign-off Checklist

- [ ] **Engineering Lead**: Code quality and performance review
- [ ] **QA Lead**: Testing coverage and bug verification  
- [ ] **Accessibility Lead**: WCAG compliance verification
- [ ] **Product Manager**: Feature completeness and UX review
- [ ] **DevOps Lead**: Infrastructure and monitoring readiness

---

## 🚦 Final Decision

${allPassed ? '🟢 **GO FOR LAUNCH**' : '🔴 **NO-GO FOR LAUNCH**'}

**Stakeholder Sign-off Required**: Please review this report and provide sign-off in the #meme-maker-launch Slack channel.

---

*Report generated by Final Review Audit v1.0*  
*Commit: ${git.sha} | Branch: ${git.branch}*
`;
};

// Output the report
console.log(generateReport()); 