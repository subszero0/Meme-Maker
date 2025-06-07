#!/bin/bash

echo "🔬 Prettier Formatting Diagnostic"
echo "================================="

# Check if we're in the frontend directory
cd frontend 2>/dev/null || echo "Not in frontend directory, checking from root..."

# Test 1: Check Prettier configuration
echo "🧪 Test 1: Prettier Configuration"
echo "📋 Prettier config files:"
find . -name ".prettierrc*" -o -name "prettier.config.*" 2>/dev/null || echo "❌ No Prettier config found"

echo ""
echo "📄 Package.json prettier script:"
grep -A 2 -B 2 "prettier" package.json 2>/dev/null || echo "❌ No prettier script in package.json"

# Test 2: Check specific formatting issues
echo ""
echo "🧪 Test 2: Specific Formatting Issues"
echo "🔍 Running Prettier check to see exact issues..."

# Check which files have issues
npx prettier --check cypress/e2e/smoke.cy.ts src/app/layout.tsx src/app/page.tsx src/app/trim/page.tsx src/app/trim/TrimPageContent.tsx src/components/TrimPanel.tsx src/components/URLInputPanel.tsx src/lib/api.ts 2>/dev/null || echo "❌ Prettier check failed"

# Test 3: Show sample of formatting differences
echo ""
echo "🧪 Test 3: Sample Formatting Diff"
echo "📝 Showing what Prettier would change in TrimPageContent.tsx:"
npx prettier --check src/app/trim/TrimPageContent.tsx --write --dry-run 2>/dev/null || echo "❌ Could not generate diff"

# Test 4: Check line endings
echo ""
echo "🧪 Test 4: Line Ending Analysis"
echo "📏 Checking line endings in problematic files:"
file cypress/e2e/smoke.cy.ts src/app/trim/TrimPageContent.tsx 2>/dev/null || echo "❌ Could not check file types"

echo ""
echo "✅ Diagnostic complete! Use this info to determine fix approach." 