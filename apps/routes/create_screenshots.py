import cv2
import base64
import json
from pathlib import Path
import numpy as np

def create_screenshots_for_keyword(video_path: str, 
                                 transcription_path: str, 
                                 keyword: str) -> dict:
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
        
        # Find all instances of the keyword
        keyword_instances = [
            word for word in transcription 
            if word['word'].lower() == keyword.lower()
        ]
        
        if not keyword_instances:
            return {
                "success": False,
                "error": f"Keyword '{keyword}' not found in transcription",
                "screenshots": []
            }
        
        # Open the video
        video = cv2.VideoCapture(video_path)
        if not video.isOpened():
            return {
                "success": False,
                "error": "Could not open video file",
                "screenshots": []
            }
        
        screenshots = []
        
        # For each instance of the keyword
        for instance in keyword_instances:
            # Get the timestamp
            timestamp = instance['start']
            
            # Set video to the timestamp
            video.set(cv2.CAP_PROP_POS_MSEC, timestamp * 1000)
            
            # Read the frame
            success, frame = video.read()
            if success:
                # Convert frame to jpg format
                _, buffer = cv2.imencode('.jpg', frame)
                # Convert to base64 string
                base64_image = base64.b64encode(buffer).decode('utf-8')
                
                screenshots.append({
                    "timestamp": timestamp,
                    "image_base64": base64_image
                })
        
        video.release()
        
        result = {
            "success": True,
            "keyword": keyword,
            "screenshots": screenshots,
            "video_processed": video_path
        }
        
    except FileNotFoundError:
        result = {
            "success": False,
            "error": "Video or transcription file not found",
            "screenshots": []
        }
    except Exception as e:
        result = {
            "success": False,
            "error": str(e),
            "screenshots": []
        }
    
    return result
