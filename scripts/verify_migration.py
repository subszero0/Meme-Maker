#!/usr/bin/env python3
"""
Verification Script for S3 to Local Storage Migration
Tests the storage implementation and configuration
"""
import os
import sys
import asyncio
import tempfile
from pathlib import Path

# Add backend to path
sys.path.append('/app/backend')
sys.path.append('backend')

try:
    from app.config import settings
    from app.storage import LocalStorageManager
    from app.storage_factory import get_storage_manager
    print("✅ Successfully imported storage modules")
except ImportError as e:
    print(f"❌ Failed to import storage modules: {e}")
    sys.exit(1)


async def test_storage_implementation():
    """Test the storage implementation"""
    print("\n🧪 Testing Storage Implementation")
    print("=" * 50)
    
    # Test 1: Configuration
    print(f"📊 Storage backend: {settings.storage_backend}")
    print(f"📁 Clips directory: {settings.clips_dir}")
    print(f"🌐 Base URL: {settings.base_url}")
    
    # Test 2: Storage Manager Factory
    try:
        storage_manager = get_storage_manager()
        print(f"✅ Storage manager created: {type(storage_manager).__name__}")
    except Exception as e:
        print(f"❌ Failed to create storage manager: {e}")
        return False
    
    # Test 3: Basic Storage Operations
    if isinstance(storage_manager, LocalStorageManager):
        try:
            # Create temporary storage for testing
            with tempfile.TemporaryDirectory() as temp_dir:
                test_storage = LocalStorageManager(temp_dir)
                
                # Test save operation
                job_id = "test-verification-123"
                video_title = "verification_test"
                test_content = b"This is test content for verification"
                
                print(f"\n🔄 Testing save operation...")
                result = await test_storage.save(job_id, test_content, video_title)
                print(f"✅ File saved: {result['filename']}")
                print(f"   Size: {result['size']} bytes")
                print(f"   SHA256: {result['sha256'][:16]}...")
                
                # Test retrieval
                print(f"\n🔄 Testing retrieval operation...")
                file_path = await test_storage.get(job_id)
                if file_path and file_path.exists():
                    print(f"✅ File retrieved: {file_path}")
                    
                    # Verify content
                    with open(file_path, 'rb') as f:
                        retrieved_content = f.read()
                    
                    if retrieved_content == test_content:
                        print("✅ Content verification passed")
                    else:
                        print("❌ Content verification failed")
                        return False
                else:
                    print("❌ File retrieval failed")
                    return False
                
                # Test existence check
                if await test_storage.exists(job_id):
                    print("✅ Existence check passed")
                else:
                    print("❌ Existence check failed")
                    return False
                
                # Test deletion
                if await test_storage.delete(job_id):
                    print("✅ Deletion successful")
                else:
                    print("❌ Deletion failed")
                    return False
                
                # Test statistics
                stats = test_storage.get_storage_stats()
                print(f"\n📊 Storage statistics:")
                print(f"   Files: {stats['file_count']}")
                print(f"   Size: {stats['total_size_mb']} MB")
                
                print("\n🎉 All storage tests passed!")
                return True
                
        except Exception as e:
            print(f"❌ Storage test failed: {e}")
            return False
    else:
        print("⚠️  Storage manager is not LocalStorageManager, skipping detailed tests")
        return True


def test_directory_structure():
    """Test that the clips directory structure is correct"""
    print("\n📁 Testing Directory Structure")
    print("=" * 50)
    
    clips_dir = Path(settings.clips_dir)
    print(f"📂 Clips directory: {clips_dir}")
    
    if clips_dir.exists():
        print("✅ Clips directory exists")
        
        # Check if writable
        if os.access(clips_dir, os.W_OK):
            print("✅ Clips directory is writable")
        else:
            print("❌ Clips directory is not writable")
            return False
            
        # Show current contents
        contents = list(clips_dir.iterdir())
        if contents:
            print(f"📋 Current contents ({len(contents)} items):")
            for item in contents[:5]:  # Show first 5 items
                print(f"   - {item.name}")
            if len(contents) > 5:
                print(f"   ... and {len(contents) - 5} more")
        else:
            print("📭 Directory is empty")
        
        return True
    else:
        print("⚠️  Clips directory does not exist (will be created on first use)")
        return True


def test_environment_variables():
    """Test environment variable configuration"""
    print("\n🌍 Testing Environment Variables")
    print("=" * 50)
    
    env_vars = [
        ("STORAGE_BACKEND", settings.storage_backend),
        ("CLIPS_DIR", settings.clips_dir),
        ("BASE_URL", settings.base_url),
        ("REDIS_URL", settings.redis_url),
    ]
    
    for var_name, var_value in env_vars:
        env_value = os.getenv(var_name, "Not set")
        print(f"   {var_name}: {var_value} (env: {env_value})")
    
    print("✅ Environment variables loaded")
    return True


async def main():
    """Main verification function"""
    print("🚀 Lightsail Storage Migration Verification")
    print("=" * 50)
    print(f"Python path: {sys.path[:2]}")
    
    all_tests_passed = True
    
    # Run tests
    tests = [
        ("Environment Variables", test_environment_variables),
        ("Directory Structure", test_directory_structure),
        ("Storage Implementation", test_storage_implementation),
    ]
    
    for test_name, test_func in tests:
        print(f"\n🧪 Running {test_name} test...")
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
            
            if not result:
                all_tests_passed = False
                print(f"❌ {test_name} test failed")
            else:
                print(f"✅ {test_name} test passed")
                
        except Exception as e:
            print(f"❌ {test_name} test error: {e}")
            all_tests_passed = False
    
    # Final summary
    print("\n" + "=" * 50)
    if all_tests_passed:
        print("🎉 All verification tests passed!")
        print("✅ Storage migration implementation is ready")
        return 0
    else:
        print("❌ Some verification tests failed")
        print("⚠️  Please check the errors above")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code) 