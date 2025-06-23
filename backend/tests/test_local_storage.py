import asyncio
import hashlib
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

import pytest

from app.config import get_settings
from app.storage import LocalStorageManager
from app.storage_factory import get_storage_manager


@pytest.fixture
def temp_storage_dir():
    """Create a temporary directory for testing"""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


@pytest.fixture
def storage_manager(temp_storage_dir):
    """Create a LocalStorageManager instance for testing"""
    return LocalStorageManager(temp_storage_dir)


@pytest.mark.asyncio
async def test_local_storage_save_and_get(storage_manager):
    """Test basic save and get operations"""
    job_id = "test-job-123"
    video_title = "Test Video"
    video_data = b"fake video data for testing"

    # Save the video
    result = await storage_manager.save(job_id, video_data, video_title)

    # Verify save result
    assert "file_path" in result
    assert "full_path" in result
    assert "sha256" in result
    assert "size" in result
    assert "filename" in result
    assert result["size"] == len(video_data)
    assert result["sha256"] == hashlib.sha256(video_data).hexdigest()

    # Test get operation
    file_path = await storage_manager.get(job_id)
    assert file_path is not None
    assert file_path.exists()

    # Verify file content
    with open(file_path, "rb") as f:
        saved_data = f.read()
    assert saved_data == video_data


@pytest.mark.asyncio
async def test_iso_8601_organization(storage_manager):
    """Test that files are organized in ISO-8601 date directories"""
    job_id = "date-test-456"
    video_title = "Date Test Video"
    video_data = b"test video data"

    # Mock datetime to control the date
    test_date = datetime(2024, 1, 15, 10, 30, 0)
    with patch("app.storage.datetime") as mock_datetime:
        mock_datetime.utcnow.return_value = test_date

        result = await storage_manager.save(job_id, video_data, video_title)

        # Verify the file is in the correct date directory
        expected_date_dir = "2024-01-15"
        assert expected_date_dir in result["file_path"]

        # Verify directory structure
        date_path = storage_manager.base_path / expected_date_dir
        assert date_path.exists()
        assert date_path.is_dir()


@pytest.mark.asyncio
async def test_atomic_operations(storage_manager):
    """Test that save operations are atomic (temp file then rename)"""
    job_id = "atomic-test-789"
    video_title = "Atomic Test Video"
    video_data = b"atomic test data"

    # Just test the atomic behavior without complex mocking
    result = await storage_manager.save(job_id, video_data, video_title)

    # Verify final file exists
    final_path = Path(result["full_path"])
    assert final_path.exists()

    # Verify file contents are correct
    with open(final_path, "rb") as f:
        saved_data = f.read()
    assert saved_data == video_data

    # Verify no temp files are left behind
    temp_files = list(final_path.parent.glob("*.tmp"))
    assert len(temp_files) == 0, f"Temporary files found: {temp_files}"


@pytest.mark.asyncio
async def test_file_integrity_validation(storage_manager):
    """Test SHA256 integrity validation"""
    job_id = "integrity-test-101"
    video_title = "Integrity Test Video"
    video_data = b"integrity test data"
    expected_hash = hashlib.sha256(video_data).hexdigest()

    # Save the file
    result = await storage_manager.save(job_id, video_data, video_title)
    file_path = Path(result["full_path"])

    # Test successful validation
    is_valid = await storage_manager.validate_file_integrity(file_path, expected_hash)
    assert is_valid

    # Test failed validation with wrong hash
    wrong_hash = hashlib.sha256(b"different data").hexdigest()
    is_invalid = await storage_manager.validate_file_integrity(file_path, wrong_hash)
    assert not is_invalid

    # Test validation of non-existent file
    fake_path = storage_manager.base_path / "non-existent.mp4"
    is_missing = await storage_manager.validate_file_integrity(fake_path, expected_hash)
    assert not is_missing


@pytest.mark.asyncio
async def test_cross_day_retrieval(storage_manager):
    """Test retrieval of files from previous days"""
    job_id = "cross-day-test-202"
    video_title = "Cross Day Test Video"
    video_data = b"cross day test data"

    # Save file with yesterday's date
    yesterday = datetime.utcnow() - timedelta(days=1)
    with patch("app.storage.datetime") as mock_datetime:
        mock_datetime.utcnow.return_value = yesterday

        await storage_manager.save(job_id, video_data, video_title)

    # Try to retrieve with today's date (should still find it)
    file_path = await storage_manager.get(job_id)
    assert file_path is not None
    assert file_path.exists()

    # Verify file exists check
    exists = await storage_manager.exists(job_id)
    assert exists


@pytest.mark.asyncio
async def test_storage_stats(storage_manager):
    """Test storage statistics functionality"""
    # Initially should be empty
    stats = storage_manager.get_storage_stats()
    assert stats["file_count"] == 0
    assert stats["total_size_bytes"] == 0
    assert stats["total_size_mb"] == 0.0

    # Add some files
    test_files = [
        ("stats-test-1", "Stats Test 1", b"test data 1"),
        ("stats-test-2", "Stats Test 2", b"test data 2 longer"),
        ("stats-test-3", "Stats Test 3", b"test data 3 even longer content"),
    ]

    total_expected_size = 0
    for job_id, title, data in test_files:
        await storage_manager.save(job_id, data, title)
        total_expected_size += len(data)

    # Check updated stats
    stats = storage_manager.get_storage_stats()
    assert stats["file_count"] == 3
    assert stats["total_size_bytes"] == total_expected_size
    assert stats["total_size_mb"] == round(total_expected_size / 1024 / 1024, 2)
    assert "base_path" in stats


