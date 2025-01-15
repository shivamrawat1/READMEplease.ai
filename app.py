from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import logging
from dotenv import load_dotenv
import os
import tempfile
from pathlib import Path
import cv2

# Import processing functions
from apps.routes.audio_processing import extract_audio
from apps.routes.transcription_with_timestamps import transcribe_audio_with_timestamps
from apps.routes.create_screenshots import create_automated_screenshots
from apps.utils.blog_generator import generate_blog_from_transcript
from apps.utils.screenshot_selector import select_screenshot_moments
from apps.utils.content_merger import generate_blog_html  # Remove merge_content_with_screenshots

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create Flask app with custom template folder
app = Flask(__name__, template_folder="apps/templates", static_folder="apps/static")
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev")

# Global variable to store processing results
processing_results = {}


@app.route("/")
def index():
    return redirect(url_for("upload"))


@app.route("/upload", methods=["GET"])
def upload():
    # Clear any previous results
    session.pop("processing_id", None)
    return render_template("upload.html")


@app.route("/test", methods=["GET"])
def test_route():
    """Test route to verify system components."""
    tests = {
        "flask": True,
        "openai_key": bool(os.getenv("OPENAI_API_KEY")),
        "ffmpeg": bool(os.system("ffmpeg -version") == 0),
        "opencv": bool(cv2.__version__),
        "temp_dir": os.access(tempfile.gettempdir(), os.W_OK),
    }
    return jsonify(tests)


@app.route("/process_video", methods=["POST"])
def process_video():
    logger.debug("Starting video processing")
    if "video" not in request.files:
        return render_template(
            "upload.html", results={"success": False, "error": "No video file uploaded"}
        )

    video = request.files["video"]

    # Check file size (25MB limit for Whisper API)
    MAX_FILE_SIZE = 25 * 1024 * 1024  # 25MB in bytes
    video.seek(0, os.SEEK_END)
    size = video.tell()
    video.seek(0)

    if size > MAX_FILE_SIZE:
        return render_template(
            "upload.html",
            results={"success": False, "error": "Video file too large (max 25MB)"},
        )

    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir_path = Path(temp_dir)
            video_path = temp_dir_path / "uploaded_video.mp4"
            video.save(video_path)

            # Extract audio with compression for large files
            audio_path = temp_dir_path / "audio.wav"
            extract_audio(str(video_path), str(audio_path), max_size_mb=25)

            # Get transcription with timestamps
            transcription = transcribe_audio_with_timestamps(str(audio_path))

            if not transcription["success"]:
                return render_template(
                    "upload.html",
                    results={
                        "success": False,
                        "error": f"Transcription failed: {transcription['error']}",
                    },
                )

            # Get screenshots based on content analysis first
            screenshot_suggestions = select_screenshot_moments(transcription["words"])
            screenshots = []

            logger.debug("Starting content-based screenshot generation")
            if screenshot_suggestions["success"] and screenshot_suggestions.get("timestamps"):
                logger.debug(f"Found {len(screenshot_suggestions['timestamps'])} meaningful moments")
                screenshots = create_automated_screenshots(
                    str(video_path),
                    screenshot_suggestions["timestamps"]
                )

            # Generate blog content with actual timestamps
            full_transcript = " ".join([word["word"] for word in transcription["words"]])
            blog_result = generate_blog_from_transcript(
                full_transcript,
                timestamps=[s["timestamp"] for s in screenshots]
            )

            if not blog_result["success"]:
                return render_template(
                    "upload.html",
                    results={
                        "success": False,
                        "error": f"Blog generation failed: {blog_result.get('error', 'Unknown error')}",
                    },
                )

            # Generate complete HTML blog with embedded screenshots
            blog_html = generate_blog_html(blog_result["blog_content"], screenshots)

            results = {
                "success": True,
                "blog_content": blog_html,
                "has_screenshots": len(screenshots) > 0,
                "screenshot_count": len(screenshots)  # Add this for debugging
            }

            return render_template("upload.html", results=results)

    except Exception as e:
        logger.exception("Error during video processing")
        return render_template(
            "upload.html",
            results={"success": False, "error": f"Processing error: {str(e)}"},
        )


if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000, ssl_context="adhoc")