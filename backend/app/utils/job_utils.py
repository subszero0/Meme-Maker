"""
Utility functions for job management.
"""

import uuid


def generate_job_id() -> str:
    """
    Generates a unique job ID using UUIDv4.

    Returns:
        str: A unique identifier for a job.
    """
    return str(uuid.uuid4())
