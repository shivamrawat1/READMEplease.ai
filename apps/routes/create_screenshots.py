import cv2
import base64
import json
import logging
from pathlib import Path
import numpy as np

logger = logging.getLogger(__name__)

def create_screenshots_for_keyword(video_path: str, transcription_path: str, keyword: str) -> dict:
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
        with open(transcription_path, 'r') as f:
            transcription = json.load(f)

        # Open the video
        video = cv2.VideoCapture(video_path)
        if not video.isOpened():
            return {"success": False, "error": "Could not open video file"}

        # Get video properties
        total_frames = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = video.get(cv2.CAP_PROP_FPS)
        duration = total_frames / fps

        logger.debug(f"Video duration: {duration}s, FPS: {fps}, Total frames: {total_frames}")

        # Find all instances of the keyword
        keyword_instances = [
            word for word in transcription
            if keyword.lower() in word['word'].lower()
        ]

        if not keyword_instances:
            return {
                "success": False,
                "error": f"Keyword '{keyword}' not found in transcription",
                "screenshots": []
            }

        screenshots = []

        for instance in keyword_instances:
            timestamp = float(instance['start'])

            # Check if timestamp is within video bounds
            if timestamp > duration:
                logger.warning(f"Timestamp {timestamp}s exceeds video duration {duration}s")
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
                _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
                base64_image = base64.b64encode(buffer).decode('utf-8')

                screenshots.append({
                    "timestamp": timestamp,
                    "word_context": instance['word'],
                    "image_base64": base64_image
                })
            else:
                logger.error(f"Failed to read frame at timestamp {timestamp}s")

        video.release()

        return {
            "success": True,
            "keyword": keyword,
            "screenshots": screenshots,
            "total_matches": len(screenshots),
            "video_duration": duration
        }

    except Exception as e:
        logger.exception("Error creating screenshots")
        return {
            "success": False,
            "error": str(e),
            "screenshots": []
        }
