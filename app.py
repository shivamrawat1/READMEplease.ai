from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_file
import logging
from dotenv import load_dotenv
import os
import tempfile
from pathlib import Path
import cv2
import markdown
import base64
from io import BytesIO
from zipfile import ZipFile
from typing import List

# Import processing functions
from apps.routes.audio_processing import extract_audio
from apps.routes.transcription_with_timestamps import transcribe_audio_with_timestamps
from apps.routes.create_screenshots import create_automated_screenshots
from apps.utils.document_generator import generate_document_from_transcript
from apps.utils.screenshot_selector import select_screenshot_moments
from apps.utils.content_merger import generate_markdown_content
from apps.utils.cloud_storage import CloudStorage
from apps.utils.github_analyzer import GitHubAnalyzer

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
    # Pass empty results to avoid template errors
    return render_template("upload.html", results=None)


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
    
    try:
        # Process video and generate initial markdown
        video_markdown = process_video_content(request)
        if not video_markdown["success"]:
            return render_template(
                "upload.html",
                results=video_markdown
            )
        
        # Process GitHub repository if URL provided
        repo_url = request.form.get("repo_url")
        selected_sections = request.form.getlist("sections")
        
        if repo_url and selected_sections:
            github_content = process_github_content(repo_url, selected_sections)
            if not github_content["success"]:
                return render_template(
                    "upload.html",
                    results={
                        "success": False,
                        "error": f"GitHub processing error: {github_content.get('error', 'Unknown error')}"
                    }
                )
            
            # Combine video markdown with GitHub sections
            final_markdown = combine_markdown_sections(video_markdown, github_content)
            return render_template("upload.html", results=final_markdown)
        
        # If no GitHub URL provided, return just the video markdown
        return render_template("upload.html", results=video_markdown)
        
    except Exception as e:
        logger.exception("Error during processing")
        return render_template(
            "upload.html",
            results={
                "success": False, 
                "error": f"Processing error: {str(e)}"
            }
        )

def process_video_content(request) -> dict:
    """Process video and generate markdown content."""
    logger.debug("Starting video processing")
    
    # Initial validation
    if "video" not in request.files:
        return {
            "success": False, 
            "error": "No video file uploaded"
        }

    video = request.files["video"]
    if not video.filename:
        return {
            "success": False, 
            "error": "No file selected"
        }

    # File size check
    MAX_FILE_SIZE = 25 * 1024 * 1024  # 25MB in bytes
    video.seek(0, os.SEEK_END)
    size = video.tell()
    video.seek(0)

    if size > MAX_FILE_SIZE:
        return {
            "success": False, 
            "error": "Video file too large (max 25MB)"
        }

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
                return {
                    "success": False,
                    "error": f"Transcription failed: {transcription['error']}"
                }

            # Get screenshots based on content analysis
            screenshot_suggestions = select_screenshot_moments(transcription["words"])
            screenshots = []

            if screenshot_suggestions["success"] and screenshot_suggestions.get("timestamps"):
                screenshots = create_automated_screenshots(
                    str(video_path),
                    screenshot_suggestions["timestamps"]
                )

            # Generate document content with actual timestamps
            full_transcript = " ".join([word["word"] for word in transcription["words"]])
            doc_result = generate_document_from_transcript(
                full_transcript,
                timestamps=[s["timestamp"] for s in screenshots]
            )

            if not doc_result["success"]:
                return {
                    "success": False,
                    "error": f"Document generation failed: {doc_result.get('error', 'Unknown error')}"
                }

            # Generate markdown content
            markdown_result = generate_markdown_content(doc_result["document_content"], screenshots)

            return {
                "success": True,
                "markdown_content": markdown_result["raw"],
                "markdown_html": markdown_result["html"],
                "screenshots": screenshots,
                "has_screenshots": len(screenshots) > 0,
                "screenshot_count": len(screenshots)
            }

    except Exception as e:
        logger.exception("Error during video processing")
        return {
            "success": False,
            "error": f"Processing error: {str(e)}"
        }

def process_github_content(repo_url: str, sections: List[str]) -> dict:
    """Generate README sections from GitHub repository."""
    try:
        analyzer = GitHubAnalyzer(repo_url)
        sections_content = []
        
        for section in sections:
            result = analyzer.generate_section(section)
            if result["success"]:
                sections_content.append(result["content"])
                
        return {
            "success": True,
            "sections": sections_content
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

def combine_markdown_sections(video_content: dict, github_content: dict) -> dict:
    """Combine video markdown with GitHub sections."""
    try:
        if not video_content.get("success", False) or not github_content.get("success", False):
            return video_content if video_content.get("success", False) else github_content
        
        combined_markdown = video_content["markdown_content"] + "\n\n"
        for section in github_content.get("sections", []):
            combined_markdown += section + "\n\n"
        
        return {
            "success": True,
            "markdown_content": combined_markdown,
            "markdown_html": markdown.markdown(combined_markdown, extensions=['extra']),
            "screenshots": video_content.get("screenshots", []),
            "has_screenshots": video_content.get("has_screenshots", False),
            "screenshot_count": video_content.get("screenshot_count", 0)
        }
    except Exception as e:
        logger.exception("Error combining markdown sections")
        return {
            "success": False,
            "error": f"Error combining sections: {str(e)}"
        }


@app.route("/download_markdown", methods=["POST"])
def download_markdown():
    try:
        data = request.get_json()
        markdown_content = data.get("markdown_content")
        screenshots = data.get("screenshots", [])
        
        # Generate markdown with cloud URLs
        markdown_result = generate_markdown_content(markdown_content, screenshots)
        
        # Return just the markdown file
        return send_file(
            BytesIO(markdown_result["raw"].encode('utf-8')),
            mimetype='text/markdown',
            as_attachment=True,
            download_name='blog_post.md'
        )
        
    except Exception as e:
        logger.error(f"Error generating markdown: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/test_s3", methods=["GET"])
def test_s3():
    try:
        logger.info("Starting S3 connection test")
        cloud_storage = CloudStorage()
        
        # Test uploading a simple image
        test_image = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
        logger.info("Attempting to upload test image")
        
        result = cloud_storage.upload_image(test_image, "test.png")
        
        if result:
            logger.info(f"Successfully uploaded test image: {result}")
            return jsonify({
                "success": True,
                "url": result,
                "message": "Test upload successful"
            })
        
        logger.error("Upload failed but no exception was raised")
        return jsonify({
            "success": False,
            "error": "Upload failed without exception",
            "message": "Check application logs for details"
        })
        
    except Exception as e:
        logger.exception("Test upload failed with exception")
        return jsonify({
            "success": False,
            "error": str(e),
            "message": "Check application logs for details"
        })


@app.route("/test_s3_detailed", methods=["GET"])
def test_s3_detailed():
    try:
        # Test environment variables
        env_vars = {
            "region": os.getenv('AWS_REGION'),
            "bucket": os.getenv('AWS_BUCKET_NAME'),
            "access_key_exists": bool(os.getenv('AWS_ACCESS_KEY_ID')),
            "secret_key_exists": bool(os.getenv('AWS_SECRET_ACCESS_KEY'))
        }
        
        # Initialize client
        cloud_storage = CloudStorage()
        
        # Test image (1x1 pixel transparent PNG)
        test_image = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
        
        # Try upload
        result = cloud_storage.upload_image(test_image, "test.png")
        
        return jsonify({
            "success": bool(result),
            "environment": env_vars,
            "url": result if result else None,
            "error": None if result else "Upload failed"
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": str(e.__traceback__)
        })


if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000, ssl_context="adhoc")