import logging
from typing import Optional
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from .storage_interface import StorageInterface
from ..config import settings

logger = logging.getLogger(__name__)


class MinIOStorage(StorageInterface):
    """MinIO/S3 storage implementation"""
    
    def __init__(self):
        """Initialize boto3 client with MinIO/S3 configuration"""
        try:
            self.s3_client = boto3.client(
                's3',
                endpoint_url=settings.aws_endpoint_url,
                aws_access_key_id=settings.aws_access_key_id,
                aws_secret_access_key=settings.aws_secret_access_key,
                region_name=settings.aws_region,
            )
            self.bucket_name = settings.s3_bucket
            self._ensure_bucket_exists()
        except Exception as e:
            logger.error(f"Failed to initialize storage client: {e}")
            raise
    
    def _ensure_bucket_exists(self) -> None:
        """Create the clips bucket if it doesn't exist"""
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            logger.info(f"Bucket '{self.bucket_name}' exists")
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
                try:
                    self.s3_client.create_bucket(Bucket=self.bucket_name)
                    logger.info(f"Created bucket '{self.bucket_name}'")
                except ClientError as create_error:
                    logger.error(f"Failed to create bucket: {create_error}")
                    raise
            else:
                logger.error(f"Error checking bucket: {e}")
                raise
    
    def upload(self, local_path: str, key: str, content_disposition: Optional[str] = None) -> None:
        """Upload a file from local_path to the storage under key."""
        try:
            extra_args = {}
            if content_disposition:
                extra_args['ContentDisposition'] = content_disposition
            
            self.s3_client.upload_file(
                local_path, 
                self.bucket_name, 
                key,
                ExtraArgs=extra_args
            )
            logger.info(f"Uploaded {local_path} as {key}")
        except Exception as e:
            logger.error(f"Failed to upload {local_path}: {e}")
            raise
    
    def generate_presigned_url(self, key: str, expiration: int = 3600) -> str:
        """Return a presigned URL for the given key."""
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': key},
                ExpiresIn=expiration
            )
            logger.info(f"Generated presigned URL for {key} (expires in {expiration}s)")
            return url
        except Exception as e:
            logger.error(f"Failed to generate presigned URL for {key}: {e}")
            raise
    
    def delete(self, key: str) -> None:
        """Delete the object identified by key."""
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=key)
            logger.info(f"Deleted object {key}")
        except Exception as e:
            logger.error(f"Failed to delete {key}: {e}")
            raise 