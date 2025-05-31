#!/usr/bin/env python3
"""
Standalone test for numeric seconds validation in JobCreate model.
This bypasses the full FastAPI test infrastructure to focus on model validation.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "app"))

from pydantic import ValidationError
from app.models import JobCreate


def test_numeric_seconds():
    """Test JobCreate accepts numeric seconds"""
    job_data = {
        "url": "https://www.youtube.com/watch?v=test",
        "start": 10.5,
        "end": 70.25,
        "accepted_terms": True
    }
    
    job = JobCreate(**job_data)
    assert job.start_seconds == 10.5
    assert job.end_seconds == 70.25
    print("✓ Numeric seconds test passed")


def test_integer_seconds():
    """Test JobCreate accepts integer seconds"""
    job_data = {
        "url": "https://www.youtube.com/watch?v=test",
        "start": 15,
        "end": 75,
        "accepted_terms": True
    }
    
    job = JobCreate(**job_data)
    assert job.start_seconds == 15.0
    assert job.end_seconds == 75.0
    print("✓ Integer seconds test passed")


def test_string_timestamps():
    """Test JobCreate accepts hh:mm:ss string format"""
    job_data = {
        "url": "https://www.youtube.com/watch?v=test",
        "start": "00:00:10",
        "end": "00:01:10",
        "accepted_terms": True
    }
    
    job = JobCreate(**job_data)
    assert job.start_seconds == 10.0
    assert job.end_seconds == 70.0
    print("✓ String timestamps test passed")


def test_fractional_string_timestamps():
    """Test JobCreate accepts hh:mm:ss.mmm string format"""
    job_data = {
        "url": "https://www.youtube.com/watch?v=test",
        "start": "00:00:10.5",
        "end": "00:01:10.25",
        "accepted_terms": True
    }
    
    job = JobCreate(**job_data)
    assert job.start_seconds == 10.5
    assert job.end_seconds == 70.25
    print("✓ Fractional string timestamps test passed")


def test_invalid_string_format():
    """Test JobCreate rejects invalid string formats"""
    job_data = {
        "url": "https://www.youtube.com/watch?v=test",
        "start": "10:30",  # Missing seconds
        "end": "00:01:10",
        "accepted_terms": True
    }
    
    try:
        job = JobCreate(**job_data)
        assert False, "Should have raised ValidationError"
    except ValidationError as e:
        assert "Time must be in hh:mm:ss format or numeric seconds" in str(e)
        print("✓ Invalid string format test passed")


def test_invalid_time_values():
    """Test JobCreate rejects invalid time values"""
    job_data = {
        "url": "https://www.youtube.com/watch?v=test",
        "start": "00:00:abc",
        "end": "00:01:10",
        "accepted_terms": True
    }
    
    try:
        job = JobCreate(**job_data)
        assert False, "Should have raised ValidationError"
    except ValidationError as e:
        assert "Invalid time format" in str(e)
        print("✓ Invalid time values test passed")


if __name__ == "__main__":
    print("Testing JobCreate model with numeric seconds...")
    
    test_numeric_seconds()
    test_integer_seconds()
    test_string_timestamps()
    test_fractional_string_timestamps()
    test_invalid_string_format()
    test_invalid_time_values()
    
    print("\nAll tests passed! ✅")
    print("JobCreate model successfully accepts both numeric and string time formats.") 