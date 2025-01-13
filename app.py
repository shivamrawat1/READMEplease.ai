from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from dotenv import load_dotenv
import os
import tempfile
from pathlib import Path
import json
import threading

# Import processing functions
from apps.routes.audio_processing import extract_audio
from apps.routes.transcription_with_timestamps import transcribe_audio_with_timestamps
from apps.routes.create_screenshots import create_screenshots_for_keyword

# Load environment variables
load_dotenv()

# Create Flask app with custom template folder
app = Flask(__name__,
           template_folder='apps/templates',
           static_folder='apps/static')
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'dev')

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

def process_video_task(video_path, keyword, processing_id):
    try:
        temp_dir = tempfile.mkdtemp()
        temp_dir_path = Path(temp_dir)
        
        # Extract audio
        audio_path = temp_dir_path / "audio.wav"
        extract_audio(str(video_path), str(audio_path))
        
        # Get transcription with timestamps
        transcription = transcribe_audio_with_timestamps(str(audio_path))
        
        if not transcription['success']:
            processing_results[processing_id] = {
                "success": False,
                "error": f"Transcription failed: {transcription['error']}"
            }
            return
        
        # Save transcription to file
        transcription_path = temp_dir_path / "transcription.json"
        with open(transcription_path, 'w') as f:
            json.dump(transcription['words'], f)
        
        # Create screenshots
        screenshots = create_screenshots_for_keyword(
            str(video_path),
            str(transcription_path),
            keyword
        )
        
        processing_results[processing_id] = screenshots
        
    except Exception as e:
        processing_results[processing_id] = {
            "success": False,
            "error": str(e)
        }
    finally:
        # Cleanup temporary directory
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)

@app.route('/process_video', methods=['POST'])
def process_video():
    if 'video' not in request.files:
        return render_template('upload.html', 
                             results={"success": False, "error": "No video file uploaded"})
    
    video = request.files['video']
    keyword = request.form.get('keyword', '').strip()
    
    if not keyword:
        return render_template('upload.html', 
                             results={"success": False, "error": "No keyword provided"})
    
    # Create temporary file for video
    temp_video = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
    video.save(temp_video.name)
    
    # Generate unique processing ID
    processing_id = str(hash(f"{temp_video.name}{keyword}{os.urandom(8).hex()}"))
    session['processing_id'] = processing_id
    
    # Start processing in background
    thread = threading.Thread(
        target=process_video_task,
        args=(temp_video.name, keyword, processing_id)
    )
    thread.start()
    
    # Redirect to wait screen
    return redirect(url_for('wait_screen'))

@app.route('/check_progress')
def check_progress():
    processing_id = session.get('processing_id')
    if not processing_id:
        return jsonify({"status": "error", "message": "No processing ID found"})
    
    if processing_id in processing_results:
        result = processing_results[processing_id]
        # Clean up results after retrieving them
        del processing_results[processing_id]
        return jsonify({"status": "complete", "results": result})
    
    return jsonify({"status": "processing"})

@app.route("/wait")
def wait_screen():
    """Display wait screen with video."""
    is_https = request.is_secure
    return render_template('wait.html', is_https=is_https)

if __name__ == '__main__':
    app.run(debug=True,
            host='127.0.0.1',
            port=5000,
            ssl_context='adhoc')