"""
Video Trimming Manager

Handles video trimming with H.264 compatibility, rotation fixes, and smart encoding strategies.
"""

import logging
import subprocess
import json
import time
from pathlib import Path
from typing import Optional

# Try imports with fallback for testing
try:
    from ..exceptions import TrimError, H264DimensionError, FFmpegError
    from ..progress.tracker import ProgressTracker
except ImportError:
    # For testing, create mock classes
    class TrimError(Exception):
        pass

    class H264DimensionError(Exception):
        pass

    class FFmpegError(Exception):
        pass

    class ProgressTracker:
        def __init__(self, *args, **kwargs):
            self.job_id = "test_job"

        def update(self, *args, **kwargs):
            pass


# Try to import from backend app, but handle gracefully for testing
try:
    import sys

    # This path adjustment is handled by the calling script (main.py)
    # sys.path.append('/app/backend')
    from app.config.configuration import get_settings

    settings = get_settings()
except ImportError:
    # This fallback is for isolated testing and won't be used in production
    class settings:
        ffmpeg_path = "ffmpeg"  # Use a generic default for testing
        ffprobe_path = "ffprobe"

    settings = settings()

logger = logging.getLogger(__name__)


class VideoTrimmer:
    """Manages video trimming with rotation correction and smart encoding"""

    def __init__(self, progress_tracker: ProgressTracker):
        self.progress_tracker = progress_tracker
        self.ffmpeg_path = settings.ffmpeg_path
        self.ffprobe_path = settings.ffprobe_path

    def find_nearest_keyframe(self, video_path: Path, timestamp: float) -> float:
        """
        Find the nearest keyframe before or at the given timestamp

        Args:
            video_path: Path to video file
            timestamp: Target timestamp in seconds

        Returns:
            Timestamp of nearest keyframe
        """
        try:
            cmd = [
                self.ffprobe_path,
                "-v",
                "quiet",
                "-select_streams",
                "v:0",
                "-show_entries",
                "frame=pkt_pts_time,key_frame",
                "-of",
                "csv=print_section=0",
                str(video_path),
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, check=True)

            keyframes = []
            for line in result.stdout.strip().split("\n"):
                if line:
                    parts = line.split(",")
                    if len(parts) >= 2 and parts[1] == "1":  # key_frame=1
                        try:
                            keyframe_time = float(parts[0])
                            if keyframe_time <= timestamp:
                                keyframes.append(keyframe_time)
                        except ValueError:
                            continue

            return max(keyframes) if keyframes else 0.0

        except Exception as e:
            logger.warning(f"Failed to find keyframe, using original timestamp: {e}")
            return timestamp

    def detect_video_rotation(self, video_path: Path) -> Optional[str]:
        """
        Detect if video has rotation metadata or visual rotation that needs correction

        Args:
            video_path: Path to video file

        Returns:
            FFmpeg filter string if rotation correction is needed, None otherwise
        """
        try:
            cmd = [
                self.ffprobe_path,
                "-v",
                "quiet",
                "-print_format",
                "json",
                "-show_streams",
                str(video_path),
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            metadata = json.loads(result.stdout)

            for stream in metadata.get("streams", []):
                if stream.get("codec_type") == "video":
                    width = stream.get("width", 0)
                    height = stream.get("height", 0)

                    # Check for rotation in side data (Display Matrix)
                    side_data = stream.get("side_data_list", [])
                    for data in side_data:
                        if data.get("side_data_type") == "Display Matrix":
                            rotation = data.get("rotation", 0)
                            if rotation:
                                logger.info(
                                    f"Found rotation metadata in Display Matrix: {rotation}°"
                                )
                                # Convert rotation to appropriate transpose filter
                                if rotation == 90 or rotation == -270:
                                    return "transpose=2"  # 90° counterclockwise
                                elif rotation == -90 or rotation == 270:
                                    return "transpose=1"  # 90° clockwise
                                elif rotation == 180 or rotation == -180:
                                    return "transpose=1,transpose=1"  # 180°

                    # Check for rotation in stream tags
                    tags = stream.get("tags", {})
                    if "rotate" in tags:
                        rotation = int(tags["rotate"])
                        logger.info(f"Found rotation tag: {rotation}°")
                        if rotation == 90:
                            return "transpose=2"  # 90° counterclockwise
                        elif rotation == -90 or rotation == 270:
                            return "transpose=1"  # 90° clockwise
                        elif rotation == 180:
                            return "transpose=1,transpose=1"  # 180°

                    # Enhanced: Check for visual rotation based on aspect ratio and encoding patterns
                    if height > width and width > 0 and height > 0:
                        aspect_ratio = height / width

                        if (
                            aspect_ratio > 1.5
                        ):  # Very tall aspect ratio suggests rotation issue
                            encoder = tags.get("encoder", "").lower()
                            handler = tags.get("handler_name", "").lower()

                            # YouTube and mobile encoders often have slight visual tilt issues
                            if "google" in handler or "youtube" in handler:
                                logger.info(
                                    f"Detected Google/YouTube video with potential tilt: {width}x{height} from {handler}"
                                )
                                logger.info(
                                    "Applying subtle 0.5° counter-clockwise tilt correction"
                                )
                                return "rotate=-0.5*PI/180:fillcolor=black"
                            elif (
                                "android" in handler
                                or "lavc" in encoder
                                or "x264" in encoder
                            ):
                                if height > width and aspect_ratio > 1.5:
                                    logger.info(
                                        f"Detected mobile portrait content: {width}x{height} from {handler}"
                                    )
                                    logger.info(
                                        "Applying 90° counter-clockwise correction for mobile portrait"
                                    )
                                    return "transpose=2"  # 90° counter-clockwise for true portrait

                    # No rotation correction needed
                    logger.info(
                        f"No rotation correction needed for {width}x{height} video"
                    )
                    return None

        except Exception as e:
            logger.warning(f"Failed to detect rotation: {e}")
            return None

    async def trim(self, input_file: Path, in_ts: float, out_ts: float) -> Path:
        """
        Trim video with H.264 compatibility and rotation fixes

        Args:
            input_file: Path to input video file
            in_ts: Start timestamp in seconds
            out_ts: End timestamp in seconds

        Returns:
            Path to trimmed video file

        Raises:
            TrimError: If trimming fails
            H264DimensionError: If H.264 dimension requirements aren't met
            FFmpegError: If FFmpeg processing fails
        """
        # Validate inputs
        if in_ts < 0:
            logger.warning(f"⚠️ Negative start timestamp: {in_ts}s")
        if out_ts <= in_ts:
            raise TrimError(
                f"Invalid timestamps: end ({out_ts}s) must be greater than start ({in_ts}s)"
            )
        if (out_ts - in_ts) < 0.5:
            logger.warning(f"⚠️ Very short clip duration: {out_ts - in_ts:.3f}s")

        # Analyze input file
        self.progress_tracker.update(30, stage="Analyzing video...")

        try:
            rotation_filter = self.detect_video_rotation(input_file)

            # Apply an extremely subtle 0.5° CCW tilt if no specific rotation metadata found
            if not rotation_filter:
                rotation_filter = "rotate=-0.5*PI/180:fillcolor=black,scale=trunc(iw/2)*2:trunc(ih/2)*2"
                logger.info(
                    "🎬 Applying systematic 0.5° counter-clockwise tilt correction"
                )

            if rotation_filter:
                logger.info(f"🎬 Applying rotation correction: {rotation_filter}")

            # Find keyframes
            logger.info(f"🎬 KEYFRAME ANALYSIS:")
            keyframe_ts = self.find_nearest_keyframe(input_file, in_ts)
            needs_reencode = (
                abs(keyframe_ts - in_ts) > 1.0
            )  # Re-encode if >1s from keyframe

            logger.info(f"🎬 - Requested start: {in_ts}s")
            logger.info(f"🎬 - Nearest keyframe: {keyframe_ts}s")
            logger.info(f"🎬 - Keyframe offset: {abs(keyframe_ts - in_ts):.3f}s")
            logger.info(f"🎬 - Needs re-encode: {needs_reencode}")

            # Determine processing strategy
            if needs_reencode:
                logger.info(f"🎬 STRATEGY: Two-pass processing (re-encode + copy)")
                return await self._trim_with_reencode(
                    input_file, in_ts, out_ts, rotation_filter
                )
            else:
                logger.info(f"🎬 STRATEGY: Single-pass stream copy")
                return await self._trim_with_copy(
                    input_file, in_ts, out_ts, rotation_filter
                )

        except Exception as e:
            if isinstance(e, (TrimError, H264DimensionError, FFmpegError)):
                raise
            raise TrimError(
                f"Video analysis failed: {e}", job_id=self.progress_tracker.job_id
            )

    async def _trim_with_reencode(
        self,
        input_file: Path,
        in_ts: float,
        out_ts: float,
        rotation_filter: Optional[str],
    ) -> Path:
        """Trim video with re-encoding for accurate timestamps"""
        output_file = input_file.parent / f"trimmed_{input_file.stem}.mp4"

        self.progress_tracker.update(35, stage="Starting video processing...")

        # Build FFmpeg command for re-encoding
        cmd_process = [
            self.ffmpeg_path,
            "-ss",
            str(in_ts),
            "-i",
            str(input_file),
            "-t",
            str(out_ts - in_ts),
        ]

        if rotation_filter:
            cmd_process.extend(["-vf", rotation_filter])

        cmd_process.extend(
            [
                "-c:v",
                "libx264",
                "-preset",
                "veryfast",
                "-crf",
                "18",
                "-c:a",
                "aac",
                "-b:a",
                "128k",
                "-avoid_negative_ts",
                "make_zero",
                str(output_file),
                "-y",
            ]
        )

        return await self._execute_ffmpeg(
            cmd_process, output_file, "Re-encoding for accurate timestamp cutting"
        )

    async def _trim_with_copy(
        self,
        input_file: Path,
        in_ts: float,
        out_ts: float,
        rotation_filter: Optional[str],
    ) -> Path:
        """Trim video with stream copy for fast processing"""
        output_file = input_file.parent / f"trimmed_{input_file.stem}.mp4"

        self.progress_tracker.update(35, stage="Starting video processing...")

        # For rotation, we need to re-encode
        if rotation_filter:
            return await self._trim_with_reencode(
                input_file, in_ts, out_ts, rotation_filter
            )

        # Build FFmpeg command for stream copy
        cmd_process = [
            self.ffmpeg_path,
            "-ss",
            str(in_ts),
            "-i",
            str(input_file),
            "-t",
            str(out_ts - in_ts),
            "-c",
            "copy",
            "-avoid_negative_ts",
            "make_zero",
            str(output_file),
            "-y",
        ]

        return await self._execute_ffmpeg(
            cmd_process, output_file, "Stream copy for fast processing"
        )

    async def _execute_ffmpeg(
        self, cmd: list, output_file: Path, description: str
    ) -> Path:
        """
        Execute FFmpeg command with detailed logging and error handling

        Args:
            cmd: FFmpeg command as list
            output_file: Expected output file path
            description: Description for logging

        Returns:
            Path to processed video file

        Raises:
            FFmpegError: If FFmpeg processing fails
        """
        logger.info(f"🎬 FFMPEG COMMAND:")
        logger.info(f"🎬 {' '.join(cmd)}")
        logger.info(f"🎬 Expected output: {output_file}")
        logger.info(f"🎬 ENCODING MODE: {description}")

        self.progress_tracker.update(40, stage="Processing video with FFmpeg...")
        ffmpeg_start = time.time()

        try:
            # Execute FFmpeg with detailed logging
            result = subprocess.run(cmd, capture_output=True, text=True)
            ffmpeg_duration = time.time() - ffmpeg_start

            logger.info(f"🎬 FFmpeg completed in {ffmpeg_duration:.2f}s")

            if result.returncode != 0:
                logger.error(f"🎬 ❌ FFmpeg failed with return code: {result.returncode}")
                logger.error(f"🎬 ❌ FFmpeg command: {' '.join(cmd)}")
                logger.error(f"🎬 ❌ FFmpeg stderr: {result.stderr}")
                logger.error(f"🎬 ❌ FFmpeg stdout: {result.stdout}")

                # Enhanced error reporting
                if "height not divisible by 2" in result.stderr:
                    logger.error(
                        "🎬 ❌ DIMENSION ERROR: Video dimensions are not even (H.264 requirement)"
                    )
                    raise H264DimensionError(
                        "Video dimensions are not even (H.264 requirement)",
                        job_id=self.progress_tracker.job_id,
                        details={"stderr": result.stderr},
                    )
                elif "No such file or directory" in result.stderr:
                    logger.error("🎬 ❌ FILE ERROR: Input file not found or corrupted")
                elif "Invalid data" in result.stderr:
                    logger.error("🎬 ❌ DATA ERROR: Corrupted video stream")

                raise FFmpegError(
                    f"Video processing failed: {result.stderr[:200]}",
                    job_id=self.progress_tracker.job_id,
                    details={"returncode": result.returncode, "stderr": result.stderr},
                )
            else:
                logger.info("🎬 ✅ FFmpeg processing completed successfully")
                self.progress_tracker.update(70, stage="Video processing complete")
                if result.stderr:  # FFmpeg often outputs info to stderr even on success
                    logger.info(
                        f"🎬 FFmpeg info: {result.stderr[-500:]}"
                    )  # Last 500 chars

            # Validate output
            await self._validate_output(
                output_file,
                (out_ts - in_ts)
                if "out_ts" in locals() and "in_ts" in locals()
                else None,
            )

            return output_file

        except subprocess.SubprocessError as e:
            raise FFmpegError(
                f"FFmpeg execution failed: {e}", job_id=self.progress_tracker.job_id
            )

    async def _validate_output(
        self, output_file: Path, expected_duration: Optional[float] = None
    ) -> None:
        """
        Validate the trimmed output file

        Args:
            output_file: Path to output file
            expected_duration: Expected duration in seconds

        Raises:
            TrimError: If validation fails
        """
        self.progress_tracker.update(80, stage="Validating output...")

        logger.info(f"🎬 OUTPUT FILE VALIDATION:")

        if not output_file.exists():
            logger.error(f"🎬 ❌ Output file does not exist: {output_file}")
            raise TrimError(
                "Output file was not created", job_id=self.progress_tracker.job_id
            )

        output_size = output_file.stat().st_size
        logger.info(f"🎬 - File exists: ✅")
        logger.info(
            f"🎬 - File size: {output_size:,} bytes ({output_size/1024/1024:.2f} MB)"
        )

        if output_size == 0:
            logger.error(f"🎬 ❌ Output file is empty!")
            raise TrimError("Output file is empty", job_id=self.progress_tracker.job_id)

        if output_size < 1024:
            logger.warning(f"🎬 ⚠️ Output file is very small: {output_size} bytes")

        # Validate the output file has video content
        try:
            cmd_validate = [
                self.ffprobe_path,
                "-v",
                "quiet",
                "-print_format",
                "json",
                "-show_streams",
                str(output_file),
            ]

            result = subprocess.run(
                cmd_validate, capture_output=True, text=True, check=True
            )
            output_info = json.loads(result.stdout)

            output_video_streams = [
                s
                for s in output_info.get("streams", [])
                if s.get("codec_type") == "video"
            ]
            output_audio_streams = [
                s
                for s in output_info.get("streams", [])
                if s.get("codec_type") == "audio"
            ]

            logger.info(f"🎬 Output validation:")
            logger.info(f"🎬 - Video streams: {len(output_video_streams)}")
            logger.info(f"🎬 - Audio streams: {len(output_audio_streams)}")

            if not output_video_streams:
                logger.error("🎬 ❌ Output file has no video streams!")
                raise TrimError(
                    "Output file contains no video content",
                    job_id=self.progress_tracker.job_id,
                )

            if output_video_streams and expected_duration:
                vs = output_video_streams[0]
                actual_duration = float(vs.get("duration", 0))

                logger.info(
                    f"🎬 - Output resolution: {vs.get('width', '?')}x{vs.get('height', '?')}"
                )
                logger.info(f"🎬 - Output codec: {vs.get('codec_name', 'unknown')}")
                logger.info(f"🎬 - Output duration: {actual_duration:.3f}s")
                logger.info(f"🎬 - Expected duration: {expected_duration:.3f}s")

                # Check for duration mismatch
                duration_diff = abs(actual_duration - expected_duration)
                if duration_diff > 0.5:  # More than 0.5 second difference
                    logger.error(f"🎬 ❌ DURATION MISMATCH!")
                    logger.error(f"🎬 - Expected: {expected_duration:.3f}s")
                    logger.error(f"🎬 - Actual: {actual_duration:.3f}s")
                    logger.error(f"🎬 - Difference: {duration_diff:.3f}s")
                else:
                    logger.info(
                        f"🎬 ✅ Duration matches expected ({duration_diff:.3f}s difference)"
                    )

        except Exception as e:
            logger.warning(f"🎬 Could not validate output file: {e}")
            # Don't fail the job for validation issues, just warn

        logger.info("🎬 ✅ Output validation complete")
