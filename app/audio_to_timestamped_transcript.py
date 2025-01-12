import openai
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Get the OpenAI API key from the .env file
openai.api_key = os.getenv("OPENAI_API_KEY")

def convert_audio_to_timestamped_transcript(audio_file_path):
    """
    Converts an audio file to a transcript with timestamps using OpenAI's Whisper API.
    Returns a list of segments with text and segment-level timestamps. 
    Word-level timestamps are only returned if Whisper provides them.
    """
    try:
        with open(audio_file_path, "rb") as audio_file:
            transcription = client.audio.transcriptions.create(
                file=audio_file,
                model="whisper-1",
                response_format="verbose_json",
                timestamp_granularities=["word"]
            )
        word_timestamps = []

        for segment in transcription.get("segments", []):
            # If your model returns word-level timestamps, they'll appear here
            if "words" in segment and segment["words"]:
                for word_info in segment["words"]:
                    word_timestamps.append({
                        "word": word_info["word"],
                        "start": round(word_info["start"], 2),
                        "end": round(word_info["end"], 2)
                    })
            else:
                # Fallback: use the entire segment as one entry
                word_timestamps.append({
                    "text": segment["text"],
                    "start": round(segment["start"], 2),
                    "end": round(segment["end"], 2)
                })

        return word_timestamps

    except Exception as e:
        raise Exception(f"Error in convert_audio_to_timestamped_transcript: {str(e)}")