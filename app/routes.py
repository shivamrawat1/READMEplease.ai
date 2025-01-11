from flask import Blueprint, request, jsonify
import os
from .video_to_audio import convert_video_to_audio
from .audio_to_timestamped_transcript import convert_audio_to_timestamped_transcript


# Define the Blueprint
main = Blueprint('main', __name__)

@main.route('/')
def home():
    return "Welcome to the Flask App"

@main.route('/process_video', methods=['POST'])
def process_video():
    if 'video_file' not in request.files:
        return jsonify({"error": "No video file provided"}), 400

    video_file = request.files['video_file']

    try:
        # Convert video to audio
        audio_path = convert_video_to_audio(video_file)

        # Convert audio to timestamped transcript
        transcript = convert_audio_to_timestamped_transcript(audio_path)

        # Clean up the temporary audio file
        if os.path.exists(audio_path):
            os.remove(audio_path)

        return jsonify({"transcript": transcript}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
