import os
import sys
import json
from pathlib import Path
import base64

# Add the parent directory to Python path to allow imports from apps
project_root = str(Path(__file__).parent.parent.parent)
if project_root not in sys.path:
    sys.path.append(project_root)

from apps.routes.create_screenshots import create_screenshots_for_keyword

# Define paths
SAMPLES_DIR = os.path.join(Path(__file__).parent.parent, "samples")
VIDEO_FILE = os.path.join(SAMPLES_DIR, "sample_video.mp4")
TRANSCRIPTION_FILE = os.path.join(SAMPLES_DIR, "sample_transcription_with_timestamps.json")
OUTPUT_FILE = os.path.join(SAMPLES_DIR, "sample_screenshots.json")

def main():
    print(f"Processing video file: {VIDEO_FILE}")
    print(f"Using transcription from: {TRANSCRIPTION_FILE}")
    
    # Check if input files exist
    if not os.path.exists(VIDEO_FILE):
        print(f"Error: Video file not found at {VIDEO_FILE}")
        return
    if not os.path.exists(TRANSCRIPTION_FILE):
        print(f"Error: Transcription file not found at {TRANSCRIPTION_FILE}")
        return
    
    # Example keyword - you can change this to any word you want to search for
    keyword = "the"
    
    # Process the video
    result = create_screenshots_for_keyword(
        VIDEO_FILE,
        TRANSCRIPTION_FILE,
        keyword
    )
    
    if result["success"]:
        # Save the results
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        print(f"\nScreenshots created successfully!")
        print(f"Output saved to: {OUTPUT_FILE}")
        print(f"\nFound {len(result['screenshots'])} instances of the keyword '{keyword}'")
        print("Timestamps of screenshots:")
        for screenshot in result['screenshots']:
            print(f"- {screenshot['timestamp']} seconds")
    else:
        print(f"\nError during processing:")
        print(result["error"])

if __name__ == "__main__":
    main() 