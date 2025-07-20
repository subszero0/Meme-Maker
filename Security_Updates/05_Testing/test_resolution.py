#!/usr/bin/env python3
import os
import sys
import json
import tempfile
import subprocess
from pathlib import Path
from typing import Dict, List, Optional
import requests
import time

# Test configuration
TEST_URL = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
API_BASE_URL = "http://localhost:8000/api/v1"
TEST_CLIP_START = 0.0
TEST_CLIP_END = 10.0

class VideoProperties:
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0
        self._properties = self._extract_properties()
    
    def _extract_properties(self) -> Dict:
        try:
            cmd = ['ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_streams', '-show_format', self.file_path]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            data = json.loads(result.stdout)
            
            video_stream = None
            for stream in data.get('streams', []):
                if stream.get('codec_type') == 'video':
                    video_stream = stream
                    break
            
            if not video_stream:
                return {}
            
            return {
                'width': video_stream.get('width', 0),
                'height': video_stream.get('height', 0),
                'bitrate': int(video_stream.get('bit_rate', 0)) if video_stream.get('bit_rate') else 0,
                'codec': video_stream.get('codec_name', ''),
                'fps': eval(video_stream.get('r_frame_rate', '0/1')) if '/' in str(video_stream.get('r_frame_rate', '')) else 0,
                'duration': float(data.get('format', {}).get('duration', 0)),
                'total_bitrate': int(data.get('format', {}).get('bit_rate', 0)) if data.get('format', {}).get('bit_rate') else 0
            }
        except Exception as e:
            print(f"Error extracting properties: {e}")
            return {}
    
    @property 
    def resolution(self) -> str:
        return f"{self._properties.get('width', 0)}x{self._properties.get('height', 0)}"
    
    @property
    def bitrate(self) -> int:
        return self._properties.get('bitrate', 0)
    
    @property
    def total_bitrate(self) -> int:
        return self._properties.get('total_bitrate', 0)
    
    def __str__(self) -> str:
        return (f"Resolution: {self.resolution}, "
                f"File Size: {self.file_size} bytes ({self.file_size/1024/1024:.2f} MB), "
                f"Video Bitrate: {self.bitrate} bps, "
                f"Total Bitrate: {self.total_bitrate} bps")

def get_available_formats(url: str) -> List[Dict]:
    try:
        response = requests.post(f"{API_BASE_URL}/metadata/extract", json={"url": url}, timeout=30)
        response.raise_for_status()
        data = response.json()
        return data.get('formats', [])
    except Exception as e:
        print(f"Error fetching formats: {e}")
        return []

