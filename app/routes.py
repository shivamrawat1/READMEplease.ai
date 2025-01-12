from flask import Blueprint, request, jsonify
import os
from .video_to_audio import convert_video_to_audio
from .audio_to_timestamped_transcript import convert_audio_to_timestamped_transcript

# Define the Blueprint
main = Blueprint('main', __name__)

@main.route('/')
def home():
    return "Welcome to the Flask App"

@main.route('/video_to_audio', methods=['POST'])
def video_to_audio():
    """
    Endpoint for converting a video file to an audio file.
    """
    if 'video_file' not in request.files:
        return jsonify({"error": "No video file provided"}), 400

    video_file = request.files['video_file']

    try:
        # Convert video to audio
        audio_path = convert_video_to_audio(video_file)

        return jsonify({"audio_path": audio_path}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@main.route('/audio_to_transcript', methods=['POST'])
def audio_to_transcript():
    """
    Endpoint for converting an audio file to a timestamped transcript.
    """
    if 'audio_file' not in request.files:
        return jsonify({"error": "No audio file provided"}), 400

    audio_file = request.files['audio_file']

    # Save the uploaded audio file temporarily
    temp_audio_path = f"/tmp/{audio_file.filename}"
    audio_file.save(temp_audio_path)

    try:
        # Convert audio to timestamped transcript
        transcript = convert_audio_to_timestamped_transcript(temp_audio_path)

        # Clean up the temporary audio file
        if os.path.exists(temp_audio_path):
            os.remove(temp_audio_path)

        return jsonify({"transcript": transcript}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500