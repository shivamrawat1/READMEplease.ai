import openai
from openai import OpenAI
import json
from pathlib import Path
import os

def transcribe_audio_with_timestamps(audio_file_path: str) -> dict:
    """
    Transcribe an audio file using OpenAI's Whisper model and return words with timestamps.

    Args:
        audio_file_path (str): Path to the audio file to transcribe

    Returns:
        dict: Dictionary containing the transcription with timestamps
    """
    try:
        client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

        with open(audio_file_path, "rb") as audio_file:
            transcription = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                response_format="verbose_json",
                timestamp_granularities=["word"]
            )

            # Convert response to dictionary if it's not already
            if not isinstance(transcription, dict):
                transcription = transcription.model_dump()

        # Extract words with timestamps directly from the response
        words_with_timestamps = []
        if isinstance(transcription, dict) and 'words' in transcription:
            for word_data in transcription['words']:
                words_with_timestamps.append({
                    "word": word_data['word'],
                    "start": round(word_data['start'], 2),
                    "end": round(word_data['end'], 2)
                })

        result = {
            "success": True,
            "words": words_with_timestamps,
            "file_processed": audio_file_path
        }

    except FileNotFoundError:
        result = {
            "success": False,
            "error": "Audio file not found",
            "file_processed": audio_file_path
        }
    except Exception as e:
        result = {
            "success": False,
            "error": str(e),
            "file_processed": audio_file_path
        }

    return result