def create_clip_job(url: str, start: float, end: float, format_id: Optional[str] = None) -> Optional[str]:
    try:
        payload = {"url": url, "in_ts": start, "out_ts": end}
        if format_id:
            payload["format_id"] = format_id
        
        response = requests.post(f"{API_BASE_URL}/jobs", json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()
        return data.get('id')
    except Exception as e:
        print(f"Error creating job: {e}")
        return None

def wait_for_job(job_id: str, timeout: int = 120) -> Optional[str]:
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        try:
            response = requests.get(f"{API_BASE_URL}/jobs/{job_id}")
            response.raise_for_status()
            data = response.json()
            
            status = data.get('status')
            print(f"Job {job_id} status: {status} (progress: {data.get('progress', 0)}%)")
            
            if status == 'done':
                return data.get('download_url')
            elif status == 'error':
                print(f"Job failed with error: {data.get('error_code', 'unknown')}")
                return None
            
            time.sleep(5)
        except Exception as e:
            print(f"Error checking job status: {e}")
            time.sleep(5)
    
    print(f"Job {job_id} timed out after {timeout} seconds")
    return None

def download_file(url: str, output_path: str) -> bool:
    try:
        response = requests.get(url, stream=True, timeout=60)
        response.raise_for_status()
        
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        return True
    except Exception as e:
        print(f"Error downloading file: {e}")
        return False

def test_resolution_picker():
    print("Testing Resolution Picker Functionality")
    print("=" * 50)
    
    # Get available formats
    print(f"Getting available formats for: {TEST_URL}")
    formats = get_available_formats(TEST_URL)
    
    if not formats:
        print("No formats available - test cannot proceed")
        return False
    
    print(f"Found {len(formats)} formats")
    
    # Select test formats (different resolutions)
    test_formats = []
    seen_resolutions = set()
    
    for fmt in formats:
        resolution = fmt.get('resolution', 'unknown')
        if resolution not in seen_resolutions and len(test_formats) < 3:
            test_formats.append(fmt)
            seen_resolutions.add(resolution)
    
    if len(test_formats) < 2:
        print("Need at least 2 different resolutions to test")
        return False
    
    print(f"Selected test formats:")
    for i, fmt in enumerate(test_formats):
        print(f"  {i+1}. {fmt['format_id']}: {fmt['resolution']} ({fmt.get('format_note', 'N/A')})")
    
    # Test each format
    test_results = []
    temp_dir = Path(tempfile.mkdtemp(prefix="resolution_test_"))
    
    try:
        for fmt in test_formats:
            format_id = fmt['format_id']
            resolution = fmt['resolution']
            
            print(f"\nTesting format {format_id} ({resolution})...")
            
            # Create job
            job_id = create_clip_job(TEST_URL, TEST_CLIP_START, TEST_CLIP_END, format_id)
            if not job_id:
                print(f"Failed to create job for format {format_id}")
                continue
            
            print(f"Created job {job_id}")
            
            # Wait for completion
            download_url = wait_for_job(job_id)
            if not download_url:
                print(f"Job failed for format {format_id}")
                continue
            
            # Download file
            output_file = temp_dir / f"test_{format_id}.mp4"
            if not download_file(download_url, str(output_file)):
                print(f"Failed to download file for format {format_id}")
                continue
            
            # Analyze properties
            props = VideoProperties(str(output_file))
            test_results.append({
                'format_id': format_id,
                'expected_resolution': resolution,
                'actual_properties': props,
            })
            
            print(f"Downloaded and analyzed: {props}")
    
    finally:
        # Clean up temp files
        try:
            import shutil
            shutil.rmtree(temp_dir)
        except:
            pass
    
    # Analyze results
    print(f"\nTest Results Analysis")
    print("=" * 50)
    
    if len(test_results) < 2:
        print("Not enough successful downloads to compare")
        return False
    
    # Check if files are identical
    properties_set = set()
    for result in test_results:
        props = result['actual_properties']
        key = (props.resolution, props.file_size, props.bitrate, props.total_bitrate)
        properties_set.add(key)
    
    if len(properties_set) == 1:
        print("ISSUE DETECTED: All files have identical properties!")
        print("This confirms the resolution picker is NOT working correctly.")
        
        print("\nDetailed Comparison:")
        for result in test_results:
            print(f"Format {result['format_id']} (expected {result['expected_resolution']}):")
            print(f"  Actual: {result['actual_properties']}")
        
        return False
    else:
        print("SUCCESS: Files have different properties!")
        print("The resolution picker appears to be working correctly.")
        
        print("\nDetailed Comparison:")
        for result in test_results:
            props = result['actual_properties']
            expected = result['expected_resolution']
            actual = props.resolution
            match = "✅" if expected == actual else "⚠️"
            print(f"Format {result['format_id']} {match}:")
            print(f"  Expected: {expected}")
            print(f"  Actual: {props}")
        
        return True

if __name__ == "__main__":
    print("Resolution Picker Test Suite")
    print("Checking if backend services are running...")
    
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        if response.status_code != 200:
            print("Backend service not responding correctly")
            sys.exit(1)
    except Exception as e:
        print(f"Cannot connect to backend service: {e}")
        print("Please make sure the development environment is running:")
        print("  docker-compose up -d")
        sys.exit(1)
    
    print("Backend service is running")
    
    success = test_resolution_picker()
    sys.exit(0 if success else 1) 