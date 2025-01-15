import os
import sys
import json
from pathlib import Path

# Add the parent directory to Python path to allow imports from apps
project_root = str(Path(__file__).parent.parent.parent)
if project_root not in sys.path:
    sys.path.append(project_root)

from apps.routes.transcription_with_timestamps import transcribe_audio_with_timestamps

# Define paths
SAMPLES_DIR = os.path.join(Path(__file__).parent.parent, "samples")
AUDIO_FILE = os.path.join(SAMPLES_DIR, "sample_audio.wav")
OUTPUT_FILE = os.path.join(SAMPLES_DIR, "sample_transcription_with_timestamps.json")

def main():
    print(f"Processing audio file: {AUDIO_FILE}")
    
    # Check if input file exists
    if not os.path.exists(AUDIO_FILE):
        print(f"Error: Audio file not found at {AUDIO_FILE}")
        return
    
    # Process the audio file
    result = transcribe_audio_with_timestamps(AUDIO_FILE)
    
    if result["success"]:
        # Save only the words array to match the desired format
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(result["words"], f, indent=2, ensure_ascii=False)
        
        print(f"\nTranscription completed!")
        print(f"Output saved to: {OUTPUT_FILE}")
        print("\nFirst few words with timestamps:")
        print(json.dumps(result["words"][:5], indent=2, ensure_ascii=False))
    else:
        print(f"\nError during transcription:")
        print(result["error"])

if __name__ == "__main__":
    main() 