@pytest.mark.asyncio
async def test_delete_operation(storage_manager):
    """Test file deletion"""
    job_id = "delete-test-303"
    video_title = "Delete Test Video"
    video_data = b"delete test data"

    # Save file
    await storage_manager.save(job_id, video_data, video_title)

    # Verify file exists
    assert await storage_manager.exists(job_id)

    # Delete file
    deleted = await storage_manager.delete(job_id)
    assert deleted

    # Verify file no longer exists
    assert not await storage_manager.exists(job_id)

    # Try to delete non-existent file
    deleted_again = await storage_manager.delete(job_id)
    assert not deleted_again


@pytest.mark.asyncio
async def test_download_url_generation(storage_manager):
    """Test download URL generation"""
    job_id = "url-test-404"
    filename = "test_video.mp4"

    url = storage_manager.get_download_url(job_id, filename)

    # Should contain base URL and job ID
    assert get_settings().base_url in url
    assert job_id in url
    assert "download" in url


def test_storage_factory_local():
    """Test storage factory returns LocalStorageManager for local backend"""
    with patch.object(get_settings(), "storage_backend", "local"):
        storage = get_storage_manager()
        assert isinstance(storage, LocalStorageManager)


# S3 storage test removed - migration to local storage complete
# def test_storage_factory_s3():
#     """Test storage factory returns S3StorageManager for s3 backend (when boto3 available)"""
#     with patch.object(settings, 'storage_backend', 's3'):
#         try:
#             storage = get_storage_manager()
#             assert isinstance(storage, S3StorageManager)
#         except RuntimeError as e:
#             if "boto3 not available" in str(e):
#                 pytest.skip("boto3 not available - S3 backend not installed (expected during migration)")
#             else:
#                 raise


def test_storage_factory_invalid():
    """Test storage factory defaults to local storage for invalid backend"""
    with patch.object(get_settings(), "storage_backend", "invalid"):
        # Should default to LocalStorageManager, not raise error
        storage = get_storage_manager()
        assert isinstance(storage, LocalStorageManager)


@pytest.mark.asyncio
async def test_error_handling_unwritable_directory():
    """Test error handling for unwritable directory"""
    import platform

    if platform.system() == "Windows":
        # Skip this test on Windows as chmod doesn't work the same way
        pytest.skip("chmod-based permission testing not reliable on Windows")

    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a directory and make it read-only
        readonly_dir = Path(temp_dir) / "readonly"
        readonly_dir.mkdir()
        readonly_dir.chmod(0o444)  # Read-only

        try:
            with pytest.raises(RuntimeError, match="clips_dir not writable"):
                LocalStorageManager(str(readonly_dir))
        finally:
            # Cleanup: restore write permissions
            readonly_dir.chmod(0o755)


@pytest.mark.asyncio
async def test_fallback_to_sync_operations(storage_manager):
    """Test fallback to sync operations when aiofiles is not available"""
    job_id = "sync-test-505"
    video_title = "Sync Test Video"
    video_data = b"sync test data"

    # Mock aiofiles as unavailable
    with patch("app.storage.AIOFILES_AVAILABLE", False):
        # Should still work with sync operations
        result = await storage_manager.save(job_id, video_data, video_title)

        assert "file_path" in result
        assert result["size"] == len(video_data)

        # Verify file was saved correctly
        file_path = await storage_manager.get(job_id)
        assert file_path is not None
        assert file_path.exists()


@pytest.mark.asyncio
async def test_sanitized_filename_in_save(storage_manager):
    """Test that video titles are sanitized for filenames"""
    job_id = "filename-test-606"
    problematic_title = "Test/Video: With\\Bad*Characters?"
    video_data = b"filename test data"

    result = await storage_manager.save(job_id, video_data, problematic_title)

    # Filename should be sanitized
    filename = result["filename"]
    assert "/" not in filename
    assert "\\" not in filename
    assert ":" not in filename
    assert "*" not in filename
    assert "?" not in filename

    # But should still contain recognizable parts
    assert "Test" in filename
    assert "Video" in filename
    assert job_id in filename


@pytest.mark.asyncio
async def test_concurrent_save_operations(storage_manager):
    """Test multiple concurrent save operations don't interfere"""
    # Create multiple save operations concurrently
    tasks = []
    for i in range(5):
        job_id = f"concurrent-test-{i}"
        video_title = f"Concurrent Test Video {i}"
        video_data = f"concurrent test data {i}".encode()

        task = storage_manager.save(job_id, video_data, video_title)
        tasks.append(task)

    # Wait for all to complete
    results = await asyncio.gather(*tasks)

    # Verify all saved successfully
    assert len(results) == 5
    for i, result in enumerate(results):
        assert "file_path" in result
        assert f"concurrent-test-{i}" in result["filename"]

        # Verify file exists
        file_path = Path(result["full_path"])
        assert file_path.exists()
