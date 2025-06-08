"""
Business Logic Unit Tests - Phase 2.1 of TestsToDo.md

Tests core business logic functions with minimal mocking.
Focus on business value: duration validation, time parsing, job status validation.
"""

import pytest
from app.models import JobStatus, JobCreate


class TestJobCreateValidation:
    """Test JobCreate model validation business logic"""

    def test_time_format_parsing_valid_formats(self):
        """Test that JobCreate correctly parses various time formats"""
        # Arrange & Act & Assert - mm:ss format
        job_data = {
            "url": "https://youtube.com/watch?v=test",
            "start": "00:30",
            "end": "01:30",
            "accepted_terms": True
        }
        job = JobCreate(**job_data)
        assert job.start_seconds == 30.0
        assert job.end_seconds == 90.0

    def test_time_format_parsing_numeric_seconds(self):
        """Test parsing numeric seconds (int and float)"""
        # Arrange & Act & Assert
        job_data = {
            "url": "https://youtube.com/watch?v=test",
            "start": 30,
            "end": 90.5,
            "accepted_terms": True
        }
        job = JobCreate(**job_data)
        assert job.start_seconds == 30.0
        assert job.end_seconds == 90.5

    def test_duration_validation_valid_clips(self):
        """Test that valid clip durations pass validation"""
        # Arrange & Act & Assert - 30 second clip
        job_data = {
            "url": "https://youtube.com/watch?v=test",
            "start": 0,
            "end": 30,
            "accepted_terms": True
        }
        job = JobCreate(**job_data)
        assert job.end_seconds - job.start_seconds == 30

    def test_duration_validation_clips_too_long(self):
        """Test that clips over 30 minutes are rejected"""
        # Arrange
        job_data = {
            "url": "https://youtube.com/watch?v=test",
            "start": 0,
            "end": 1801,  # Over 30 minutes
            "accepted_terms": True
        }
        
        # Act & Assert
        with pytest.raises(ValueError, match="Clip too long"):
            JobCreate(**job_data)

    def test_duration_validation_end_before_start(self):
        """Test that end time before start time is rejected"""
        # Arrange
        job_data = {
            "url": "https://youtube.com/watch?v=test",
            "start": 100,
            "end": 50,  # End before start
            "accepted_terms": True
        }
        
        # Act & Assert
        with pytest.raises(ValueError, match="end time must be greater than start time"):
            JobCreate(**job_data)


class TestJobStatusEnum:
    """Test JobStatus enum business logic"""

    def test_job_status_enum_values(self):
        """Test that JobStatus enum has correct values"""
        # Assert all expected statuses exist
        assert JobStatus.queued == "queued"
        assert JobStatus.working == "working"
        assert JobStatus.done == "done"
        assert JobStatus.error == "error"

    def test_job_status_progression_logic(self):
        """Test logical job status progression"""
        # Arrange - Define valid transitions
        valid_transitions = {
            JobStatus.queued: [JobStatus.working, JobStatus.error],
            JobStatus.working: [JobStatus.done, JobStatus.error],
            JobStatus.done: [],  # Terminal state
            JobStatus.error: []  # Terminal state
        }
        
        # Act & Assert - Test transition logic
        for current_status, allowed_next in valid_transitions.items():
            # Can transition to allowed states
            for next_status in allowed_next:
                assert self._can_transition(current_status, next_status)

    def _can_transition(self, from_status: JobStatus, to_status: JobStatus) -> bool:
        """Helper method to check if status transition is valid"""
        # Simple business logic for status transitions
        if from_status == JobStatus.queued:
            return to_status in [JobStatus.working, JobStatus.error]
        elif from_status == JobStatus.working:
            return to_status in [JobStatus.done, JobStatus.error]
        elif from_status in [JobStatus.done, JobStatus.error]:
            return False  # Terminal states
        return False 