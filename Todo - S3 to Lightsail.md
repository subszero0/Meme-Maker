# Todo - S3 to Lightsail Migration

## Overview
Migrate from Amazon S3 storage to local storage on Amazon Lightsail instance (2GB RAM, 60GB SSD) to reduce costs and simplify architecture.

## Current State Analysis
- **Current Storage**: Amazon S3 for processed video clips
- **Target Infrastructure**: Amazon Lightsail (2GB RAM, 60GB SSD)
- **Storage Requirements**: ~4GB for 20 concurrent jobs (60GB is sufficient)
- **Benefits**: Cost savings, simplified architecture, better performance, easier debugging

## Migration Steps

### Phase 1: Backend Storage Layer Migration

#### 1. Create Local Storage Implementation
**File**: `backend/app/storage.py` (NEW)
```python
import os
import aiofiles
from pathlib import Path
from typing import Optional
from app.config import settings

class LocalStorage:
    def __init__(self, base_path: str = "/opt/meme-maker/storage"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
    
    async def upload_file(self, file_path: str, content: bytes) -> str:
        full_path = self.base_path / file_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        
        async with aiofiles.open(full_path, 'wb') as f:
            await f.write(content)
        
        return str(full_path)
    
    async def download_file(self, file_path: str) -> bytes:
        full_path = self.base_path / file_path
        async with aiofiles.open(full_path, 'rb') as f:
            return await f.read()
    
    async def delete_file(self, file_path: str) -> bool:
        full_path = self.base_path / file_path
        if full_path.exists():
            full_path.unlink()
            return True
        return False
    
    async def file_exists(self, file_path: str) -> bool:
        full_path = self.base_path / file_path
        return full_path.exists()
    
    def get_download_url(self, file_path: str) -> str:
        return f"{settings.BASE_URL}/api/files/{file_path}"
```

#### 2. Update Configuration
**File**: `backend/app/config.py`
```python
# Remove S3 settings, add local storage
STORAGE_TYPE = os.getenv("STORAGE_TYPE", "local")  # "s3" or "local"
LOCAL_STORAGE_PATH = os.getenv("LOCAL_STORAGE_PATH", "/opt/meme-maker/storage")
BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")

# Keep S3 settings for backwards compatibility during migration
# Remove after migration is complete
```

#### 3. Create Storage Factory
**File**: `backend/app/storage_factory.py` (NEW)
```python
from app.config import settings
from app.storage import LocalStorage

def get_storage():
    if settings.STORAGE_TYPE == "local":
        return LocalStorage(settings.LOCAL_STORAGE_PATH)
    else:
        # Keep S3 for backwards compatibility during migration
        # Remove after migration complete
        from app.s3_storage import S3Storage
        return S3Storage()
```

#### 4. Add File Serving Endpoint
**File**: `backend/app/api/files.py` (NEW)
```python
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path
from app.config import settings

router = APIRouter()

@router.get("/files/{file_path:path}")
async def serve_file(file_path: str):
    full_path = Path(settings.LOCAL_STORAGE_PATH) / file_path
    
    if not full_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(
        path=str(full_path),
        media_type='application/octet-stream',
        filename=full_path.name
    )
```

#### 5. Update Main API Router
**File**: `backend/app/main.py`
```python
# Add file serving router
from app.api import files

app.include_router(files.router, prefix="/api", tags=["files"])
```

### Phase 2: Update Existing Code

#### 6. Update Worker Process
**File**: `worker/process_clip.py`
```python
# Replace S3 upload with local storage
from storage_factory import get_storage

async def process_and_store_clip(job_data):
    storage = get_storage()
    
    # Process video...
    processed_file_path = f"clips/{job_id}/{filename}"
    
    # Store locally instead of S3
    file_url = await storage.upload_file(processed_file_path, video_data)
    
    return file_url
```

#### 7. Update API Endpoints
**File**: `backend/app/api/clips.py`
```python
# Update download endpoints to use local storage
from app.storage_factory import get_storage

@router.get("/clips/{clip_id}/download")
async def download_clip(clip_id: str):
    storage = get_storage()
    
    if await storage.file_exists(f"clips/{clip_id}"):
        return {"download_url": storage.get_download_url(f"clips/{clip_id}")}
    else:
        raise HTTPException(status_code=404, detail="Clip not found")
```

### Phase 3: Infrastructure Setup

#### 8. Lightsail Instance Configuration
```bash
# SSH into Lightsail instance
ssh -i your-key.pem ubuntu@your-lightsail-ip

# Create storage directory
sudo mkdir -p /opt/meme-maker/storage
sudo chown www-data:www-data /opt/meme-maker/storage
sudo chmod 755 /opt/meme-maker/storage

# Setup Nginx for file serving (if needed)
sudo nano /etc/nginx/sites-available/meme-maker
```

**Nginx Configuration**:
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    # API proxy
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    # Direct file serving for large files (optional optimization)
    location /api/files/ {
        alias /opt/meme-maker/storage/;
        expires 1d;
        add_header Cache-Control "public, immutable";
    }
    
    # Frontend
    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

#### 9. Environment Variables Update
**File**: `.env` (Production)
```bash
# Storage Configuration
STORAGE_TYPE=local
LOCAL_STORAGE_PATH=/opt/meme-maker/storage
BASE_URL=https://your-domain.com

# Remove S3 variables after migration
# AWS_ACCESS_KEY_ID=
# AWS_SECRET_ACCESS_KEY=
# S3_BUCKET_NAME=
# S3_REGION=
```

#### 10. Dependencies Update
**File**: `backend/requirements.txt`
```bash
# Remove S3 dependencies
# boto3==1.26.137
# botocore==1.29.137

# Add local file handling
aiofiles==23.1.0
```

