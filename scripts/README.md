# Scripts Directory

This directory contains automation and utility scripts for the Meme Maker project.

## Available Scripts

### 🧪 Testing Scripts

#### `run_smoke_tests.sh`
End-to-end smoke test runner that verifies the complete user flow.

```bash
# Run E2E tests against local development server
./scripts/run_smoke_tests.sh

# Run tests against a specific API URL
./scripts/run_smoke_tests.sh --url https://api.yourdomain.com

# Run only quick tests (skip full E2E flow)
./scripts/run_smoke_tests.sh --quick
```

**Features:**
- Configurable API endpoints and test videos
- Verbose output for debugging
- Colored output with progress indicators
- Custom timeouts and parameters

### 📊 Analysis Scripts

#### `line_counts.sh`
Counts lines of code by component directory and provides project statistics.

```bash
# Basic line count analysis
./scripts/line_counts.sh

# Show help
./scripts/line_counts.sh --help
```

**Output Example:**
```
📊 Meme Maker - Line Count Analysis
==========================================

✅ Using cloc for accurate code analysis

📁 Lines by Component:

backend         2,113 lines
frontend          800 lines
worker            200 lines
infra             150 lines
scripts           300 lines
.github           220 lines
docs              100 lines

📊 Summary:
🎯 Total Lines (components): 3,883

📈 Additional Statistics:
Code files: 70
Estimated effort: ~39 developer-days
```

**Features:**
- Uses `cloc` when available, falls back to `wc -l`
- Excludes generated files and dependencies
- Cross-platform compatible (Unix/Linux/macOS)
- Colored output with emoji indicators

#### `line_counts_simple.ps1`
PowerShell version of the line counter for Windows environments.

```powershell
# Basic line count
.\scripts\line_counts_simple.ps1

# Verbose output with file details
.\scripts\line_counts_simple.ps1 -Verbose
```

## Environment Requirements

### Unix/Linux/macOS
- **bash** or **sh** shell
- **find**, **wc**, **awk** (standard Unix tools)
- **cloc** (optional, for more accurate counting)

### Windows
- **PowerShell** 5.1+ 
- **WSL** (optional, for running bash scripts)

## Installation Notes

### Installing cloc
For more accurate line counting, install `cloc`:

```bash
# macOS (Homebrew)
brew install cloc

# Ubuntu/Debian
apt install cloc

# CentOS/RHEL
yum install cloc

# Windows (Chocolatey)
choco install cloc
```

### Making Scripts Executable

On Unix systems:
```bash
chmod +x scripts/*.sh
```

On Windows, PowerShell scripts are executable by default, but you may need to adjust execution policy:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

## Usage Patterns

### Development Workflow
```bash
# Quick project overview
./scripts/line_counts.sh

# Test changes before commit
./scripts/run_smoke_tests.sh --quick

# Full integration test
./scripts/run_smoke_tests.sh
```

### CI/CD Integration
```bash
# In GitHub Actions or similar
export BASE_URL=https://staging.api.example.com
./scripts/run_smoke_tests.sh
```

### Cross-Platform Development
```bash
# Unix/Linux/macOS
./scripts/line_counts.sh

# Windows PowerShell
.\scripts\line_counts_simple.ps1

# Windows with WSL
wsl ./scripts/line_counts.sh
```

## File Structure

```
scripts/
├── README.md                    # This file
├── line_counts.sh              # Line counter (bash/sh)
├── line_counts_simple.ps1      # Line counter (PowerShell)
└── run_smoke_tests.sh          # E2E test runner
```

## Contributing

When adding new scripts:

1. **Documentation:** Add usage examples and descriptions
2. **Cross-platform:** Consider Windows compatibility
3. **Error handling:** Use `set -e` and proper error messages
4. **Help text:** Include `--help` option
5. **Colors:** Use conditional color output for better UX

### Script Template

```bash
#!/bin/sh
set -e

# Script description here
# Usage: ./script_name.sh [options]

# Show help
if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    cat << EOF
Script Name

USAGE:
    $0 [OPTIONS]

OPTIONS:
    -h, --help          Show this help message

DESCRIPTION:
    What this script does...

EOF
    exit 0
fi

# Main logic here
main() {
    echo "Script execution..."
}

main "$@"
``` 