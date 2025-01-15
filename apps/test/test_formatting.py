import os
import json
import requests
from pathlib import Path

# Define paths
SAMPLES_DIR = os.path.join(Path(__file__).parent.parent, "samples")
TRANSCRIPTION_FILE = os.path.join(SAMPLES_DIR, "sample_transcription_with_timestamps.json")
SCREENSHOTS_FILE = os.path.join(SAMPLES_DIR, "sample_screenshots.json")
CONVERT_MARKDOWN_URL = "http://127.0.0.1:5000/convert_markdown"

def test_convert_markdown():
    """
    Tests the /convert_markdown endpoint.
    """
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

    # Prepare the request payload
    payload = {
        "transcription": transcription,
        "screenshots": screenshots
    }

    # Make the POST request to the /convert_markdown endpoint
    try:
        response = requests.post(CONVERT_MARKDOWN_URL, json=payload)
        response.raise_for_status()  # Raise an error for HTTP codes >= 400

        # Parse and display the response
        result = response.json()
        if result.get("success"):
            print("Markdown Conversion Successful!")
            print("\nGenerated Markdown:")
            print(result.get("markdown"))
        else:
            print("Conversion failed:", result.get("error"))
    except requests.exceptions.RequestException as e:
        print(f"Error making request to {CONVERT_MARKDOWN_URL}: {e}")

if __name__ == "__main__":
    test_convert_markdown()
