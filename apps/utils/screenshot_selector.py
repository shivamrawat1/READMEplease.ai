from openai import OpenAI
import json
from .content_analyzer import analyze_content


def select_screenshot_moments(transcript_words: list) -> dict:
    """Select moments for screenshots based on content analysis."""
    try:
        if not transcript_words:
            return {"success": False, "error": "No transcript provided"}

        # Get content analysis
        analysis = analyze_content(transcript_words)
        if not analysis["success"]:
            return analysis

        # Get total duration
        duration = transcript_words[-1]["end"]
        MIN_GAP = 3.0  # Minimum 3 seconds between screenshots

        # Prioritize content-based moments
        timestamps = []
        if analysis["moments"]:
            timestamps = [moment["timestamp"] for moment in analysis["moments"]]

        # If we have too few moments, add some at key points
        if len(timestamps) < 3:
            key_points = [
                duration * 0.2,  # Early section
                duration * 0.5,  # Middle
                duration * 0.8,  # Later section
            ]

            for point in key_points:
                if not any(abs(point - t) < MIN_GAP for t in timestamps):
                    timestamps.append(point)

        # Sort and filter timestamps
        timestamps.sort()
        filtered_timestamps = []
        last_time = -MIN_GAP

        for time in timestamps:
            if time - last_time >= MIN_GAP:
                filtered_timestamps.append(round(time, 2))  # Round to 2 decimal places
                last_time = time

        return {
            "success": True,
            "timestamps": filtered_timestamps,
            "suggestions": f"Selected {len(filtered_timestamps)} key visual moments"
        }

    except Exception as e:
        return {"success": False, "error": str(e)}