**File**: `backend/pyproject.toml`
```toml
# Remove boto3 from dependencies
# Add aiofiles
dependencies = [
    "fastapi[all]>=0.68.0",
    "aiofiles>=23.1.0",
    # ... other dependencies
]
```

### Phase 4: Migration Execution

#### 11. Data Migration Script
**File**: `scripts/migrate_s3_to_local.py` (NEW)
```python
import asyncio
import boto3
from pathlib import Path
from app.storage import LocalStorage
from app.config import settings

async def migrate_s3_to_local():
    # Initialize S3 client
    s3 = boto3.client('s3')
    local_storage = LocalStorage()
    
    # List all objects in S3 bucket
    response = s3.list_objects_v2(Bucket=settings.S3_BUCKET_NAME)
    
    for obj in response.get('Contents', []):
        print(f"Migrating {obj['Key']}...")
        
        # Download from S3
        s3_object = s3.get_object(Bucket=settings.S3_BUCKET_NAME, Key=obj['Key'])
        content = s3_object['Body'].read()
        
        # Upload to local storage
        await local_storage.upload_file(obj['Key'], content)
        
        print(f"✅ Migrated {obj['Key']}")
    
    print("Migration complete!")

if __name__ == "__main__":
    asyncio.run(migrate_s3_to_local())
```

#### 12. Cleanup Script
**File**: `scripts/cleanup_old_files.py` (NEW)
```python
import os
import time
from pathlib import Path
from app.config import settings

def cleanup_old_files(max_age_hours=24):
    """Remove files older than max_age_hours"""
    storage_path = Path(settings.LOCAL_STORAGE_PATH)
    cutoff_time = time.time() - (max_age_hours * 3600)
    
    for file_path in storage_path.rglob('*'):
        if file_path.is_file():
            if file_path.stat().st_mtime < cutoff_time:
                file_path.unlink()
                print(f"Deleted old file: {file_path}")

if __name__ == "__main__":
    cleanup_old_files()
```

### Phase 5: Testing & Validation

#### 13. Test Local Storage
**File**: `backend/tests/test_local_storage.py` (NEW)
```python
import pytest
import tempfile
from pathlib import Path
from app.storage import LocalStorage

@pytest.mark.asyncio
async def test_local_storage_operations():
    with tempfile.TemporaryDirectory() as temp_dir:
        storage = LocalStorage(temp_dir)
        
        # Test upload
        test_content = b"test video data"
        file_path = "test/video.mp4"
        
        await storage.upload_file(file_path, test_content)
        assert await storage.file_exists(file_path)
        
        # Test download
        downloaded = await storage.download_file(file_path)
        assert downloaded == test_content
        
        # Test delete
        assert await storage.delete_file(file_path)
        assert not await storage.file_exists(file_path)
```

#### 14. Integration Testing
```bash
# Test file upload/download workflow
curl -X POST http://localhost:8000/api/clips \
  -H "Content-Type: application/json" \
  -d '{"url": "test-video-url", "start_time": 0, "end_time": 30}'

# Test file serving
curl -I http://localhost:8000/api/files/clips/test-clip-id/video.mp4
```

### Phase 6: Deployment & Monitoring

#### 15. Deployment Checklist
- [ ] Deploy updated backend with local storage support
- [ ] Update environment variables on Lightsail
- [ ] Run data migration script
- [ ] Test file upload/download functionality
- [ ] Monitor disk usage
- [ ] Setup automated cleanup cron job
- [ ] Remove S3 dependencies and code
- [ ] Update documentation

#### 16. Monitoring Setup
**Cron Job for Cleanup**:
```bash
# Add to crontab: cleanup old files daily at 2 AM
0 2 * * * /usr/bin/python3 /opt/meme-maker/scripts/cleanup_old_files.py
```

**Disk Usage Monitoring**:
```bash
# Add to monitoring script
df -h /opt/meme-maker/storage
```

## Risk Mitigation

### Backup Strategy
1. Keep S3 code during migration (feature flag)
2. Test thoroughly in staging environment
3. Monitor disk usage closely
4. Implement automated cleanup
5. Have rollback plan ready

### Performance Considerations
1. Local storage is faster than S3 for small files
2. Nginx can serve static files efficiently
3. Monitor disk I/O on Lightsail instance
4. Consider file compression for storage efficiency

### Storage Management
1. Implement automatic cleanup of old files
2. Monitor disk usage with alerts
3. Consider log rotation for application logs
4. Regular backup of critical processed videos

## Success Criteria
- [ ] All video processing works with local storage
- [ ] File download URLs work correctly
- [ ] Disk usage stays under 50GB (safety margin)
- [ ] Performance meets or exceeds S3 performance
- [ ] Cost savings achieved (no S3 charges)
- [ ] Monitoring and cleanup automation in place

## Post-Migration Tasks
1. Remove all S3-related code and dependencies
2. Update documentation
3. Monitor system for 1 week
4. Optimize storage structure if needed
5. Consider adding CDN if file serving becomes bottleneck

## Estimated Timeline
- **Phase 1-2 (Code Changes)**: 2-3 days
- **Phase 3 (Infrastructure)**: 1 day
- **Phase 4 (Migration)**: 1 day
- **Phase 5 (Testing)**: 1-2 days
- **Phase 6 (Deployment & Monitoring)**: 1 day

**Total Estimated Time**: 6-8 days

## Notes
- 60GB storage is more than sufficient for current needs (~4GB for 20 concurrent jobs)
- Local storage provides better performance and easier debugging
- Simplified architecture reduces complexity and costs
- Lightsail instance specs (2GB RAM, 60GB SSD) are adequate for this workload
