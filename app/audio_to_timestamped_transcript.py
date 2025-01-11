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
    Returns the transcript with word-level timestamps.
    """
    try:
        with open(audio_file_path, "rb") as audio_file:
            transcription = openai.Audio.transcribe(
                model="whisper-1",
                file=audio_file,
                response_format="verbose_json"
            )
        
        return transcription

    except Exception as e:
        raise Exception(f"Error in convert_audio_to_timestamped_transcript: {str(e)}")