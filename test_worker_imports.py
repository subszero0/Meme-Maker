#!/usr/bin/env python3
"""
Test script to debug worker import issues
"""

import sys
import os

# Add backend to path exactly like worker does
backend_path = os.path.join(os.path.dirname(__file__), 'backend')
print(f"🔍 Backend path: {backend_path}")
print(f"🔍 Backend path exists: {os.path.exists(backend_path)}")

if backend_path not in sys.path:
    sys.path.insert(0, backend_path)
    print(f"✅ Added backend path to sys.path")

print(f"🔍 Current working directory: {os.getcwd()}")
print(f"🔍 Python path: {sys.path[:3]}...")

# Test imports step by step
try:
    print("\n1️⃣ Testing basic app import...")
    from app import redis, settings
    print(f"✅ Basic app import successful")
    print(f"🔍 Redis before init: {redis}")
    print(f"🔍 Settings: {type(settings)}")
except Exception as e:
    print(f"❌ Basic app import failed: {e}")
    import traceback
    traceback.print_exc()

try:
    print("\n2️⃣ Testing init_redis import...")
    from app import init_redis
    print(f"✅ init_redis import successful")
except Exception as e:
    print(f"❌ init_redis import failed: {e}")
    import traceback
    traceback.print_exc()

try:
    print("\n3️⃣ Testing Redis initialization...")
    redis_instance = init_redis()
    print(f"✅ Redis initialized: {type(redis_instance)}")
    
    if redis_instance:
        # Test ping
        result = redis_instance.ping()
        print(f"✅ Redis ping successful: {result}")
    else:
        print("⚠️ Redis initialization returned None")
        
except Exception as e:
    print(f"❌ Redis initialization failed: {e}")
    import traceback
    traceback.print_exc()

try:
    print("\n4️⃣ Testing JobStatus import...")
    from app.models import JobStatus
    print(f"✅ JobStatus import successful: {JobStatus}")
except Exception as e:
    print(f"❌ JobStatus import failed: {e}")
    import traceback
    traceback.print_exc()

print("\n🎯 Import test complete") 