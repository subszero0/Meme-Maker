#!/usr/bin/env python3
"""
Rotation Fix Testing Script
Creates test videos and applies different rotation correction methods
"""

import subprocess
import json
import tempfile
import os
from pathlib import Path

def run_cmd(cmd, description=""):
    """Run command and return success, stdout, stderr"""
    try:
        print(f"🔧 {description}")
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=True)
        return True, result.stdout, result.stderr
    except subprocess.CalledProcessError as e:
        return False, e.stdout, e.stderr

def analyze_video(video_path):
    """Quick video analysis"""
    cmd = f'ffprobe -v quiet -print_format json -show_streams "{video_path}"'
    success, stdout, stderr = run_cmd(cmd, f"Analyzing {Path(video_path).name}")
    
    if not success:
        return None
    
    try:
        metadata = json.loads(stdout)
        video_streams = [s for s in metadata.get('streams', []) if s.get('codec_type') == 'video']
        if video_streams:
            stream = video_streams[0]
            return {
                'width': stream.get('width'),
                'height': stream.get('height'),
                'codec': stream.get('codec_name')
            }
    except:
        pass
    return None

def test_rotation_corrections():
    """Test different rotation correction approaches"""
    print("🧪 ROTATION CORRECTION TESTING")
    print("=" * 60)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Step 1: Create a test video that's slightly rotated
        print("\n📝 STEP 1: Creating test video with known tilt")
        test_video = temp_path / "test_original.mp4"
        
        # Create a 10-second test video with color bars and text
        create_cmd = f'''ffmpeg -f lavfi -i "color=blue:size=640x360:duration=10:rate=25" -f lavfi -i "color=white:size=40x200" -filter_complex "[0][1]overlay=300:80:enable='between(t,2,8)'" -c:v libx264 -preset fast -crf 23 "{test_video}" -y'''
        
        success, _, stderr = run_cmd(create_cmd, "Creating test video")
        if not success:
            print(f"❌ Failed to create test video: {stderr}")
            return
        
        info = analyze_video(test_video)
        if info:
            print(f"✅ Test video: {info['width']}x{info['height']} {info['codec']}")
        
        # Step 2: Create a tilted version by applying a small rotation
        print("\n📝 STEP 2: Creating tilted version (simulating camera tilt)")
        tilted_video = temp_path / "test_tilted.mp4"
        
        # Apply a 2-degree clockwise rotation to simulate camera tilt
        tilt_cmd = f'''ffmpeg -i "{test_video}" -vf "rotate=2*PI/180:fillcolor=black" -c:v libx264 -preset fast -crf 23 "{tilted_video}" -y'''
        
        success, _, stderr = run_cmd(tilt_cmd, "Creating tilted version")
        if not success:
            print(f"❌ Failed to create tilted video: {stderr}")
            return
        
        info = analyze_video(tilted_video)
        if info:
            print(f"✅ Tilted video: {info['width']}x{info['height']} {info['codec']}")
        
        # Step 3: Test different correction methods
        print("\n📝 STEP 3: Testing rotation correction methods")
        
        correction_methods = {
            'rotate_minus_2': {
                'filter': 'rotate=-2*PI/180:fillcolor=black',
                'description': 'Counter-rotate by -2 degrees'
            },
            'deshake': {
                'filter': 'deshake=rx=16:ry=16',
                'description': 'Video stabilization (deshake)'
            },
            'perspective_correction': {
                'filter': 'perspective=x0=0:y0=0:x1=639:y1=0:x2=0:y2=359:x3=637:y3=357',
                'description': 'Perspective correction (slight keystone)'
            },
            'transpose_none': {
                'filter': '',
                'description': 'No correction (copy original tilt)'
            }
        }
        
        results = {}
        
        for method_name, method_config in correction_methods.items():
            print(f"\n🔧 Testing: {method_config['description']}")
            
            output_video = temp_path / f"test_corrected_{method_name}.mp4"
            
            if method_config['filter']:
                cmd = f'''ffmpeg -i "{tilted_video}" -vf "{method_config['filter']}" -c:v libx264 -preset fast -crf 23 "{output_video}" -y'''
            else:
                cmd = f'''ffmpeg -i "{tilted_video}" -c copy "{output_video}" -y'''
            
            success, stdout, stderr = run_cmd(cmd, f"Applying {method_name}")
            
            if success and output_video.exists():
                info = analyze_video(output_video)
                file_size = output_video.stat().st_size
                results[method_name] = {
                    'success': True,
                    'file_size': file_size,
                    'info': info,
                    'description': method_config['description']
                }
                print(f"✅ {method_name}: {file_size} bytes")
            else:
                results[method_name] = {
                    'success': False,
                    'error': stderr,
                    'description': method_config['description']
                }
                print(f"❌ {method_name}: {stderr}")
        
        # Step 4: Analysis and recommendations
        print("\n📊 RESULTS ANALYSIS")
        print("=" * 40)
        
        for method_name, result in results.items():
            if result['success']:
                print(f"✅ {method_name}: {result['description']}")
                print(f"   File size: {result['file_size']:,} bytes")
                if result['info']:
                    print(f"   Resolution: {result['info']['width']}x{result['info']['height']}")
            else:
                print(f"❌ {method_name}: FAILED")
        
        print(f"\n🎯 RECOMMENDATIONS:")
        print(f"1. For slight camera tilt: Use 'rotate' filter with opposite angle")
        print(f"2. For video stabilization: Use 'deshake' filter")
        print(f"3. For perspective issues: Use 'perspective' filter")
        print(f"4. Test these filters in the worker's rotation detection function")
        
        return results

def test_worker_integration():
    """Test how to integrate rotation fixes into the worker"""
    print("\n🔧 WORKER INTEGRATION TESTING")
    print("=" * 50)
    
    # Test the worker's current rotation detection logic
    print("Current worker logic would detect rotation based on:")
    print("1. Stream tags with 'rotate' field")
    print("2. Display Matrix side data")
    print("3. Portrait aspect ratio with mobile encoders")
    
    print("\n💡 PROPOSED ENHANCEMENT:")
    print("Add visual tilt detection and correction:")
    print("- Detect slight rotation using feature matching")
    print("- Apply counter-rotation filter if detected")
    print("- Add user option to disable auto-correction")

if __name__ == "__main__":
    test_rotation_corrections()
    test_worker_integration() 