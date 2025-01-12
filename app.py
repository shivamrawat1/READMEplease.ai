from flask import Flask, request, jsonify, render_template
from openai import OpenAI
import os

app = Flask(__name__)
# Use environment variable with fallback to hardcoded key
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {"mp3"}

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/transcribe", methods=["POST"])
def transcribe():
    print("=== Starting transcription request ===")
    if "file" not in request.files:
        print("No file found in request")
        return jsonify({"error": "No file provided"}), 400

    file = request.files["file"]
    magic_word = request.form.get("magic_word", "").lower()
    print(f"Processing file: {file.filename}")
    print(f"Searching for magic word: {magic_word}")

    if file.filename == "" or not allowed_file(file.filename):
        print(f"Invalid file type: {file.filename}")
        return jsonify({"error": "Invalid file"}), 400

    filepath = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(filepath)
    print(f"File saved temporarily at: {filepath}")

    try:
        print("Starting Whisper API transcription...")
        with open(filepath, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                file=audio_file,
                model="whisper-1",
                response_format="verbose_json",
                timestamp_granularities=["word"],
            )
        print("Transcription completed successfully")
        print(f"Raw transcript: {transcript}")

        occurrences = []
        for word in transcript.words:
            # Access word value using dictionary syntax
            if word["word"].lower() == magic_word:
                occurrence = {
                    "timestamp": word["start"],
                    "context": f"...{word['word']}...",
                }
                occurrences.append(occurrence)
                print(f"Found occurrence at {word['start']}s: {occurrence}")

        print(f"Total occurrences found: {len(occurrences)}")
        return jsonify({"occurrences": occurrences, "total": len(occurrences)})

    except Exception as e:
        print(f"Error during transcription: {str(e)}")
        raise
    finally:
        if os.path.exists(filepath):
            os.remove(filepath)
            print(f"Cleaned up temporary file: {filepath}")


if __name__ == "__main__":
    app.run(debug=True)
