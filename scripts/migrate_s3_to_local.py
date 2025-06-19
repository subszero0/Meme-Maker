#!/usr/bin/env python3
"""
S3 to Local Storage Migration Script
Migrates existing video files from S3 to local storage with integrity validation
"""
import asyncio
import os
import sys
import hashlib
from pathlib import Path
from datetime import datetime

# Add backend to path
sys.path.append('/app/backend')

try:
    import boto3
    from botocore.exceptions import ClientError
    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False
    print("Warning: boto3 not available, S3 migration will be skipped")

from app.config import settings
from app.storage import LocalStorageManager


class S3ToLocalMigrator:
    """Handles migration from S3 to local storage"""
    
    def __init__(self):
        self.local_storage = LocalStorageManager()
        self.s3_client = None
        self.bucket = settings.s3_bucket
        
        if BOTO3_AVAILABLE and settings.aws_access_key_id:
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=settings.aws_access_key_id,
                aws_secret_access_key=settings.aws_secret_access_key,
                region_name=settings.aws_region,
                endpoint_url=settings.aws_endpoint_url
            )
        else:
            print("S3 client not available - check AWS credentials")
    
    async def list_s3_objects(self):
        """List all objects in S3 bucket"""
        if not self.s3_client:
            return []
        
        try:
            response = self.s3_client.list_objects_v2(Bucket=self.bucket)
            return response.get('Contents', [])
        except ClientError as e:
            print(f"Error listing S3 objects: {e}")
            return []
    
    async def migrate_file(self, s3_key: str, continue_on_error: bool = True):
        """Migrate a single file from S3 to local storage"""
        try:
            print(f"📦 Migrating: {s3_key}")
            
            # Download from S3
            s3_object = self.s3_client.get_object(Bucket=self.bucket, Key=s3_key)
            content = s3_object['Body'].read()
            
            # Extract job_id and title from S3 key
            # Expected format: clips/YYYY-MM-DD/title_job_id.mp4
            key_parts = s3_key.split('/')
            if len(key_parts) >= 2:
                filename = key_parts[-1]
                if filename.endswith('.mp4'):
                    # Extract job_id from filename (last part before .mp4)
                    name_parts = filename[:-4].split('_')
                    if len(name_parts) >= 2:
                        job_id = name_parts[-1]
                        video_title = '_'.join(name_parts[:-1])
                    else:
                        job_id = name_parts[0]
                        video_title = "migrated_video"
                else:
                    job_id = filename
                    video_title = "migrated_video"
            else:
                job_id = s3_key.replace('/', '_')
                video_title = "migrated_video"
            
            # Save to local storage
            result = await self.local_storage.save(job_id, content, video_title)
            
            # Verify integrity
            local_hash = hashlib.sha256(content).hexdigest()
            if result['sha256'] == local_hash:
                print(f"✅ {s3_key} -> {result['file_path']} ({result['size']} bytes)")
                return True
            else:
                print(f"❌ Integrity check failed for {s3_key}")
                return False
                
        except Exception as e:
            print(f"❌ Error migrating {s3_key}: {e}")
            if not continue_on_error:
                raise
            return False
    
    async def migrate_all(self, continue_on_error: bool = True):
        """Migrate all files from S3 to local storage"""
        if not self.s3_client:
            print("❌ S3 client not available, skipping migration")
            return
        
        print(f"🚀 Starting S3 to Local migration")
        print(f"📂 Source bucket: {self.bucket}")
        print(f"📁 Target directory: {self.local_storage.base_path}")
        
        objects = await self.list_s3_objects()
        if not objects:
            print("📭 No objects found in S3 bucket")
            return
        
        print(f"📊 Found {len(objects)} objects to migrate")
        
        success_count = 0
        error_count = 0
        
        for obj in objects:
            if await self.migrate_file(obj['Key'], continue_on_error):
                success_count += 1
            else:
                error_count += 1
        
        print(f"\n📈 Migration Summary:")
        print(f"✅ Successful: {success_count}")
        print(f"❌ Failed: {error_count}")
        print(f"📊 Total: {len(objects)}")
        
        if error_count == 0:
            print("🎉 Migration completed successfully!")
        else:
            print(f"⚠️  Migration completed with {error_count} errors")


async def main():
    """Main migration entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Migrate files from S3 to local storage')
    parser.add_argument('--continue-on-error', action='store_true',
                       help='Continue migration even if individual files fail')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be migrated without actually doing it')
    
    args = parser.parse_args()
    
    migrator = S3ToLocalMigrator()
    
    if args.dry_run:
        print("🔍 DRY RUN - No files will be migrated")
        objects = await migrator.list_s3_objects()
        print(f"📊 Would migrate {len(objects)} objects:")
        for obj in objects[:10]:  # Show first 10
            print(f"  - {obj['Key']} ({obj['Size']} bytes)")
        if len(objects) > 10:
            print(f"  ... and {len(objects) - 10} more")
    else:
        await migrator.migrate_all(args.continue_on_error)


if __name__ == "__main__":
    asyncio.run(main()) 