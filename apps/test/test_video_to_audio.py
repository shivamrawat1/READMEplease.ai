import requests
import os

# Get the current directory of the script
current_dir = os.path.dirname(os.path.abspath(__file__))

# Construct the path to the video file (going up to project root then to videos folder)
video_file_path = "/Users/cvk/Downloads/[CODE] Local Projects/nosuai/videos/financial_literacy_1min.MP4"

# Verify if file exists
if not os.path.exists(video_file_path):
    raise FileNotFoundError(f"Video file not found at: {video_file_path}")

# Define the API endpoint - make sure it matches your Flask route
video_to_audio_url = "http://127.0.0.1:5000/video_to_audio"  # This should match the blueprint route

def test_video_to_audio():
    """
    Test the /video_to_audio endpoint
    """
    print(f"Testing endpoint: {video_to_audio_url}")
    print(f"Using video file: {video_file_path}")
    with open(video_file_path, "rb") as video_file:
        files = {"video_file": video_file}
        response = requests.post(video_to_audio_url, files=files)  # Use the API endpoint here

    print("Status Code:", response.status_code)
    try:
        response_data = response.json()
        print("Response JSON:", response_data)

        # Check audio path
        audio_path = response_data.get("audio_path")
        if audio_path:
            print(f"Audio Path: {audio_path}")
            # Check if the file exists in the temporary directory
            if os.path.exists(audio_path):
                # Save the file locally
                saved_audio_path = os.path.join(current_dir, 'output_audio.wav')
                with open(audio_path, 'rb') as temp_audio_file:
                    with open(saved_audio_path, 'wb') as output_audio_file:
                        output_audio_file.write(temp_audio_file.read())
                print(f"Audio file saved at: {saved_audio_path}")

        # Check transcription
        # transcription = response_data.get("transcription")
        # if transcription:
        #     print("\nTranscription Results:")
        #     for word in transcription:
        #         print(f"Word: {word['word']}, Start: {word['start']}, End: {word['end']}")

        return response_data

    except Exception as e:
        print("Failed to parse response JSON:", e)
        return None


if __name__ == "__main__":
    # Test the /video_to_audio endpoint
    audio_file_path = test_video_to_audio()
    if not audio_file_path:
        print("Video to audio conversion failed.")
    else:
        print(f"Audio file saved at: {audio_file_path}")
