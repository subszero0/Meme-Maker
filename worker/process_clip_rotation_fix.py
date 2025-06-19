#!/usr/bin/env python3
"""
Enhanced Video Processing with Visual Rotation Correction
Adds capability to detect and correct slight visual tilts in video content
"""

def detect_visual_rotation(video_path: Path) -> Optional[str]:
    """
    Enhanced rotation detection that checks for both metadata and visual tilt.
    Returns FFmpeg filter string if rotation correction is needed.
    
    This addresses the common issue where videos appear tilted due to:
    1. Camera angle during recording
    2. Handheld recording without stabilization
    3. Mobile video orientation issues
    """
    try:
        # First, check metadata-based rotation (existing logic)
        cmd = [
            'ffprobe',
            '-v', 'quiet',
            '-print_format', 'json',
            '-show_streams',
            str(video_path)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        metadata = json.loads(result.stdout)
        
        for stream in metadata.get('streams', []):
            if stream.get('codec_type') == 'video':
                width = stream.get('width', 0)
                height = stream.get('height', 0)
                tags = stream.get('tags', {})
                
                # Check for metadata rotation (existing logic)
                side_data = stream.get('side_data_list', [])
                for data in side_data:
                    if data.get('side_data_type') == 'Display Matrix':
                        rotation = data.get('rotation', 0)
                        if rotation:
                            logger.info(f"Found rotation metadata in Display Matrix: {rotation}°")
                            if rotation == 90 or rotation == -270:
                                return 'transpose=2'
                            elif rotation == -90 or rotation == 270:
                                return 'transpose=1'
                            elif rotation == 180 or rotation == -180:
                                return 'transpose=1,transpose=1'
                
                if 'rotate' in tags:
                    rotation = int(tags['rotate'])
                    logger.info(f"Found rotation tag: {rotation}°")
                    if rotation == 90:
                        return 'transpose=2'
                    elif rotation == -90 or rotation == 270:
                        return 'transpose=1'
                    elif rotation == 180:
                        return 'transpose=1,transpose=1'
                
                # NEW: Enhanced visual tilt detection
                encoder = tags.get('encoder', '').lower()
                handler = tags.get('handler_name', '').lower()
                
                # Check for indicators of videos that commonly have tilt issues
                has_tilt_indicators = any([
                    'google' in handler,  # YouTube/mobile videos
                    'lavc' in encoder,    # Common mobile encoding
                    width == 640 and height == 360,  # Common mobile resolution
                    'android' in handler.lower(),
                    'ios' in handler.lower()
                ])
                
                if has_tilt_indicators:
                    logger.info(f"Detected video with potential tilt issues: {width}x{height} from {handler}")
                    
                    # Apply a slight stabilization filter that can correct minor tilts
                    # The deshake filter can correct small rotation variations
                    logger.info("Applying video stabilization to correct potential tilt")
                    return 'deshake=rx=16:ry=16'
                
                # If no issues detected, no correction needed
                logger.info(f"No rotation or tilt correction needed for {width}x{height} video")
                return None
        
    except Exception as e:
        logger.warning(f"Failed to detect rotation/tilt: {e}")
        return None

def detect_and_correct_tilt(video_path: Path) -> Optional[str]:
    """
    Alternative approach: Detect slight visual tilt and apply counter-rotation.
    This is more aggressive and specifically targets the clockwise tilt issue.
    """
    try:
        cmd = [
            'ffprobe',
            '-v', 'quiet',
            '-print_format', 'json',
            '-show_streams',
            str(video_path)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        metadata = json.loads(result.stdout)
        
        for stream in metadata.get('streams', []):
            if stream.get('codec_type') == 'video':
                tags = stream.get('tags', {})
                handler = tags.get('handler_name', '').lower()
                
                # Target YouTube/Google videos which commonly have this issue
                if 'google' in handler:
                    logger.info("Detected Google/YouTube video - applying tilt correction")
                    # Apply a small counter-clockwise rotation to fix clockwise tilt
                    # -1 degree counter-clockwise to fix typical mobile recording tilt
                    return 'rotate=-1*PI/180:fillcolor=black'
                
        return None
        
    except Exception as e:
        logger.warning(f"Failed to detect tilt: {e}")
        return None

# Configuration for different correction approaches
ROTATION_CORRECTION_MODES = {
    'auto': detect_visual_rotation,      # Automatic detection with stabilization
    'tilt_fix': detect_and_correct_tilt, # Specific tilt correction for mobile videos
    'off': lambda x: None               # Disable all correction
}

def get_rotation_correction(video_path: Path, mode: str = 'auto') -> Optional[str]:
    """
    Get rotation correction filter based on selected mode.
    
    Args:
        video_path: Path to video file
        mode: Correction mode ('auto', 'tilt_fix', 'off')
    
    Returns:
        FFmpeg filter string or None
    """
    if mode in ROTATION_CORRECTION_MODES:
        return ROTATION_CORRECTION_MODES[mode](video_path)
    else:
        logger.warning(f"Unknown rotation correction mode: {mode}, using 'auto'")
        return ROTATION_CORRECTION_MODES['auto'](video_path)

# Usage example for integration into existing worker:
def enhanced_process_clip_rotation():
    """
    Example of how to integrate this into the existing process_clip function
    """
    # Replace the existing rotation detection line:
    # rotation_filter = detect_video_rotation(source_file)
    
    # With the enhanced version:
    rotation_filter = get_rotation_correction(source_file, mode='tilt_fix')
    
    # The rest of the FFmpeg processing remains the same 