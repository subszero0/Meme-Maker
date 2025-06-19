"""
Custom exceptions for the backend application.
Provides specific error types for different failure scenarios.
"""


class VideoProcessingError(Exception):
    """Base exception for video processing errors"""
    
    def __init__(self, message: str, job_id: str = None, error_code: str = None):
        self.message = message
        self.job_id = job_id
        self.error_code = error_code or "GENERAL_ERROR"
        super().__init__(self.message)


class QueueFullError(VideoProcessingError):
    """Raised when the processing queue is at capacity"""
    
    def __init__(self, message: str = "Queue is full"):
        super().__init__(message, error_code="QUEUE_FULL")


class ValidationError(VideoProcessingError):
    """Raised when input validation fails"""
    
    def __init__(self, message: str, field: str = None):
        self.field = field
        super().__init__(message, error_code="VALIDATION_ERROR")


class RepositoryError(VideoProcessingError):
    """Raised when repository operations fail"""
    
    def __init__(self, message: str):
        super().__init__(message, error_code="REPOSITORY_ERROR")


class JobNotFoundError(VideoProcessingError):
    """Raised when a job cannot be found"""
    
    def __init__(self, job_id: str):
        message = f"Job {job_id} not found"
        super().__init__(message, job_id=job_id, error_code="JOB_NOT_FOUND")


class ProcessingError(VideoProcessingError):
    """Raised when video processing fails"""
    
    def __init__(self, message: str, job_id: str = None):
        super().__init__(message, job_id=job_id, error_code="PROCESSING_ERROR") 