#!/bin/sh

# Line Counting Script for Meme Maker
# 
# Counts lines of code by component directory and provides overall statistics.
# Uses cloc if available, otherwise falls back to wc -l with file filtering.
#
# Usage: ./scripts/line_counts.sh [--help]

set -e

# Colors for output (if supported)
if [ -t 1 ]; then
    RED='\033[0;31m'
    GREEN='\033[0;32m'
    YELLOW='\033[1;33m'
    BLUE='\033[0;34m'
    PURPLE='\033[0;35m'
    CYAN='\033[0;36m'
    NC='\033[0m'
else
    RED=''
    GREEN=''
    YELLOW=''
    BLUE=''
    PURPLE=''
    CYAN=''
    NC=''
fi

# Configuration
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Component directories to analyze
DIRS="backend frontend worker infra scripts .github docs"

# Show help
if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    cat << EOF
Meme Maker Line Counter

USAGE:
    $0 [OPTIONS]

OPTIONS:
    -h, --help          Show this help message

DESCRIPTION:
    Counts lines of code by component directory and provides overall statistics.
    Uses cloc if available, otherwise falls back to wc -l with file filtering.

COMPONENTS ANALYZED:
    - backend
    - frontend
    - worker
    - infra
    - scripts
    - .github
    - docs

EOF
    exit 0
fi

# Logging functions
log_info() {
    printf "${BLUE}ℹ️  %s${NC}\n" "$1"
}

log_success() {
    printf "${GREEN}✅ %s${NC}\n" "$1"
}

log_warning() {
    printf "${YELLOW}⚠️  %s${NC}\n" "$1"
}

# Check if cloc is available
check_cloc() {
    command -v cloc >/dev/null 2>&1
}

# Count lines using cloc
count_with_cloc() {
    dir="$1"
    
    if [ ! -d "$dir" ]; then
        echo "0"
        return
    fi
    
    # Run cloc and extract total lines
    cloc --quiet --csv "$dir" 2>/dev/null | tail -n1 | cut -d',' -f5 || echo "0"
}

# Count lines using wc with find
count_with_wc() {
    dir="$1"
    
    if [ ! -d "$dir" ]; then
        echo "0"
        return
    fi
    
    # Find code files and count lines
    find "$dir" -type f \( \
        -name "*.py" -o \
        -name "*.js" -o \
        -name "*.jsx" -o \
        -name "*.ts" -o \
        -name "*.tsx" -o \
        -name "*.yaml" -o \
        -name "*.yml" -o \
        -name "*.json" -o \
        -name "*.sh" -o \
        -name "*.md" -o \
        -name "*.toml" -o \
        -name "*.ini" \) \
        ! -path "*/node_modules/*" \
        ! -path "*/__pycache__/*" \
        ! -path "*/.pytest_cache/*" \
        ! -path "*/out/*" \
        ! -path "*/dist/*" \
        ! -path "*/build/*" \
        ! -path "*/.next/*" \
        ! -path "*/.venv/*" \
        ! -path "*/venv/*" \
        ! -path "*/.git/*" \
        2>/dev/null | xargs wc -l 2>/dev/null | tail -n1 | awk '{print $1}' || echo "0"
}

# Format number with commas (basic version)
format_number() {
    num="$1"
    # Simple thousands separator (not perfect but works for most cases)
    printf "%s" "$num" | sed ':a;s/\B[0-9]\{3\}\>/,&/;ta'
}

# Main execution
main() {
    cd "$PROJECT_ROOT"
    
    printf "${PURPLE}📊 Meme Maker - Line Count Analysis${NC}\n"
    printf "==========================================\n"
    printf "\n"
    
    # Check which tool we're using
    if check_cloc; then
        use_cloc=true
        log_success "Using cloc for accurate code analysis"
    else
        use_cloc=false
        log_warning "cloc not available, using wc -l fallback"
        log_info "Install cloc for more accurate results: brew install cloc (macOS) or apt install cloc (Ubuntu)"
    fi
    
    printf "\n"
    printf "${BLUE}📁 Lines by Component:${NC}\n"
    printf "\n"
    
    total_lines=0
    
    # Analyze each component directory
    for dir in $DIRS; do
        if [ -d "$dir" ]; then
            if [ "$use_cloc" = "true" ]; then
                lines=$(count_with_cloc "$dir")
            else
                lines=$(count_with_wc "$dir")
            fi
            
            total_lines=$((total_lines + lines))
            formatted_lines=$(format_number "$lines")
            
            printf "%-12s %8s lines\n" "$dir" "$formatted_lines"
        else
            printf "%-12s %8s (not found)\n" "$dir" "0"
        fi
    done
    
    printf "\n"
    printf "${GREEN}📊 Summary:${NC}\n"
    
    formatted_total=$(format_number "$total_lines")
    printf "${GREEN}🎯 Total Lines (components): %s${NC}\n" "$formatted_total"
    
    # Overall project analysis
    printf "\n"
    printf "${BLUE}🌐 Overall Project Analysis:${NC}\n"
    printf "\n"
    
    if [ "$use_cloc" = "true" ]; then
        cloc . --quiet 2>/dev/null || {
            log_warning "cloc overall analysis failed, using fallback"
            overall_total=$(count_with_wc ".")
            formatted_total=$(format_number "$overall_total")
            printf "Total lines (all files): %s\n" "$formatted_total"
        }
    else
        overall_total=$(count_with_wc ".")
        formatted_total=$(format_number "$overall_total")
        printf "Total lines (filtered files): %s\n" "$formatted_total"
    fi
    
    # Additional statistics
    printf "\n"
    printf "${CYAN}📈 Additional Statistics:${NC}\n"
    
    # Count files
    file_count=$(find . -type f \( \
        -name "*.py" -o \
        -name "*.js" -o \
        -name "*.ts" -o \
        -name "*.tsx" -o \
        -name "*.md" \) \
        ! -path "*/node_modules/*" \
        ! -path "*/__pycache__/*" \
        ! -path "*/.pytest_cache/*" \
        ! -path "*/out/*" \
        ! -path "*/dist/*" \
        ! -path "*/build/*" \
        ! -path "*/.next/*" \
        ! -path "*/.venv/*" \
        ! -path "*/venv/*" \
        ! -path "*/.git/*" \
        2>/dev/null | wc -l)
    
    formatted_files=$(format_number "$file_count")
    printf "Code files: %s\n" "$formatted_files"
    
    # Estimate effort (rough LOC to days conversion)
    if [ "$total_lines" -gt 0 ]; then
        effort_days=$((total_lines / 100))
        formatted_effort=$(format_number "$effort_days")
        printf "Estimated effort: ~%s developer-days\n" "$formatted_effort"
    fi
    
    printf "\n"
    log_success "Line count analysis complete!"
}

# Execute main function
main "$@" 