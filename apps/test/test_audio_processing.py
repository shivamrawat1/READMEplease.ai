import os
import sys
from pathlib import Path

# Add the parent directory to Python path to allow imports from apps
project_root = str(Path(__file__).parent.parent.parent)
if project_root not in sys.path:
    sys.path.append(project_root)

from apps.routes.audio_processing import extract_audio

# Path to the video file
video_path = os.path.join(Path(__file__).parent.parent, "samples", "sample_video.mp4")
output_audio_path = os.path.join(Path(__file__).parent.parent, "samples", "sample_audio.wav")

# Test the function
if __name__ == "__main__":
    try:
        result = extract_audio(video_path, output_audio_path)
        print(f"Audio extracted successfully! Saved at: {result}")
    except FileNotFoundError:
        print("The video file was not found. Please check the path.")
    except Exception as e:
        print(f"An error occurred: {e}")

