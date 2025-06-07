#!/bin/bash

echo "🔍 Black Formatting Verification Script"
echo "======================================="

cd backend || exit 1

echo "📋 Checking Black version:"
python -m black --version

echo ""
echo "🎯 Checking Black configuration:"
echo "Target version: py312 (from pyproject.toml)"
echo "Line length: 88 (from pyproject.toml)"

echo ""
echo "🧪 Running Black check with CI-matching configuration:"
python -m black --check . --target-version py312

exit_code=$?

if [ $exit_code -eq 0 ]; then
    echo ""
    echo "✅ All files pass Black formatting checks!"
    echo "🚀 CI should now pass the backend lint stage."
else
    echo ""
    echo "❌ Black formatting issues found."
    echo "🔧 Run: python -m black . --target-version py312"
fi

exit $exit_code 