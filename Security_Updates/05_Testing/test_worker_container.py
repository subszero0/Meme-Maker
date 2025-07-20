#!/usr/bin/env python3
"""
Test script to run inside worker container to debug imports
"""

import sys
import os

print("🔍 Container Debug - Worker Import Test")
print(f"🔍 Current working directory: {os.getcwd()}")
print(f"🔍 Python executable: {sys.executable}")
print(f"🔍 Python path: {sys.path[:5]}")

# Check if backend directory exists
backend_path = "/app/backend"
print(f"🔍 Backend path exists: {os.path.exists(backend_path)}")
if os.path.exists(backend_path):
    backend_contents = os.listdir(backend_path)
    print(f"🔍 Backend directory contents: {backend_contents[:5]}")

# Test imports step by step - same as worker main.py
print("\n" + "="*50)
print("🧪 TESTING WORKER IMPORT SEQUENCE")
print("="*50)

# Step 1: Add backend to path (same as worker main.py)
try:
    print("\n1️⃣ Adding backend to Python path...")
    backend_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'backend')
    print(f"🔍 Calculated backend path: {backend_path}")
    
    if backend_path not in sys.path:
        sys.path.append(backend_path)
        print(f"✅ Added {backend_path} to sys.path")
    else:
        print(f"⚠️ Backend path already in sys.path")
        
except Exception as e:
    print(f"❌ Failed to add backend path: {e}")

# Step 2: Test imports
try:
    print("\n2️⃣ Testing backend app imports...")
    from app import redis, settings
    print(f"✅ Import successful - redis: {redis}, settings type: {type(settings)}")
except Exception as e:
    print(f"❌ Import failed: {e}")
    import traceback
    traceback.print_exc()

try:
    print("\n3️⃣ Testing models import...")
    from app.models import JobStatus
    print(f"✅ JobStatus import successful: {JobStatus}")
except Exception as e:
    print(f"❌ JobStatus import failed: {e}")
    import traceback
    traceback.print_exc()

try:
    print("\n4️⃣ Testing init_redis...")
    from app import init_redis
    redis_instance = init_redis()
    print(f"✅ Redis initialization: {type(redis_instance)}")
    
    if redis_instance:
        ping_result = redis_instance.ping()
        print(f"✅ Redis ping: {ping_result}")
    else:
        print("⚠️ Redis instance is None")
        
except Exception as e:
    print(f"❌ Redis test failed: {e}")
    import traceback
    traceback.print_exc()

print("\n🎯 Container import test complete") 