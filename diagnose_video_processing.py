#!/usr/bin/env python3
"""
Video Processing Diagnostic Script - Fix Black/Corrupted Clips

This script identifies and fixes issues in the video processing pipeline
that cause black or corrupted frames in downloaded clips.
"""

import subprocess
import json
import tempfile
import os
from pathlib import Path

def run_cmd(cmd):
    """Run command and return success, stdout, stderr"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=False)
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def analyze_video(video_path):
    """Quick video analysis"""
    cmd = f'ffprobe -v quiet -print_format json -show_streams "{video_path}"'
    success, stdout, stderr = run_cmd(cmd)
    
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
                'codec': stream.get('codec_name'),
                'duration': float(stream.get('duration', 0))
            }
    except:
        pass
    return None

def test_rotation_issue():
    """Test if rotation filter is causing black frames"""
    print("🧪 TESTING ROTATION FILTER ISSUE")
    print("=" * 50)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create test video
        test_video = temp_path / "test.mp4"
        create_cmd = f'ffmpeg -f lavfi -i "testsrc2=size=640x360:duration=5:rate=25" -c:v libx264 -preset fast "{test_video}" -y'
        
        print("📝 Creating test video...")
        success, _, stderr = run_cmd(create_cmd)
        if not success:
            print(f"❌ Failed to create test video: {stderr}")
            return
        
        print("✅ Test video created")
        source_info = analyze_video(str(test_video))
        print(f"📺 Source: {source_info['width']}x{source_info['height']}, {source_info['duration']:.1f}s")
        
        # Test different approaches
        tests = {
            'no_rotation': {
                'cmd': f'ffmpeg -i "{test_video}" -ss 1 -t 3 -c:v libx264 -preset veryfast -crf 18',
                'desc': 'No rotation (baseline)'
            },
            'current_rotation': {
                'cmd': f'ffmpeg -i "{test_video}" -ss 1 -t 3 -vf "rotate=-1*PI/180:fillcolor=black:ow=rotw(-1*PI/180):oh=roth(-1*PI/180)" -c:v libx264 -preset veryfast -crf 18',
                'desc': 'Current rotation filter'
            },
            'simple_rotation': {
                'cmd': f'ffmpeg -i "{test_video}" -ss 1 -t 3 -vf "rotate=-1*PI/180:fillcolor=black" -c:v libx264 -preset veryfast -crf 18',
                'desc': 'Simple rotation'
            },
            'no_filter': {
                'cmd': f'ffmpeg -i "{test_video}" -ss 1 -t 3 -c copy',
                'desc': 'Stream copy (no processing)'
            }
        }
        
        results = {}
        
        for test_name, test_config in tests.items():
            print(f"\n🔧 Testing: {test_config['desc']}")
            output_file = temp_path / f"{test_name}.mp4"
            full_cmd = f"{test_config['cmd']} \"{output_file}\" -y"
            
            success, stdout, stderr = run_cmd(full_cmd)
            
            if success and output_file.exists():
                info = analyze_video(str(output_file))
                file_size = output_file.stat().st_size
                
                if info and file_size > 1000:  # At least 1KB
                    results[test_name] = {
                        'success': True,
                        'size': file_size,
                        'info': info
                    }
                    print(f"✅ {test_name}: {file_size:,} bytes, {info['width']}x{info['height']}")
                else:
                    print(f"❌ {test_name}: Invalid output or too small ({file_size} bytes)")
                    results[test_name] = {'success': False, 'error': 'Invalid output'}
            else:
                print(f"❌ {test_name}: Command failed - {stderr[:100]}")
                results[test_name] = {'success': False, 'error': stderr}
        
        # Analysis
        print(f"\n📊 ANALYSIS")
        print("=" * 30)
        
        baseline = results.get('no_rotation', {})
        baseline_size = baseline.get('size', 0)
        
        for name, result in results.items():
            if result.get('success'):
                size_ratio = result['size'] / baseline_size if baseline_size > 0 else 0
                if size_ratio < 0.1:
                    print(f"🚨 {name}: BLACK FRAMES DETECTED (size ratio: {size_ratio:.3f})")
                elif size_ratio < 0.5:
                    print(f"⚠️  {name}: Quality issues (size ratio: {size_ratio:.3f})")
                else:
                    print(f"✅ {name}: Normal output (size ratio: {size_ratio:.3f})")
            else:
                print(f"❌ {name}: Failed")
        
        return results

def recommend_fix():
    """Provide specific fix recommendations"""
    print("\n🎯 RECOMMENDED FIXES")
    print("=" * 40)
    
    print("1. 🔧 IMMEDIATE FIX: Disable rotation temporarily")
    print("   Comment out the rotation filter application in worker/process_clip.py")
    print("   Lines 598-603: The systematic tilt correction")
    
    print("\n2. 🔧 BETTER FIX: Use video stabilization instead")
    print("   Replace rotation filter with: 'deshake=rx=8:ry=8'")
    print("   This provides stabilization without the cropping issues")
    
    print("\n3. 🔧 ADVANCED FIX: Conditional rotation")
    print("   Only apply rotation if video actually has rotation metadata")
    print("   Remove the universal -1° correction")
    
    print("\n4. 🔧 SAFEST FIX: Make rotation user-configurable")
    print("   Add a checkbox in the UI to enable/disable rotation correction")
    print("   Default to disabled until the issue is properly resolved")

def generate_fix_script():
    """Generate a script to apply the fix"""
    fix_script = """#!/bin/bash
# Quick fix for black video frames

echo "🔧 Applying fix for black video frames..."

# Create backup
cp worker/process_clip.py worker/process_clip.py.backup

# Comment out the problematic rotation filter
sed -i 's/rotation_filter = .rotate/#rotation_filter = .rotate/' worker/process_clip.py

# Restart worker
docker-compose restart worker

echo "✅ Fix applied. Test with a video clip."
echo "To restore: cp worker/process_clip.py.backup worker/process_clip.py"
"""
    
    with open('fix_black_frames.sh', 'w') as f:
        f.write(fix_script)
    
    print(f"\n📝 Generated fix script: fix_black_frames.sh")
    print("Run: chmod +x fix_black_frames.sh && ./fix_black_frames.sh")

def main():
    """Main diagnostic function"""
    print("🔍 VIDEO PROCESSING DIAGNOSTIC")
    print("Investigating black/corrupted clip issues...")
    print("=" * 60)
    
    # Test rotation filter
    results = test_rotation_issue()
    
    # Analyze results
    if results:
        current_rotation_result = results.get('current_rotation', {})
        no_rotation_result = results.get('no_rotation', {})
        
        if not current_rotation_result.get('success') and no_rotation_result.get('success'):
            print("\n🚨 ROOT CAUSE IDENTIFIED: ROTATION FILTER")
            print("The current rotation filter is causing black frames!")
        elif current_rotation_result.get('success'):
            print("\n🤔 ROTATION FILTER WORKS IN ISOLATION")
            print("The issue might be in the integration with other parameters")
        else:
            print("\n⚠️  BROADER FFMPEG ISSUE")
            print("The problem might be with FFmpeg parameters or environment")
    
    # Provide recommendations
    recommend_fix()
    
    # Generate fix script
    generate_fix_script()

if __name__ == "__main__":
    main() 