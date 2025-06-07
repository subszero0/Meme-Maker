#!/usr/bin/env python3
"""
Script to fix Flake8 issues in backend code
Handles unused imports (F401), unused variables (F841), and long lines (E501)
"""

import os
import re

def fix_unused_imports():
    """Remove unused imports from test files"""
    fixes = [
        ("tests/test_jobs.py", "from decimal import Decimal"),
        ("tests/test_jobs.py", "from app.models import JobStatus"),
        ("tests/test_jobs.py", "from app.ratelimit import clip_limiter"),
        ("tests/test_jobs_mock_storage_simplified.py", "from datetime import datetime"),
        ("tests/test_jobs_mock_storage_simplified.py", "from unittest.mock import MagicMock, patch"),
        ("tests/test_jobs_with_mock_storage.py", "from app.models import JobStatus"),
        ("tests/test_mock_storage_integration.py", "import pytest"),
        ("tests/test_rate_limit.py", "import asyncio"),
        ("tests/test_rate_limit.py", "import time"),
        ("tests/test_rate_limit.py", "from fastapi import FastAPI"),
        ("tests/test_security_middleware.py", "from unittest.mock import patch"),
        ("tests/test_simple.py", "import pytest"),
        ("tests/test_storage_interface.py", "from unittest.mock import Mock"),
        ("tests/test_worker_integration.py", "import logging"),
        ("tests/test_worker_integration.py", "import tempfile"),
        ("tests/test_worker_integration.py", "import time"),
        ("tests/test_worker_integration.py", "from app import redis, settings"),
    ]
    
    for file_path, import_line in fixes:
        fix_file_import(file_path, import_line)

def fix_file_import(file_path, import_to_remove):
    """Remove specific import from file"""
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Remove the import line
        lines = content.split('\n')
        new_lines = []
        for line in lines:
            if import_to_remove not in line:
                new_lines.append(line)
        
        with open(file_path, 'w') as f:
            f.write('\n'.join(new_lines))
        
        print(f"✅ Removed '{import_to_remove}' from {file_path}")
    except Exception as e:
        print(f"❌ Error fixing {file_path}: {e}")

def fix_unused_variables():
    """Fix unused variables by prefixing with underscore or using them"""
    fixes = [
        ("app/api/jobs.py", 226, "except Exception as e:", "except Exception as _e:"),
        ("tests/test_rate_limit.py", 72, "mock_redis", "_mock_redis"),
        ("tests/test_rate_limit.py", 142, "mock_redis", "_mock_redis"),
        ("tests/test_security_middleware.py", 132, "has_cors", "_has_cors"),
    ]
    
    for file_path, line_num, old_text, new_text in fixes:
        fix_file_line(file_path, line_num, old_text, new_text)

def fix_file_line(file_path, target_line, old_text, new_text):
    """Replace text on specific line"""
    try:
        with open(file_path, 'r') as f:
            lines = f.readlines()
        
        if target_line <= len(lines):
            lines[target_line - 1] = lines[target_line - 1].replace(old_text, new_text)
        
        with open(file_path, 'w') as f:
            f.writelines(lines)
        
        print(f"✅ Fixed line {target_line} in {file_path}")
    except Exception as e:
        print(f"❌ Error fixing {file_path}: {e}")

def fix_long_lines():
    """Fix lines that are too long"""
    long_line_fixes = [
        # These need manual attention due to complexity
        ("tests/test_e2e_smoke.py", [230, 266, 282]),
        ("tests/test_jobs_with_mock_storage.py", [65, 259, 261]),
        ("tests/test_mock_storage_integration.py", [94]),
        ("tests/test_security_middleware.py", [46, 50, 116, 136]),
        ("tests/test_storage_interface.py", [47]),
        ("tests/test_worker_integration.py", [125]),
    ]
    
    for file_path, line_numbers in long_line_fixes:
        print(f"⚠️ Manual fix needed for long lines in {file_path}: {line_numbers}")

if __name__ == "__main__":
    print("🔧 Fixing Flake8 issues...")
    
    # Change to backend directory
    os.chdir("backend")
    
    print("\n📋 Fixing unused imports...")
    fix_unused_imports()
    
    print("\n📋 Fixing unused variables...")
    fix_unused_variables()
    
    print("\n📋 Long lines require manual fixing...")
    fix_long_lines()
    
    print("\n✅ Automated fixes complete!")
    print("💡 Run 'python -m flake8 .' to verify fixes") 