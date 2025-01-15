# NosuAI - Video Keyword Screenshot Generator

A Flask web application that processes videos, transcribes speech using OpenAI Whisper, and generates screenshots at moments when specific keywords are spoken.

## Features

- Upload and process video files
- Extract audio from video
- Transcribe speech with timestamps using OpenAI Whisper API
- Generate screenshots at exact moments when keywords are spoken
- Word boundary-aware keyword matching (case insensitive)
- Integration with GitHub and Notion APIs
- Secure HTTPS local development
- Debug logging and system status checks

## Requirements

- Python 3.11+
- FFmpeg
- OpenCV
- OpenAI API key
- (Optional) GitHub OAuth credentials
- (Optional) Notion OAuth credentials

## Installation

1. Clone the repository:

```bash
git clone <repository-url>
cd nosuai
```

2. Create and activate a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the project root with your credentials:

```env
OPENAI_API_KEY=your-openai-api-key
FLASK_SECRET_KEY=your-secret-key
# Optional OAuth credentials
GITHUB_CLIENT_ID=your-github-client-id
GITHUB_CLIENT_SECRET=your-github-client-secret
GITHUB_REDIRECT_URI=https://127.0.0.1:5000/github/callback
NOTION_CLIENT_ID=your-notion-client-id
NOTION_CLIENT_SECRET=your-notion-client-secret
NOTION_REDIRECT_URI=https://127.0.0.1:5000/notion/callback
```

## Usage

1. Start the Flask application:

```bash
python app.py
```

2. Open your browser and navigate to:

```
https://127.0.0.1:5000
```

3. Upload a video and enter a keyword to search for.

4. The application will:
   - Extract the audio from your video
   - Transcribe the speech using OpenAI Whisper
   - Find timestamps where your keyword is spoken
   - Generate screenshots at those moments
   - Display the results in a grid with timestamps

## Project Structure

```
nosuai/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── .env                  # Environment variables
├── apps/
│   ├── routes/
│   │   ├── audio_processing.py
│   │   ├── create_screenshots.py
│   │   ├── github.py
│   │   ├── notion.py
│   │   └── transcription_with_timestamps.py
│   ├── static/
│   │   └── css/
│   ├── templates/
│   │   ├── upload.html
│   │   ├── github.html
│   │   └── notion.html
│   └── utils/
│       └── clean_samples.py
```

## API Endpoints

- `/`: Main upload page
- `/upload`: Video upload form
- `/process_video`: Process uploaded video
- `/test`: System component status check
- `/github/*`: GitHub OAuth endpoints
- `/notion/*`: Notion OAuth endpoints

## Development

The application uses HTTPS for local development to support OAuth callbacks. Accept the self-signed certificate warning in your browser for testing.

## License

MIT License - See LICENSE file for details

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request