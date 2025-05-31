#!/usr/bin/env node

/**
 * Bundle Audit Script for Meme Maker Frontend
 * 
 * Analyzes Next.js build output for performance budget compliance:
 * - Total bundle size ≤ 250 kB gzip
 * - Individual chunks ≤ 100 kB gzip
 * - Critical path (first screen) ≤ 180 kB gzip
 * 
 * Usage: node scripts/bundle-audit.js [--enforce] [--verbose]
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');
const zlib = require('zlib');

// Performance budget thresholds
const BUDGETS = {
  TOTAL_GZIP_KB: 250,
  CHUNK_GZIP_KB: 100,
  CRITICAL_GZIP_KB: 180,
  SINGLE_MODULE_KB: 10,
};

class BundleAuditor {
  constructor(options = {}) {
    this.enforce = options.enforce || false;
    this.verbose = options.verbose || false;
    this.frontendDir = path.join(__dirname, '../frontend');
    this.buildDir = path.join(this.frontendDir, 'out');
    this.reportPath = path.join(this.frontendDir, 'bundle-report.json');
    this.results = {
      chunks: [],
      violations: [],
      summary: {},
      timestamp: new Date().toISOString(),
    };
  }

  async run() {
    console.log('🔍 Starting Bundle Audit...\n');

    try {
      await this.ensureBuildExists();
      await this.analyzeChunks();
      await this.checkPerformanceBudgets();
      await this.generateReport();
      await this.printSummary();

      if (this.enforce && this.results.violations.length > 0) {
        console.error('\n❌ Bundle audit failed! Performance budget violations detected.');
        process.exit(1);
      }

      console.log('\n✅ Bundle audit completed successfully!');
    } catch (error) {
      console.error('❌ Bundle audit failed:', error.message);
      process.exit(1);
    }
  }

  async ensureBuildExists() {
    if (!fs.existsSync(this.buildDir)) {
      console.log('📦 Build directory not found. Running build...');
      execSync('npm run build', { 
        cwd: this.frontendDir, 
        stdio: 'inherit' 
      });
    }
  }

  async analyzeChunks() {
    console.log('📊 Analyzing JavaScript chunks...');
    
    const staticDir = path.join(this.buildDir, '_next/static');
    const chunksDir = path.join(staticDir, 'chunks');
    
    if (!fs.existsSync(chunksDir)) {
      throw new Error('Chunks directory not found. Ensure build completed successfully.');
    }

    // Find all JS files recursively
    const jsFiles = this.findJSFiles(chunksDir);
    
    for (const filePath of jsFiles) {
      const chunk = await this.analyzeFile(filePath);
      this.results.chunks.push(chunk);
    }

    // Sort chunks by gzip size (largest first)
    this.results.chunks.sort((a, b) => b.gzipSize - a.gzipSize);
  }

  findJSFiles(dir, files = []) {
    const entries = fs.readdirSync(dir, { withFileTypes: true });
    
    for (const entry of entries) {
      const fullPath = path.join(dir, entry.name);
      if (entry.isDirectory()) {
        this.findJSFiles(fullPath, files);
      } else if (entry.name.endsWith('.js')) {
        files.push(fullPath);
      }
    }
    
    return files;
  }

  async analyzeFile(filePath) {
    const content = fs.readFileSync(filePath);
    const gzipContent = zlib.gzipSync(content);
    
    const relativePath = path.relative(this.buildDir, filePath);
    const fileName = path.basename(filePath);
    
    // Determine chunk type
    const chunkType = this.categorizeChunk(fileName);
    
    return {
      name: fileName,
      path: relativePath,
      type: chunkType,
      rawSize: content.length,
      gzipSize: gzipContent.length,
      rawSizeKB: Math.round(content.length / 1024 * 100) / 100,
      gzipSizeKB: Math.round(gzipContent.length / 1024 * 100) / 100,
    };
  }

  categorizeChunk(fileName) {
    if (fileName.includes('main')) return 'main';
    if (fileName.includes('framework')) return 'framework';
    if (fileName.includes('polyfill')) return 'polyfill';
    if (fileName.includes('webpack')) return 'runtime';
    if (fileName.startsWith('reactPlayer')) return 'lazy-media';
    if (/^\d+[-.]/.test(fileName)) return 'vendor';
    return 'app';
  }

  async checkPerformanceBudgets() {
    console.log('⚖️  Checking performance budgets...');

    // Calculate totals
    const totalGzipKB = this.results.chunks.reduce((sum, chunk) => sum + chunk.gzipSizeKB, 0);
    const criticalChunks = this.results.chunks.filter(chunk => 
      ['main', 'framework', 'runtime'].includes(chunk.type)
    );
    const criticalGzipKB = criticalChunks.reduce((sum, chunk) => sum + chunk.gzipSizeKB, 0);

    this.results.summary = {
      totalChunks: this.results.chunks.length,
      totalGzipKB: Math.round(totalGzipKB * 100) / 100,
      criticalGzipKB: Math.round(criticalGzipKB * 100) / 100,
      lazyChunks: this.results.chunks.filter(chunk => chunk.type === 'lazy-media').length,
    };

    // Check budget violations
    if (totalGzipKB > BUDGETS.TOTAL_GZIP_KB) {
      this.results.violations.push({
        type: 'TOTAL_BUDGET_EXCEEDED',
        current: totalGzipKB,
        budget: BUDGETS.TOTAL_GZIP_KB,
        message: `Total bundle size ${totalGzipKB} kB exceeds budget of ${BUDGETS.TOTAL_GZIP_KB} kB`,
      });
    }

    if (criticalGzipKB > BUDGETS.CRITICAL_GZIP_KB) {
      this.results.violations.push({
        type: 'CRITICAL_BUDGET_EXCEEDED',
        current: criticalGzipKB,
        budget: BUDGETS.CRITICAL_GZIP_KB,
        message: `Critical path size ${criticalGzipKB} kB exceeds budget of ${BUDGETS.CRITICAL_GZIP_KB} kB`,
      });
    }

    // Check individual chunk sizes
    for (const chunk of this.results.chunks) {
      if (chunk.gzipSizeKB > BUDGETS.CHUNK_GZIP_KB) {
        this.results.violations.push({
          type: 'CHUNK_BUDGET_EXCEEDED',
          chunk: chunk.name,
          current: chunk.gzipSizeKB,
          budget: BUDGETS.CHUNK_GZIP_KB,
          message: `Chunk ${chunk.name} (${chunk.gzipSizeKB} kB) exceeds budget of ${BUDGETS.CHUNK_GZIP_KB} kB`,
        });
      }
    }
  }

  async generateReport() {
    console.log('📄 Generating detailed report...');
    
    const report = {
      ...this.results,
      budgets: BUDGETS,
      recommendations: this.generateRecommendations(),
    };

    fs.writeFileSync(this.reportPath, JSON.stringify(report, null, 2));
    console.log(`📊 Report saved to: ${this.reportPath}`);
  }

  generateRecommendations() {
    const recommendations = [];

    // Large chunks
    const largeChunks = this.results.chunks.filter(chunk => chunk.gzipSizeKB > 50);
    if (largeChunks.length > 0) {
      recommendations.push({
        type: 'LARGE_CHUNKS',
        description: 'Consider code splitting or tree shaking for large chunks',
        chunks: largeChunks.map(c => `${c.name} (${c.gzipSizeKB} kB)`),
      });
    }

    // React Player optimization
    const reactPlayerChunks = this.results.chunks.filter(chunk => 
      chunk.name.startsWith('reactPlayer')
    );
    if (reactPlayerChunks.length > 5) {
      recommendations.push({
        type: 'REACT_PLAYER_OPTIMIZATION',
        description: 'Many React Player modules detected. Consider lazy loading only needed players',
        count: reactPlayerChunks.length,
      });
    }

    // Framework size
    const frameworkChunk = this.results.chunks.find(chunk => chunk.type === 'framework');
    if (frameworkChunk && frameworkChunk.gzipSizeKB > 150) {
      recommendations.push({
        type: 'FRAMEWORK_SIZE',
        description: 'Framework bundle is large. Consider upgrading to newer React version or tree shaking',
        size: frameworkChunk.gzipSizeKB,
      });
    }

    return recommendations;
  }

  async printSummary() {
    const { summary, violations } = this.results;
    
    console.log('\n📋 Bundle Analysis Summary');
    console.log('═'.repeat(50));
    console.log(`Total chunks: ${summary.totalChunks}`);
    console.log(`Total bundle size: ${summary.totalGzipKB} kB gzip (budget: ${BUDGETS.TOTAL_GZIP_KB} kB)`);
    console.log(`Critical path size: ${summary.criticalGzipKB} kB gzip (budget: ${BUDGETS.CRITICAL_GZIP_KB} kB)`);
    console.log(`Lazy-loaded chunks: ${summary.lazyChunks}`);

    if (this.verbose) {
      console.log('\n📦 Largest Chunks (Top 10)');
      console.log('─'.repeat(50));
      this.results.chunks.slice(0, 10).forEach(chunk => {
        console.log(`${chunk.name.padEnd(35)} ${chunk.gzipSizeKB.toString().padStart(8)} kB (${chunk.type})`);
      });
    }

    if (violations.length > 0) {
      console.log('\n⚠️  Budget Violations');
      console.log('─'.repeat(50));
      violations.forEach(violation => {
        console.log(`❌ ${violation.message}`);
      });
    } else {
      console.log('\n✅ All performance budgets met!');
    }
  }
}

// CLI handling
const args = process.argv.slice(2);
const options = {
  enforce: args.includes('--enforce'),
  verbose: args.includes('--verbose') || args.includes('-v'),
};

if (args.includes('--help') || args.includes('-h')) {
  console.log(`
Bundle Audit Tool for Meme Maker

Usage: node scripts/bundle-audit.js [options]

Options:
  --enforce    Exit with error code if budget violations found
  --verbose    Show detailed chunk breakdown
  --help       Show this help message

Performance Budgets:
  Total bundle: ≤ ${BUDGETS.TOTAL_GZIP_KB} kB gzip
  Single chunk: ≤ ${BUDGETS.CHUNK_GZIP_KB} kB gzip  
  Critical path: ≤ ${BUDGETS.CRITICAL_GZIP_KB} kB gzip
`);
  process.exit(0);
}

// Run the auditor
const auditor = new BundleAuditor(options);
auditor.run().catch(console.error); 