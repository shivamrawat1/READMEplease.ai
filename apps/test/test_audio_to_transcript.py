import requests

# Endpoint URL for audio to transcript
audio_to_transcript_url = "http://127.0.0.1:5000/audio_to_transcript"

# Path to the audio file
audio_file_path = "output_audio.mp3"

def test_audio_to_transcript():
    """
    Test the /audio_to_transcript endpoint
    """
    print("Testing /audio_to_transcript...")
    with open(audio_file_path, "rb") as audio_file:
        files = {"audio_file": audio_file}
        response = requests.post(audio_to_transcript_url, files=files)

    print("Status Code:", response.status_code)
    try:
        response_data = response.json()
        print("Response JSON:", response_data)

        # Validate word-level timestamps
        if isinstance(response_data, list) and all("word" in entry for entry in response_data):
            print("Word-level timestamps successfully received:")
            for entry in response_data:
                print(f"Word: {entry['word']}, Start: {entry['start']}, End: {entry['end']}")
        else:
            print("Unexpected response format. Check the API implementation.")

    except Exception as e:
        print("Failed to parse response JSON:", e)


if __name__ == "__main__":
    # Test the /audio_to_transcript endpoint
    test_audio_to_transcript()