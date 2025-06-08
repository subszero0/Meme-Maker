#!/bin/bash
# 🎯 Full Test Runner - All Tests
# Goal: Complete in < 3 minutes for comprehensive validation

set -e

echo "🎯 Starting full test suite..."
echo "⏱️  Expected runtime: < 3 minutes"
echo "📊 Test breakdown: Unit → Integration → E2E"
echo ""

# Start timing
start_time=$(date +%s)

# Stage 1: Unit Tests
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🧪 Stage 1: Unit Tests"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

stage1_start=$(date +%s)

# Backend Unit Tests
echo "🐍 Running backend unit tests..."
cd backend
python -m pytest tests/test_business_logic.py tests/test_simple.py -v --tb=short
echo ""

# Frontend Unit Tests  
echo "🟨 Running frontend unit tests..."
cd ../frontend
npm test -- --passWithNoTests --watchAll=false
echo ""

stage1_end=$(date +%s)
stage1_time=$((stage1_end - stage1_start))
echo "✅ Stage 1 completed in ${stage1_time}s"
echo ""

# Stage 2: Integration Tests
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔗 Stage 2: Integration Tests"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

stage2_start=$(date +%s)

echo "🔗 Running API contract tests..."
cd ../backend
python -m pytest tests/test_api_contracts.py tests/test_jobs.py -v --tb=short
echo ""

stage2_end=$(date +%s)
stage2_time=$((stage2_end - stage2_start))
echo "✅ Stage 2 completed in ${stage2_time}s"
echo ""

# Stage 3: E2E Tests (optional, commented out by default for speed)
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎯 Stage 3: E2E Tests"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

stage3_start=$(date +%s)

# Check if --with-e2e flag is passed
if [[ "$*" == *"--with-e2e"* ]]; then
    echo "🎯 Running critical E2E tests..."
    cd ../frontend
    
    # Build frontend for E2E
    echo "🏗️  Building frontend..."
    npm run build
    
    # Run E2E tests
    echo "🎯 Running Cypress E2E tests..."
    npx cypress run --spec 'cypress/e2e/smoke.cy.ts' --headless
else
    echo "⏭️  Skipping E2E tests (use --with-e2e to include)"
    echo "💡 E2E tests are run automatically in CI on main branch"
fi

stage3_end=$(date +%s)
stage3_time=$((stage3_end - stage3_start))
echo "✅ Stage 3 completed in ${stage3_time}s"
echo ""

# Calculate total runtime
end_time=$(date +%s)
total_runtime=$((end_time - start_time))

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎉 Full test suite completed successfully!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 Performance Summary:"
echo "   Stage 1 (Unit):        ${stage1_time}s"
echo "   Stage 2 (Integration): ${stage2_time}s"
echo "   Stage 3 (E2E):         ${stage3_time}s"
echo "   Total Runtime:         ${total_runtime}s"
echo ""

if [ $total_runtime -lt 180 ]; then
    echo "🎯 Target achieved: < 3 minutes ✅"
else
    echo "⚠️  Runtime exceeded 3 minute target"
fi

echo ""
echo "💡 Usage tips:"
echo "   ./scripts/test-quick.sh     # Unit tests only (< 1 min)"
echo "   ./scripts/test-full.sh      # Unit + Integration (< 3 min)"  
echo "   ./scripts/test-full.sh --with-e2e  # All tests including E2E" 