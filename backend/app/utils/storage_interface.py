from abc import ABC, abstractmethod


class StorageInterface(ABC):
    """Abstract interface for storage operations"""
    
    @abstractmethod
    def upload(self, local_path: str, key: str) -> None:
        """Upload a file from local_path to the storage under key."""
        pass

    @abstractmethod
    def generate_presigned_url(self, key: str, expiration: int) -> str:
        """Return a presigned URL for the given key."""
        pass

    @abstractmethod
    def delete(self, key: str) -> None:
        """Delete the object identified by key."""
        pass 