#!/bin/bash
# 🚀 Quick Test Runner - Unit Tests Only
# Goal: Complete in < 1 minute for fast developer feedback

set -e

echo "🚀 Starting quick test run (unit tests only)..."
echo "⏱️  Expected runtime: < 1 minute"
echo ""

# Start timing
start_time=$(date +%s)

# Backend Unit Tests
echo "🐍 Running backend unit tests..."
cd backend
python -m pytest tests/test_business_logic.py tests/test_simple.py -v --tb=short -q
echo "✅ Backend unit tests passed"
echo ""

# Frontend Unit Tests
echo "🟨 Running frontend unit tests..."
cd ../frontend
npm test -- --passWithNoTests --watchAll=false --silent
echo "✅ Frontend unit tests passed"
echo ""

# Calculate runtime
end_time=$(date +%s)
runtime=$((end_time - start_time))

echo "🎉 Quick tests completed successfully!"
echo "⏱️  Runtime: ${runtime} seconds"

if [ $runtime -lt 60 ]; then
    echo "🎯 Target achieved: < 1 minute ✅"
else
    echo "⚠️  Runtime exceeded 1 minute target"
fi 