from openai import OpenAI
import json


def select_screenshot_moments(transcript_words: list) -> dict:
    """Select moments for screenshots."""
    try:
        # Always get some screenshots spread throughout the video
        if not transcript_words:
            return {"success": False, "error": "No transcript provided"}

        # Get total duration
        duration = transcript_words[-1]["end"]

        # Take screenshots at regular intervals plus any specifically marked moments
        timestamps = [
            duration * 0.2,  # 20% through
            duration * 0.4,  # 40% through
            duration * 0.6,  # 60% through
            duration * 0.8,  # 80% through
        ]

        return {
            "success": True,
            "timestamps": timestamps,
            "suggestions": "Screenshots will be taken at key points throughout the video"
        }

    except Exception as e:
        return {"success": False, "error": str(e)}
