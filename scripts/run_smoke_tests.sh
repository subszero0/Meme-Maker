#!/usr/bin/env bash

# End-to-End Smoke Test Runner for Meme Maker
# 
# This script runs the complete E2E test suite to verify:
# - API endpoint availability
# - Metadata fetching
# - Job creation and processing
# - File download
#
# Usage:
#   ./scripts/run_smoke_tests.sh [options]
#
# Environment Variables:
#   BASE_URL          API base URL (default: http://localhost:8000)
#   TEST_VIDEO_URL    Test video URL (default: yt-dlp test video)
#   PYTEST_ARGS       Additional pytest arguments

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default configuration
DEFAULT_BASE_URL="http://localhost:8000"
DEFAULT_TEST_VIDEO_URL="https://www.youtube.com/watch?v=BaW_jenozKc"

# Configuration from environment or defaults
export BASE_URL=${BASE_URL:-$DEFAULT_BASE_URL}
export TEST_VIDEO_URL=${TEST_VIDEO_URL:-$DEFAULT_TEST_VIDEO_URL}

# Script directory for relative paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BACKEND_DIR="$PROJECT_ROOT/backend"

# Help function
show_help() {
    cat << EOF
Meme Maker E2E Smoke Test Runner

USAGE:
    $0 [OPTIONS]

OPTIONS:
    -h, --help              Show this help message
    -u, --url URL           Set API base URL (default: $DEFAULT_BASE_URL)
    -v, --video URL         Set test video URL (default: $DEFAULT_TEST_VIDEO_URL)
    -q, --quick             Run only quick tests (skip full E2E flow)
    -w, --wait-time SEC     Max wait time for job completion (default: 60)
    --verbose               Enable verbose pytest output
    --no-color              Disable colored output

ENVIRONMENT VARIABLES:
    BASE_URL               API base URL
    TEST_VIDEO_URL         Test video URL  
    PYTEST_ARGS            Additional pytest arguments

EXAMPLES:
    # Run tests against local development server
    $0

    # Run tests against production server
    $0 --url https://api.mememaker.com

    # Run only quick tests (no full E2E)
    $0 --quick

    # Run with custom video and verbose output
    $0 --video "https://www.youtube.com/watch?v=dQw4w9WgXcQ" --verbose

EOF
}

# Parse command line arguments
QUICK_MODE=false
VERBOSE_MODE=false
USE_COLOR=true

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -u|--url)
            export BASE_URL="$2"
            shift 2
            ;;
        -v|--video)
            export TEST_VIDEO_URL="$2"
            shift 2
            ;;
        -q|--quick)
            QUICK_MODE=true
            shift
            ;;
        -w|--wait-time)
            export MAX_WAIT_TIMEOUT_SECONDS="$2"
            shift 2
            ;;
        --verbose)
            VERBOSE_MODE=true
            shift
            ;;
        --no-color)
            USE_COLOR=false
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Disable colors if requested
if [[ "$USE_COLOR" == "false" ]]; then
    RED=""
    GREEN=""
    YELLOW=""
    BLUE=""
    NC=""
fi

# Logging functions
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if we're in the correct directory
check_environment() {
    log_info "Checking environment..."
    
    # Check if we're in the right project
    if [[ ! -f "$PROJECT_ROOT/prd.md" ]] || [[ ! -d "$BACKEND_DIR" ]]; then
        log_error "This script must be run from the Meme Maker project root"
        log_error "Current directory: $(pwd)"
        log_error "Expected backend directory: $BACKEND_DIR"
        exit 1
    fi
    
    # Check if backend directory exists
    if [[ ! -d "$BACKEND_DIR" ]]; then
        log_error "Backend directory not found: $BACKEND_DIR"
        exit 1
    fi
    
    # Check if test file exists
    if [[ ! -f "$BACKEND_DIR/tests/test_e2e_smoke.py" ]]; then
        log_error "E2E test file not found: $BACKEND_DIR/tests/test_e2e_smoke.py"
        exit 1
    fi
    
    log_success "Environment check passed"
}

# Test API availability before running full tests
test_api_availability() {
    log_info "Testing API availability at $BASE_URL..."
    
    # Try to reach health endpoint with timeout
    if curl --fail --silent --connect-timeout 10 --max-time 30 "$BASE_URL/health" > /dev/null 2>&1; then
        log_success "API is reachable at $BASE_URL"
        return 0
    else
        log_warning "API not reachable at $BASE_URL"
        log_warning "This might be expected if the server isn't running yet"
        return 1
    fi
}

# Build pytest command with appropriate arguments
build_pytest_command() {
    local pytest_cmd="python -m pytest"
    local test_file="tests/test_e2e_smoke.py"
    
    # Add verbosity
    if [[ "$VERBOSE_MODE" == "true" ]]; then
        pytest_cmd="$pytest_cmd -v -s"
    else
        pytest_cmd="$pytest_cmd -v"
    fi
    
    # Add test selection for quick mode
    if [[ "$QUICK_MODE" == "true" ]]; then
        pytest_cmd="$pytest_cmd -k 'not test_complete_user_flow'"
        log_info "Running in quick mode (skipping full E2E flow)"
    fi
    
    # Add any additional pytest arguments from environment
    if [[ -n "$PYTEST_ARGS" ]]; then
        pytest_cmd="$pytest_cmd $PYTEST_ARGS"
    fi
    
    # Add the test file
    pytest_cmd="$pytest_cmd $test_file"
    
    echo "$pytest_cmd"
}

# Main execution
main() {
    echo -e "${BLUE}🧪 Meme Maker E2E Smoke Tests${NC}"
    echo "=================================="
    echo ""
    
    # Show configuration
    log_info "Configuration:"
    echo "  📍 API Base URL: $BASE_URL"
    echo "  🎬 Test Video: $TEST_VIDEO_URL"
    echo "  📁 Backend Dir: $BACKEND_DIR"
    echo "  ⚡ Quick Mode: $QUICK_MODE"
    echo ""
    
    # Environment checks
    check_environment
    
    # Test API availability (non-blocking)
    test_api_availability || true
    
    echo ""
    log_info "Starting smoke tests..."
    echo ""
    
    # Change to backend directory for pytest
    cd "$BACKEND_DIR"
    
    # Build and execute pytest command
    pytest_cmd=$(build_pytest_command)
    log_info "Running: $pytest_cmd"
    echo ""
    
    # Execute tests
    if eval "$pytest_cmd"; then
        echo ""
        log_success "🎉 All smoke tests passed!"
        echo ""
        log_info "The Meme Maker API is working correctly:"
        echo "  ✅ API endpoints are accessible"
        echo "  ✅ Metadata fetching works"
        echo "  ✅ Job creation and validation work"
        if [[ "$QUICK_MODE" == "false" ]]; then
            echo "  ✅ Complete E2E flow works (metadata → job → download)"
        fi
        echo ""
        return 0
    else
        echo ""
        log_error "💥 Some smoke tests failed!"
        echo ""
        log_warning "Troubleshooting tips:"
        echo "  🔍 Check if the API server is running: curl $BASE_URL/health"
        echo "  🔍 Check if Redis and workers are running"
        echo "  🔍 Check server logs for errors"
        echo "  🔍 Verify the test video URL is accessible"
        echo ""
        return 1
    fi
}

# Execute main function
main "$@" 