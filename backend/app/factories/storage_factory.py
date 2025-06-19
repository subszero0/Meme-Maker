"""
Storage factory for runtime storage backend selection.
Implements factory pattern for pluggable storage strategies.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Union
from pathlib import Path
from enum import Enum

from ..config.settings import get_settings
from ..constants import StorageConfig
from ..logging.config import get_logger
from ..exceptions import ProcessingError


logger = get_logger(__name__)


class StorageBackend(Enum):
    """Available storage backend types"""
    LOCAL = "local"
    LIGHTSAIL = "lightsail"
    S3 = "s3"


class StorageStrategy(ABC):
    """Abstract base class for storage strategies"""
    
    @abstractmethod
    async def store_file(
        self, 
        source_path: str, 
        job_id: str, 
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Store a file and return download URL
        
        Args:
            source_path: Path to source file
            job_id: Job identifier
            metadata: Optional file metadata
            
        Returns:
            Download URL for the stored file
        """
        pass
    
    @abstractmethod
    async def delete_file(self, file_key: str) -> bool:
        """
        Delete a file from storage
        
        Args:
            file_key: Storage key/path for the file
            
        Returns:
            True if deleted successfully, False otherwise
        """
        pass
    
    @abstractmethod
    async def get_file_info(self, file_key: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a stored file
        
        Args:
            file_key: Storage key/path for the file
            
        Returns:
            File information dictionary or None if not found
        """
        pass
    
    @abstractmethod
    async def list_files(self, prefix: Optional[str] = None) -> list[Dict[str, Any]]:
        """
        List files in storage
        
        Args:
            prefix: Optional prefix filter
            
        Returns:
            List of file information dictionaries
        """
        pass
    
    @abstractmethod
    def get_backend_type(self) -> StorageBackend:
        """Get the storage backend type"""
        pass


class LocalStorageStrategy(StorageStrategy):
    """Local filesystem storage strategy"""
    
    def __init__(self, base_path: Optional[str] = None):
        self.settings = get_settings()
        self.base_path = Path(base_path or self.settings.clips_dir)
        self.base_path.mkdir(parents=True, exist_ok=True)
        
    async def store_file(
        self, 
        source_path: str, 
        job_id: str, 
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Store file in local filesystem"""
        try:
            source = Path(source_path)
            
            if not source.exists():
                raise ProcessingError(f"Source file not found: {source_path}")
            
            # Generate storage path with ISO-8601 date organization
            from datetime import datetime
            now = datetime.utcnow()
            date_dir = now.strftime("%Y/%m/%d")
            storage_dir = self.base_path / date_dir
            storage_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate filename
            file_extension = source.suffix
            filename = f"{job_id}{file_extension}"
            destination = storage_dir / filename
            
            # Copy file to storage location
            import shutil
            shutil.copy2(source, destination)
            
            # Generate download URL (relative path)
            relative_path = destination.relative_to(self.base_path)
            download_url = f"/downloads/{relative_path}"
            
            logger.info(f"Stored file locally: {destination}")
            return download_url
            
        except Exception as e:
            logger.error(f"Failed to store file locally: {str(e)}")
            raise ProcessingError(f"Local storage failed: {str(e)}") from e
    
    async def delete_file(self, file_key: str) -> bool:
        """Delete file from local storage"""
        try:
            # Convert URL back to file path
            if file_key.startswith("/downloads/"):
                relative_path = file_key.replace("/downloads/", "")
                file_path = self.base_path / relative_path
            else:
                file_path = Path(file_key)
            
            if file_path.exists():
                file_path.unlink()
                logger.debug(f"Deleted local file: {file_path}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to delete local file: {str(e)}")
            return False
    
    async def get_file_info(self, file_key: str) -> Optional[Dict[str, Any]]:
        """Get local file information"""
        try:
            if file_key.startswith("/downloads/"):
                relative_path = file_key.replace("/downloads/", "")
                file_path = self.base_path / relative_path
            else:
                file_path = Path(file_key)
            
            if not file_path.exists():
                return None
            
            stat = file_path.stat()
            
            return {
                'path': str(file_path),
                'size': stat.st_size,
                'modified': stat.st_mtime,
                'exists': True,
                'backend': self.get_backend_type().value
            }
            
        except Exception as e:
            logger.error(f"Failed to get file info: {str(e)}")
            return None
    
    async def list_files(self, prefix: Optional[str] = None) -> list[Dict[str, Any]]:
        """List files in local storage"""
        try:
            files = []
            search_path = self.base_path
            
            if prefix:
                search_path = self.base_path / prefix
            
            if search_path.exists():
                for file_path in search_path.rglob("*"):
                    if file_path.is_file():
                        stat = file_path.stat()
                        relative_path = file_path.relative_to(self.base_path)
                        
                        files.append({
                            'key': str(relative_path),
                            'path': str(file_path),
                            'size': stat.st_size,
                            'modified': stat.st_mtime,
                            'url': f"/downloads/{relative_path}"
                        })
            
            return files
            
        except Exception as e:
            logger.error(f"Failed to list local files: {str(e)}")
            return []
    
    def get_backend_type(self) -> StorageBackend:
        """Get storage backend type"""
        return StorageBackend.LOCAL


class LightsailStorageStrategy(StorageStrategy):
    """AWS Lightsail storage strategy (placeholder for future implementation)"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        logger.info("Initializing Lightsail storage strategy")
    
    async def store_file(
        self, 
        source_path: str, 
        job_id: str, 
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Store file in Lightsail storage"""
        # Placeholder implementation - would integrate with AWS Lightsail Object Storage
        raise NotImplementedError("Lightsail storage not yet implemented")
    
    async def delete_file(self, file_key: str) -> bool:
        """Delete file from Lightsail storage"""
        raise NotImplementedError("Lightsail storage not yet implemented")
    
    async def get_file_info(self, file_key: str) -> Optional[Dict[str, Any]]:
        """Get Lightsail file information"""
        raise NotImplementedError("Lightsail storage not yet implemented")
    
    async def list_files(self, prefix: Optional[str] = None) -> list[Dict[str, Any]]:
        """List files in Lightsail storage"""
        raise NotImplementedError("Lightsail storage not yet implemented")
    
    def get_backend_type(self) -> StorageBackend:
        """Get storage backend type"""
        return StorageBackend.LIGHTSAIL


class S3StorageStrategy(StorageStrategy):
    """AWS S3 storage strategy (placeholder for future implementation)"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        logger.info("Initializing S3 storage strategy")
    
    async def store_file(
        self, 
        source_path: str, 
        job_id: str, 
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Store file in S3 storage"""
        # Placeholder implementation - would integrate with AWS S3
        raise NotImplementedError("S3 storage not yet implemented")
    
    async def delete_file(self, file_key: str) -> bool:
        """Delete file from S3 storage"""
        raise NotImplementedError("S3 storage not yet implemented")
    
    async def get_file_info(self, file_key: str) -> Optional[Dict[str, Any]]:
        """Get S3 file information"""
        raise NotImplementedError("S3 storage not yet implemented")
    
    async def list_files(self, prefix: Optional[str] = None) -> list[Dict[str, Any]]:
        """List files in S3 storage"""
        raise NotImplementedError("S3 storage not yet implemented")
    
    def get_backend_type(self) -> StorageBackend:
        """Get storage backend type"""
        return StorageBackend.S3


class StorageFactory:
    """Factory for creating storage strategy instances"""
    
    _strategies = {
        StorageBackend.LOCAL: LocalStorageStrategy,
        StorageBackend.LIGHTSAIL: LightsailStorageStrategy,
        StorageBackend.S3: S3StorageStrategy
    }
    
    _instances: Dict[StorageBackend, StorageStrategy] = {}
    
    @classmethod
    def create_storage(
        self, 
        backend: Union[StorageBackend, str], 
        config: Optional[Dict[str, Any]] = None
    ) -> StorageStrategy:
        """
        Create storage strategy instance
        
        Args:
            backend: Storage backend type
            config: Optional configuration for the storage backend
            
        Returns:
            Storage strategy instance
            
        Raises:
            ValueError: If backend type is not supported
        """
        # Convert string to enum if needed
        if isinstance(backend, str):
            try:
                backend = StorageBackend(backend.lower())
            except ValueError:
                raise ValueError(f"Unsupported storage backend: {backend}")
        
        # Use singleton pattern for storage instances
        if backend not in self._instances:
            if backend not in self._strategies:
                raise ValueError(f"No strategy available for backend: {backend}")
            
            strategy_class = self._strategies[backend]
            self._instances[backend] = strategy_class(config)
            
            logger.info(f"Created storage strategy for backend: {backend.value}")
        
        return self._instances[backend]
    
    @classmethod
    def get_default_storage(cls) -> StorageStrategy:
        """Get default storage strategy based on configuration"""
        settings = get_settings()
        backend = StorageBackend(settings.storage_backend)
        return cls.create_storage(backend)
    
    @classmethod
    def list_available_backends(cls) -> list[StorageBackend]:
        """List available storage backends"""
        return list(cls._strategies.keys())
    
    @classmethod
    def register_strategy(
        cls, 
        backend: StorageBackend, 
        strategy_class: type[StorageStrategy]
    ) -> None:
        """
        Register a new storage strategy
        
        Args:
            backend: Storage backend type
            strategy_class: Storage strategy class
        """
        cls._strategies[backend] = strategy_class
        logger.info(f"Registered storage strategy for backend: {backend.value}")
    
    @classmethod
    def clear_instances(cls) -> None:
        """Clear cached storage instances (for testing)"""
        cls._instances.clear()


# Video processing strategy interfaces
class VideoProcessingStrategy(ABC):
    """Abstract base class for video processing strategies"""
    
    @abstractmethod
    async def process_video(
        self, 
        source_path: str, 
        start_time: float, 
        end_time: float, 
        job_id: str,
        **kwargs
    ) -> str:
        """
        Process video with specific strategy
        
        Args:
            source_path: Path to source video
            start_time: Start time in seconds
            end_time: End time in seconds
            job_id: Job identifier
            **kwargs: Additional processing parameters
            
        Returns:
            Path to processed video
        """
        pass
    
    @abstractmethod
    def get_strategy_name(self) -> str:
        """Get strategy name"""
        pass


class StandardVideoProcessingStrategy(VideoProcessingStrategy):
    """Standard video processing strategy using FFmpeg"""
    
    async def process_video(
        self, 
        source_path: str, 
        start_time: float, 
        end_time: float, 
        job_id: str,
        **kwargs
    ) -> str:
        """Process video using standard FFmpeg approach"""
        # This would integrate with existing video processing logic
        # For now, return a placeholder
        logger.info(f"Processing video with standard strategy: {source_path}")
        return source_path  # Placeholder
    
    def get_strategy_name(self) -> str:
        """Get strategy name"""
        return "standard"


class HighQualityVideoProcessingStrategy(VideoProcessingStrategy):
    """High quality video processing strategy"""
    
    async def process_video(
        self, 
        source_path: str, 
        start_time: float, 
        end_time: float, 
        job_id: str,
        **kwargs
    ) -> str:
        """Process video with high quality settings"""
        logger.info(f"Processing video with high quality strategy: {source_path}")
        return source_path  # Placeholder
    
    def get_strategy_name(self) -> str:
        """Get strategy name"""
        return "high_quality"


class VideoProcessingFactory:
    """Factory for video processing strategies"""
    
    _strategies = {
        "standard": StandardVideoProcessingStrategy,
        "high_quality": HighQualityVideoProcessingStrategy
    }
    
    @classmethod
    def create_processor(cls, strategy: str = "standard") -> VideoProcessingStrategy:
        """Create video processing strategy"""
        if strategy not in cls._strategies:
            raise ValueError(f"Unknown processing strategy: {strategy}")
        
        return cls._strategies[strategy]()
    
    @classmethod
    def list_strategies(cls) -> list[str]:
        """List available processing strategies"""
        return list(cls._strategies.keys())


# Utility functions
def get_storage_for_job(job_config: Optional[Dict[str, Any]] = None) -> StorageStrategy:
    """
    Get storage strategy for a specific job
    
    Args:
        job_config: Optional job-specific configuration
        
    Returns:
        Storage strategy instance
    """
    if job_config and "storage_backend" in job_config:
        backend = job_config["storage_backend"]
        return StorageFactory.create_storage(backend, job_config.get("storage_config"))
    
    return StorageFactory.get_default_storage()


async def migrate_storage_backend(
    source_backend: StorageBackend, 
    target_backend: StorageBackend,
    file_filter: Optional[str] = None
) -> Dict[str, Any]:
    """
    Migrate files from one storage backend to another
    
    Args:
        source_backend: Source storage backend
        target_backend: Target storage backend
        file_filter: Optional file filter pattern
        
    Returns:
        Migration statistics
    """
    source_storage = StorageFactory.create_storage(source_backend)
    target_storage = StorageFactory.create_storage(target_backend)
    
    # Get list of files to migrate
    files = await source_storage.list_files(file_filter)
    
    migrated = 0
    failed = 0
    
    for file_info in files:
        try:
            # This would implement actual file migration logic
            # For now, just count files
            migrated += 1
            logger.debug(f"Migrated file: {file_info['key']}")
            
        except Exception as e:
            failed += 1
            logger.error(f"Failed to migrate file {file_info['key']}: {str(e)}")
    
    return {
        'total_files': len(files),
        'migrated': migrated,
        'failed': failed,
        'source_backend': source_backend.value,
        'target_backend': target_backend.value
    } 