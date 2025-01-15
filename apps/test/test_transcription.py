import os
import sys
import json
from pathlib import Path

# Add the parent directory to Python path to allow imports from apps
project_root = str(Path(__file__).parent.parent.parent)
if project_root not in sys.path:
    sys.path.append(project_root)

from apps.routes.transcription import transcribe_audio

# Define paths
SAMPLES_DIR = os.path.join(Path(__file__).parent.parent, "samples")
AUDIO_FILE = os.path.join(SAMPLES_DIR, "sample_audio.wav")
OUTPUT_FILE = os.path.join(SAMPLES_DIR, "sample_transcript.json")

def main():
    print(f"Processing audio file: {AUDIO_FILE}")
    
    # Check if input file exists
    if not os.path.exists(AUDIO_FILE):
        print(f"Error: Audio file not found at {AUDIO_FILE}")
        return
    
    # Process the audio file
    result = transcribe_audio(AUDIO_FILE)
    
    # Save the results
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    print(f"\nTranscription completed!")
    print(f"Output saved to: {OUTPUT_FILE}")
    print("\nTranscription result:")
    print(json.dumps(result, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main() 