"""
Video Download Manager

Handles video downloading with robust fallback configurations and error handling.
"""

import logging
import tempfile
import yt_dlp
from pathlib import Path
from typing import Optional, List, Dict, Any

from ..exceptions import DownloadError, FormatNotAvailableError
from ..progress.tracker import ProgressTracker

logger = logging.getLogger(__name__)


class VideoDownloader:
    """Manages video downloading with fallback configurations for robustness"""
    
    def __init__(self, progress_tracker: ProgressTracker):
        self.progress_tracker = progress_tracker
        self.config_attempts = self._build_download_configs()
    
    def _build_download_configs(self) -> List[Dict[str, Any]]:
        """Build a list of yt-dlp configurations to try in order"""
        return [
            # Attempt 1: Default configuration (WORKING as of 2025-01-13)
            {
                'quiet': True,
                'no_warnings': True,
                'writesubtitles': False,
                'writeautomaticsub': False,
                'extract_flat': False,
            },
            # Attempt 2: Updated Android client configuration (2024)
            {
                'quiet': True,
                'no_warnings': True,
                'writesubtitles': False,
                'writeautomaticsub': False,
                'extract_flat': False,
                'extractor_args': {
                    'youtube': {
                        'player_client': ['android_creator'],
                        'skip': ['dash']
                    }
                },
                'http_headers': {
                    'User-Agent': 'com.google.android.apps.youtube.creator/24.47.100 (Linux; U; Android 14; SM-S918B) gzip',
                    'Accept': '*/*',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'DNT': '1',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1'
                }
            },
            # Attempt 3: Web client with modern headers
            {
                'quiet': True,
                'no_warnings': True,
                'writesubtitles': False,
                'writeautomaticsub': False,
                'extract_flat': False,
                'extractor_args': {
                    'youtube': {
                        'player_client': ['web'],
                        'skip': ['dash', 'hls']
                    }
                },
                'http_headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'DNT': '1',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                    'Sec-Fetch-Dest': 'document',
                    'Sec-Fetch-Mode': 'navigate',
                    'Sec-Fetch-Site': 'none',
                    'Sec-Fetch-User': '?1',
                    'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
                    'sec-ch-ua-mobile': '?0',
                    'sec-ch-ua-platform': '"Windows"'
                }
            },
            # Attempt 4: iOS client
            {
                'quiet': True,
                'no_warnings': True,
                'writesubtitles': False,
                'writeautomaticsub': False,
                'extract_flat': False,
                'extractor_args': {
                    'youtube': {
                        'player_client': ['ios']
                    }
                },
                'http_headers': {
                    'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'DNT': '1',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1'
                }
            },
            # Attempt 5: Age-gate bypass attempt with embedded player
            {
                'quiet': True,
                'no_warnings': True,
                'writesubtitles': False,
                'writeautomaticsub': False,
                'extract_flat': False,
                'extractor_args': {
                    'youtube': {
                        'player_client': ['web_embedded'],
                        'skip': ['dash', 'hls']
                    }
                },
                'http_headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Referer': 'https://www.youtube.com/',
                    'Accept': '*/*',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'DNT': '1',
                    'Connection': 'keep-alive'
                }
            }
        ]
    
    def _validate_format_availability(self, url: str, format_id: Optional[str]) -> Optional[str]:
        """
        Validate format availability without downloading
        
        Args:
            url: Video URL
            format_id: Requested format ID
            
        Returns:
            Updated format selector or None if validation fails
        """
        if not format_id or format_id == "None":
            return 'best[height<=720]/best'
        
        try:
            self.progress_tracker.update(5, stage=f"Validating format {format_id}...")
            
            validate_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': False,
            }
            
            with yt_dlp.YoutubeDL(validate_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                if 'entries' in info and info['entries']:
                    info = info['entries'][0]
                
                available_formats = [f.get('format_id') for f in info.get('formats', [])]
                logger.info(f"Available formats: {available_formats[:10]}...")  # Show first 10
                
                if format_id in available_formats:
                    logger.info(f"✅ Format {format_id} is available")
                    return f'{format_id}+bestaudio/{format_id}/best[height<=720]/best'
                else:
                    logger.warning(f"⚠️ Format {format_id} NOT available! Backend provided incorrect format.")
                    return 'best[height<=720]/best'
                    
        except Exception as e:
            logger.warning(f"⚠️ Format validation failed: {e}")
            return f'{format_id}+bestaudio/{format_id}/best[height<=720]/best'
    
    async def download(self, url: str, format_id: Optional[str] = None, temp_dir: Optional[Path] = None) -> Path:
        """
        Download video with fallback configurations
        
        Args:
            url: Video URL to download
            format_id: Optional specific format to download
            temp_dir: Optional temporary directory, creates one if not provided
            
        Returns:
            Path to downloaded video file
            
        Raises:
            DownloadError: If all download attempts fail
            FormatNotAvailableError: If requested format is not available
        """
        if temp_dir is None:
            temp_dir = Path(tempfile.mkdtemp(prefix=f"download_"))
        
        # Build format selector
        format_selector = self._validate_format_availability(url, format_id)
        
        # Define output template
        source_file = temp_dir / f"video.%(ext)s"
        
        download_success = False
        last_error = None
        actual_format_used = None
        
        for i, config in enumerate(self.config_attempts):
            try:
                logger.info(f"🎬 Download attempt {i+1}: Trying config {i+1}")
                
                # Update progress for each attempt
                progress_base = 8 + (i * 3)  # Progress from 8 to 20 across attempts
                self.progress_tracker.update(progress_base, stage=f"Download attempt {i+1}/5...")
                
                # Configure for this attempt
                ydl_opts = config.copy()
                ydl_opts['outtmpl'] = str(source_file)
                ydl_opts['format'] = format_selector
                
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    self.progress_tracker.update(progress_base + 1, stage=f"Extracting video info (attempt {i+1})...")
                    info = ydl.extract_info(url, download=True)
                    
                    # Handle playlist URLs
                    if 'entries' in info and info['entries']:
                        info = info['entries'][0]
                    
                    # Log the actual format that was downloaded
                    actual_format_used = info.get('format_id', 'unknown')
                    actual_resolution = f"{info.get('width', 'unknown')}x{info.get('height', 'unknown')}"
                    requested_format = format_id if format_id and format_id != "None" else "auto"
                    
                    logger.info(f"🎬 Downloaded format: {actual_format_used}, resolution: {actual_resolution}")
                    logger.info(f"🎬 Requested: {requested_format}, Got: {actual_format_used}")
                    
                    if format_id and format_id != "None" and actual_format_used != format_id:
                        logger.warning(f"⚠️ Format mismatch! Requested {format_id}, got {actual_format_used}")
                
                download_success = True
                logger.info(f"✅ Download successful with config {i+1}")
                break
                
            except Exception as e:
                last_error = e
                logger.warning(f"❌ Config {i+1} failed: {str(e)}")
                
                # Special handling for format not available errors
                if "Requested format is not available" in str(e):
                    logger.warning(f"🎬 Format {format_id} confirmed unavailable - backend metadata was wrong")
                
                # Clean up any partial files
                for f in temp_dir.glob("video.*"):
                    try:
                        f.unlink()
                    except:
                        pass
                continue
        
        if not download_success:
            if last_error and "Requested format is not available" in str(last_error):
                raise FormatNotAvailableError(
                    f"Format {format_id} is not available",
                    job_id=self.progress_tracker.job_id,
                    details={"format_id": format_id, "url": url}
                )
            raise DownloadError(
                f"All download attempts failed. Last error: {str(last_error)}",
                job_id=self.progress_tracker.job_id,
                details={"attempts": len(self.config_attempts), "last_error": str(last_error)}
            )
        
        # Find the actual downloaded file
        downloaded_files = list(temp_dir.glob("video.*"))
        if not downloaded_files:
            raise DownloadError(
                "No file downloaded",
                job_id=self.progress_tracker.job_id
            )
        
        source_file = downloaded_files[0]
        
        # Validate downloaded file
        self._validate_downloaded_file(source_file)
        
        logger.info(f"🎬 Download complete: {source_file}")
        return source_file
    
    def _validate_downloaded_file(self, file_path: Path) -> None:
        """
        Validate that the downloaded file is a proper video file
        
        Args:
            file_path: Path to downloaded file
            
        Raises:
            DownloadError: If file validation fails
        """
        logger.info(f"🎬 File validation:")
        logger.info(f"🎬 - Path: {file_path}")
        logger.info(f"🎬 - Extension: {file_path.suffix}")
        
        # Check file existence
        if not file_path.exists():
            raise DownloadError(
                f"Downloaded file does not exist: {file_path}",
                job_id=self.progress_tracker.job_id
            )
        
        # Check file size
        file_size = file_path.stat().st_size
        logger.info(f"🎬 - Size: {file_size:,} bytes ({file_size/1024/1024:.2f} MB)")
        
        if file_size == 0:
            raise DownloadError(
                "Downloaded file is empty",
                job_id=self.progress_tracker.job_id
            )
        
        if file_size < 1024:  # Less than 1KB is suspicious for video
            raise DownloadError(
                f"Downloaded file is too small ({file_size} bytes) - likely not a video",
                job_id=self.progress_tracker.job_id
            )
        
        # Validate that we got a video file, not HTML
        if file_path.suffix.lower() in ['.html', '.mhtml', '.htm']:
            raise DownloadError(
                "Downloaded HTML page instead of video - URL may be unavailable",
                job_id=self.progress_tracker.job_id
            )
        
        # Check for video-like extensions
        valid_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.webm', '.flv', '.m4v']
        if file_path.suffix.lower() not in valid_extensions:
            logger.warning(f"⚠️ Unexpected file extension: {file_path.suffix}. Proceeding with FFmpeg validation.")
        
        logger.info("🎬 ✅ File validation passed") 