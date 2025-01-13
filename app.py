from flask import Flask, render_template, request, redirect, url_for
from dotenv import load_dotenv
import os
import tempfile
from pathlib import Path
import json

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

@app.route('/')
def index():
    return redirect(url_for('upload'))

@app.route('/upload', methods=['GET'])
def upload():
    return render_template('upload.html')

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
    
    # Create temporary directory for processing
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)
        
        # Save uploaded video
        video_path = temp_dir_path / "uploaded_video.mp4"
        video.save(video_path)
        
        # Extract audio
        audio_path = temp_dir_path / "audio.wav"
        extract_audio(str(video_path), str(audio_path))
        
        # Get transcription with timestamps
        transcription = transcribe_audio_with_timestamps(str(audio_path))
        
        if not transcription['success']:
            return render_template('upload.html', 
                                 results={"success": False, 
                                        "error": f"Transcription failed: {transcription['error']}"})
        
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
        
        return render_template('upload.html', results=screenshots)

if __name__ == '__main__':
    app.run(debug=True,
            host='127.0.0.1',
            port=5000,
            ssl_context='adhoc')