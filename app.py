from flask import Flask, render_template, request, redirect, url_for, session, jsonify, jsonify
import logging
from dotenv import load_dotenv
import os
import tempfile
from pathlib import Path
import json
import cv2

# Import processing functions
from apps.routes.audio_processing import extract_audio
from apps.routes.transcription_with_timestamps import transcribe_audio_with_timestamps
from apps.routes.create_screenshots import create_screenshots_for_keyword
from apps.routes.formatted_file import convert_to_markdown

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create Flask app with custom template folder
app = Flask(__name__,
           template_folder='apps/templates',
           static_folder='apps/static')
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'dev')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB limit

# Global variable to store processing results
processing_results = {}

@app.route('/')
def index():
    return redirect(url_for('upload'))

@app.route('/upload', methods=['GET'])
def upload():
    # Clear any previous results
    session.pop('processing_id', None)
    return render_template('upload.html')

@app.route('/test', methods=['GET'])
def test_route():
    """Test route to verify system components."""
    tests = {
        "flask": True,
        "openai_key": bool(os.getenv('OPENAI_API_KEY')),
        "ffmpeg": bool(os.system('ffmpeg -version') == 0),
        "opencv": bool(cv2.__version__),
        "temp_dir": os.access(tempfile.gettempdir(), os.W_OK)
    }
    return jsonify(tests)

@app.route('/process_video', methods=['POST'])
def process_video():
    logger.debug("Starting video processing")
    if 'video' not in request.files:
        logger.error("No video file uploaded")
        return render_template('upload.html',
                             results={"success": False, "error": "No video file uploaded"})

    video = request.files['video']
    keyword = request.form.get('keyword', '').strip()
    logger.info(f"Processing video for keyword: {keyword}")

    if not keyword:
        logger.error("No keyword provided")
        return render_template('upload.html',
                             results={"success": False, "error": "No keyword provided"})

    try:
        # Create temporary directory for processing
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir_path = Path(temp_dir)
            logger.debug(f"Created temp directory: {temp_dir_path}")

            # Save uploaded video
            video_path = temp_dir_path / "uploaded_video.mp4"
            video.save(video_path)
            logger.debug(f"Saved video to: {video_path}")

            # Extract audio
            audio_path = temp_dir_path / "audio.wav"
            logger.debug("Extracting audio...")
            extract_audio(str(video_path), str(audio_path))

            # Get transcription with timestamps
            logger.debug("Starting transcription...")
            transcription = transcribe_audio_with_timestamps(str(audio_path))

            if not transcription['success']:
                logger.error(f"Transcription failed: {transcription['error']}")
                return render_template('upload.html',
                                    results={"success": False,
                                           "error": f"Transcription failed: {transcription['error']}"})

            # Save transcription to file
            transcription_path = temp_dir_path / "transcription.json"
            with open(transcription_path, 'w') as f:
                json.dump(transcription['words'], f)
            logger.debug("Saved transcription to file")

            # Create screenshots
            logger.debug("Creating screenshots...")
            screenshots = create_screenshots_for_keyword(
                str(video_path),
                str(transcription_path),
                keyword
            )

            logger.info(f"Processing complete. Found {len(screenshots.get('screenshots', []))} screenshots")
            return render_template('upload.html', results=screenshots)

    except Exception as e:
        logger.exception("Error during video processing")
        return render_template('upload.html',
                             results={"success": False, "error": f"Processing error: {str(e)}"})
    

@app.route('/convert_markdown', methods=['POST'])
def convert_markdown():
    """
    Converts transcription and screenshots into Markdown.
    """
    try:
        data = request.get_json()
        logging.debug("Received payload: %s", json.dumps(data, indent=2))
        transcription = data.get("transcription", [])
        screenshots = data.get("screenshots", [])
        
        if not transcription or not screenshots:
            logging.error("Missing transcription or screenshots in payload.")
            return jsonify({"success": False, "error": "Missing transcription or screenshots"}), 400

        markdown = convert_to_markdown(transcription, screenshots)
        logging.debug("Generated Markdown: %s", markdown)

        return jsonify({"success": True, "markdown": markdown}), 200
    except Exception as e:
        logging.exception("Error during Markdown conversion")
        return jsonify({"success": False, "error": str(e)}), 500



if __name__ == '__main__':
    app.run(debug=True,
            host='127.0.0.1',
            port=5000,
            ssl_context='adhoc')