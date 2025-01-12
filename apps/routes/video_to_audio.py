import os
import uuid
from flask import Blueprint, request, jsonify
from moviepy.editor import VideoFileClip

# Define the Blueprint
video_to_audio_blueprint = Blueprint('video_to_audio', __name__)

def convert_video_to_audio(video_file):
    """
    Converts a video file to an audio file.
    Returns the path to the generated audio file.
    """
    temp_video_path = None
    temp_audio_path = None

    try:
        # Save the video file temporarily
        temp_video_path = f"/tmp/{uuid.uuid4().hex}.mp4"
        video_file.save(temp_video_path)

        # Extract audio from the video and save to a temporary file
        temp_audio_path = f"/tmp/{uuid.uuid4().hex}.wav"
        clip = VideoFileClip(temp_video_path)
        clip.audio.write_audiofile(temp_audio_path)  # Save audio as a file
        clip.close()

        return temp_audio_path

    except Exception as e:
        raise Exception(f"Error in convert_video_to_audio: {str(e)}")

    finally:
        # Clean up the temporary video file
        if temp_video_path and os.path.exists(temp_video_path):
            os.remove(temp_video_path)


@video_to_audio_blueprint.route('/')
def home():
    return "Welcome to the Video to Audio Flask App"

@video_to_audio_blueprint.route('/video_to_audio_to_transcript', methods=['POST'])
def video_to_audio_to_transcript():
    """
    Endpoint for converting a video file to an audio file and then generating a transcript with timestamps.
    """
    if 'video_file' not in request.files:
        return jsonify({"error": "No video file provided"}), 400

    video_file = request.files['video_file']

    try:
        # Step 1: Convert video to audio
        audio_path = convert_video_to_audio(video_file)

        # Step 2: Generate transcript with timestamps from the audio
        transcript = convert_audio_to_timestamped_transcript(audio_path)

        # Clean up the temporary audio file
        if os.path.exists(audio_path):
            os.remove(audio_path)

        return jsonify({"transcript": transcript}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
