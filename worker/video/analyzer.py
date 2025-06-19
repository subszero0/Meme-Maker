"""
Video Analysis Manager

Handles video metadata extraction, validation, and title extraction.
"""

import logging
import subprocess
import json
import re
import yt_dlp
from pathlib import Path
from typing import Dict, Any, Optional

from ..exceptions import VideoAnalysisError
from ..progress.tracker import ProgressTracker

logger = logging.getLogger(__name__)


class VideoAnalyzer:
    """Manages video analysis, metadata extraction, and validation"""
    
    def __init__(self, progress_tracker: ProgressTracker):
        self.progress_tracker = progress_tracker
    
    def extract_video_title(self, url: str) -> str:
        """
        Extract video title from URL using yt-dlp
        
        Args:
            url: Video URL
            
        Returns:
            Sanitized video title suitable for filename
        """
        try:
            self.progress_tracker.update(2, stage="Extracting video title...")
            
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': False,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                # Handle playlist URLs
                if 'entries' in info and info['entries']:
                    info = info['entries'][0]
                
                title = info.get('title', '').strip()
                if title:
                    sanitized_title = self.sanitize_filename(title)
                    logger.info(f"🎬 Extracted title: '{title}' -> '{sanitized_title}'")
                    return sanitized_title
                else:
                    logger.warning("🎬 No title found, using default")
                    return 'video'
                    
        except Exception as e:
            logger.warning(f"🎬 Failed to extract title: {e}")
            return 'video'
    
    def sanitize_filename(self, title: str, max_length: int = 100) -> str:
        """
        Sanitize a video title for use as a filename
        
        Args:
            title: Raw video title
            max_length: Maximum filename length
            
        Returns:
            Sanitized filename-safe string
        """
        if not title or title.strip() == '':
            return 'video'
        
        # Remove or replace problematic characters
        sanitized = re.sub(r'[<>:"/\\|?*]', '_', title)  # Replace invalid filename chars
        sanitized = re.sub(r'[^\w\s\-_\.\(\)\[\]]', '', sanitized)  # Keep only safe chars
        sanitized = re.sub(r'\s+', '_', sanitized)  # Replace spaces with underscores
        sanitized = re.sub(r'_{2,}', '_', sanitized)  # Replace multiple underscores with single
        sanitized = sanitized.strip('_')  # Remove leading/trailing underscores
        
        # Limit length and ensure it's not empty
        if len(sanitized) > max_length:
            sanitized = sanitized[:max_length].rstrip('_')
        
        return sanitized if sanitized else 'video'
    
    async def analyze_video_file(self, video_path: Path) -> Dict[str, Any]:
        """
        Analyze video file using ffprobe to extract metadata
        
        Args:
            video_path: Path to video file
            
        Returns:
            Dictionary containing video metadata
            
        Raises:
            VideoAnalysisError: If analysis fails
        """
        try:
            self.progress_tracker.update(25, stage="Analyzing video...")
            
            cmd = [
                'ffprobe',
                '-v', 'quiet',
                '-print_format', 'json', 
                '-show_streams',
                '-show_format',
                str(video_path)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            video_info = json.loads(result.stdout)
            
            # Extract relevant information
            video_streams = [s for s in video_info.get('streams', []) if s.get('codec_type') == 'video']
            audio_streams = [s for s in video_info.get('streams', []) if s.get('codec_type') == 'audio']
            
            analysis_result = {
                'file_path': str(video_path),
                'file_size': video_path.stat().st_size,
                'video_streams': len(video_streams),
                'audio_streams': len(audio_streams),
                'format_info': video_info.get('format', {}),
                'streams': video_info.get('streams', [])
            }
            
            # Log stream information
            logger.info(f"🎬 Source analysis:")
            logger.info(f"🎬 - Video streams: {len(video_streams)}")
            logger.info(f"🎬 - Audio streams: {len(audio_streams)}")
            
            if video_streams:
                vs = video_streams[0]
                analysis_result.update({
                    'video_codec': vs.get('codec_name', 'unknown'),
                    'width': vs.get('width', 0),
                    'height': vs.get('height', 0),
                    'frame_rate': vs.get('avg_frame_rate', 'unknown'),
                    'pixel_format': vs.get('pix_fmt', 'unknown'),
                    'duration': float(vs.get('duration', 0))
                })
                
                logger.info(f"🎬 - Video codec: {vs.get('codec_name', 'unknown')}")
                logger.info(f"🎬 - Resolution: {vs.get('width', '?')}x{vs.get('height', '?')}")
                logger.info(f"🎬 - Frame rate: {vs.get('avg_frame_rate', 'unknown')}")
                logger.info(f"🎬 - Pixel format: {vs.get('pix_fmt', 'unknown')}")
                
                # Check if we actually have video content
                if vs.get('codec_name') == 'none' or vs.get('width', 0) == 0:
                    logger.error("🎬 ❌ Video stream appears to be empty or invalid!")
                    raise VideoAnalysisError(
                        "Video stream is empty or invalid",
                        job_id=self.progress_tracker.job_id,
                        details=analysis_result
                    )
            else:
                logger.error("🎬 ❌ No video streams found in file!")
                raise VideoAnalysisError(
                    "No video streams found in file",
                    job_id=self.progress_tracker.job_id,
                    details=analysis_result
                )
                
            if audio_streams:
                aud = audio_streams[0]
                analysis_result.update({
                    'audio_codec': aud.get('codec_name', 'unknown'),
                    'sample_rate': aud.get('sample_rate', 'unknown')
                })
                logger.info(f"🎬 - Audio codec: {aud.get('codec_name', 'unknown')}")
                logger.info(f"🎬 - Sample rate: {aud.get('sample_rate', 'unknown')}")
            
            return analysis_result
            
        except subprocess.CalledProcessError as e:
            logger.error(f"🎬 Failed to analyze video file: {e}")
            raise VideoAnalysisError(
                f"Cannot analyze video file: {e}",
                job_id=self.progress_tracker.job_id,
                details={"stderr": e.stderr if hasattr(e, 'stderr') else str(e)}
            )
        except json.JSONDecodeError as e:
            logger.error(f"🎬 Failed to parse ffprobe output: {e}")
            raise VideoAnalysisError(
                f"Cannot parse video analysis results: {e}",
                job_id=self.progress_tracker.job_id
            )
        except Exception as e:
            logger.warning(f"🎬 Video analysis warning: {e}")
            raise VideoAnalysisError(
                f"Video analysis failed: {e}",
                job_id=self.progress_tracker.job_id
            ) 