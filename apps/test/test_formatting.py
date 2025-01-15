import os
import json
import requests
from pathlib import Path
import time

# Define paths
SAMPLES_DIR = os.path.join(Path(__file__).parent.parent, "samples")
TRANSCRIPTION_FILE = os.path.join(SAMPLES_DIR, "sample_transcription_with_timestamps.json")
SCREENSHOTS_FILE = os.path.join(SAMPLES_DIR, "sample_screenshots.json")
CONVERT_MARKDOWN_URL = "https://127.0.0.1:5000/convert_markdown"



def save_debug_info(filename, data):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    print(f"Saved debug info to {filename}")

def save_markdown_to_file(markdown_content, filename="generated_markdown.md"):
    with open(filename, "w", encoding="utf-8") as f:
        f.write(markdown_content)
    print(f"Generated Markdown saved to {filename}")

def test_convert_markdown():
    print("Testing /convert_markdown endpoint...")


    # Verify sample files exist
    if not os.path.exists(TRANSCRIPTION_FILE):
        print(f"Error: Transcription file not found at {TRANSCRIPTION_FILE}")
        return

    if not os.path.exists(SCREENSHOTS_FILE):
        print(f"Error: Screenshots file not found at {SCREENSHOTS_FILE}")
        return

    # Load transcription and screenshots data
    with open(TRANSCRIPTION_FILE, "r", encoding="utf-8") as f:
        transcription = json.load(f)

    with open(SCREENSHOTS_FILE, "r", encoding="utf-8") as f:
        screenshots = json.load(f)

    payload = {"transcription": transcription, "screenshots": screenshots}

    try:
        start_time = time.time()
        response = requests.post(CONVERT_MARKDOWN_URL, json=payload,verify=False, timeout=120)
        response.raise_for_status()
        print(f"Request completed in {time.time() - start_time:.2f} seconds.")

        result = response.json()
        save_debug_info("response_debug.json", result)

        if result.get("success"):
            print("Markdown Conversion Successful!")
            save_markdown_to_file(result.get("markdown"))
        else:
            print("Conversion failed:", result.get("error"))
    except requests.exceptions.RequestException as e:
        print(f"Error making request to {CONVERT_MARKDOWN_URL}: {e}")

if __name__ == "__main__":
    test_convert_markdown()
