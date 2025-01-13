from openai import OpenAI
import json
from pathlib import Path

def transcribe_audio(audio_file_path: str) -> dict:
    """
    Transcribe an audio file using OpenAI's Whisper model and return the results as JSON.
    
    Args:
        audio_file_path (str): Path to the audio file to transcribe
    
    Returns:
        dict: Dictionary containing the transcription text
    """
    try:
        client = OpenAI()
        
        with open(audio_file_path, "rb") as audio_file:
            transcription = client.audio.transcriptions.create(
                model="whisper-1", 
                file=audio_file
            )
        
        result = {
            "success": True,
            "transcription": transcription.text,
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