import cv2
import base64
import json
import logging
import re
from pathlib import Path
import numpy as np
import os

logger = logging.getLogger(__name__)


def create_screenshots_for_keyword(
    video_path: str, transcription_path: str, keyword: str
) -> dict:
    """
    Create screenshots from a video at timestamps when a specific keyword is spoken.

    Args:
        video_path (str): Path to the video file
        transcription_path (str): Path to the transcription JSON file with timestamps
        keyword (str): Keyword to search for in the transcription

    Returns:
        dict: Dictionary containing the screenshots and their timestamps
    """
    try:
        # Read the transcription file
        with open(transcription_path, "r") as f:
            transcription = json.load(f)

        # Open the video
        video = cv2.VideoCapture(video_path)
        if not video.isOpened():
            return {"success": False, "error": "Could not open video file"}

        # Get video properties
        total_frames = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = video.get(cv2.CAP_PROP_FPS)
        duration = total_frames / fps

        logger.debug(
            f"Video duration: {duration}s, FPS: {fps}, Total frames: {total_frames}"
        )

        # Create regex pattern for strict word boundary matching
        pattern = r"\b" + re.escape(keyword) + r"\b"
        regex = re.compile(pattern, re.IGNORECASE)

        # Find all instances of the keyword using regex
        keyword_instances = [
            word for word in transcription if regex.search(word["word"])
        ]

        if not keyword_instances:
            return {
                "success": False,
                "error": f"Keyword '{keyword}' not found in transcription",
                "screenshots": [],
            }

        screenshots = []

        for instance in keyword_instances:
            timestamp = float(instance["start"])

            # Check if timestamp is within video bounds
            if timestamp > duration:
                logger.warning(
                    f"Timestamp {timestamp}s exceeds video duration {duration}s"
                )
                continue

            # Calculate frame number
            frame_number = int(timestamp * fps)

            # Set video to the frame
            video.set(cv2.CAP_PROP_POS_FRAMES, frame_number)

            # Read the frame
            success, frame = video.read()
            if success:
                # Resize frame if too large (optional)
                max_size = 800
                height, width = frame.shape[:2]
                if width > max_size or height > max_size:
                    scale = max_size / max(width, height)
                    frame = cv2.resize(frame, None, fx=scale, fy=scale)

                # Convert frame to jpg
                _, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
                base64_image = base64.b64encode(buffer).decode("utf-8")

                screenshots.append(
                    {
                        "timestamp": timestamp,
                        "word_context": instance["word"],
                        "image_base64": base64_image,
                    }
                )
            else:
                logger.error(f"Failed to read frame at timestamp {timestamp}s")

        video.release()

        return {
            "success": True,
            "keyword": keyword,
            "screenshots": screenshots,
            "total_matches": len(screenshots),
            "video_duration": duration,
        }

    except Exception as e:
        logger.exception("Error creating screenshots")
        return {"success": False, "error": str(e), "screenshots": []}


def create_automated_screenshots(video_path: str, timestamps: list) -> list:
    """Create screenshots from a video at specified timestamps."""
    try:
        logger.debug(f"Opening video file: {video_path}")
        if not os.path.exists(video_path):
            logger.error(f"Video file not found: {video_path}")
            return []

        video = cv2.VideoCapture(str(video_path))
        if not video.isOpened():
            logger.error("Failed to open video file with OpenCV")
            return []

        # Get video properties
        fps = video.get(cv2.CAP_PROP_FPS)
        total_frames = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = total_frames / fps

        logger.debug(f"Video stats - FPS: {fps}, Total frames: {total_frames}, Duration: {duration}s")
        screenshots = []

        for timestamp in timestamps:
            try:
                # Ensure timestamp is within video duration
                if timestamp > duration:
                    logger.warning(f"Timestamp {timestamp}s exceeds video duration {duration}s")
                    continue

                frame_number = int(timestamp * fps)
                logger.debug(f"Seeking to frame {frame_number} at timestamp {timestamp}s")

                # Set position and read frame
                video.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
                success, frame = video.read()

                if success:
                    # Process frame
                    height, width = frame.shape[:2]
                    logger.debug(f"Read frame: {width}x{height}")

                    # Resize if needed
                    max_size = 800
                    if width > max_size or height > max_size:
                        scale = max_size / max(width, height)
                        frame = cv2.resize(frame, None, fx=scale, fy=scale)
                        logger.debug(f"Resized frame to {int(width*scale)}x{int(height*scale)}")

                    # Convert to JPG
                    quality = [int(cv2.IMWRITE_JPEG_QUALITY), 85]
                    _, buffer = cv2.imencode('.jpg', frame, quality)
                    if buffer is None:
                        logger.error("Failed to encode frame to JPEG")
                        continue

                    base64_image = base64.b64encode(buffer).decode('utf-8')
                    logger.debug(f"Successfully encoded frame at {timestamp}s")

                    screenshots.append({
                        "timestamp": timestamp,
                        "image_base64": base64_image,
                        "reason": f"Key moment at {timestamp:.2f}s"
                    })
                else:
                    logger.error(f"Failed to read frame at timestamp {timestamp}s")

            except Exception as frame_error:
                logger.exception(f"Error processing frame at {timestamp}s: {str(frame_error)}")
                continue

        video.release()
        logger.info(f"Successfully created {len(screenshots)} screenshots")
        return screenshots

    except Exception as e:
        logger.exception(f"Error in create_automated_screenshots: {str(e)}")
        return []
