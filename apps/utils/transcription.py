import os
from openai import OpenAI

def transcribe_audio(audio_file_path):
    """
    Transcribes an audio file using OpenAI Whisper API and returns word-level timestamps
    """
    api_key = os.getenv("OPENAI_API_KEY")
    client = OpenAI(api_key=api_key)

    try:
        with open(audio_file_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                file=audio_file,
                model="whisper-1",
                response_format="verbose_json",
                timestamp_granularities=["word"]
            )

        # Convert TranscriptionWord objects to dictionaries
        words_list = []
        for word in transcript.words:
            words_list.append({
                "word": word.word,
                "start": word.start,
                "end": word.end
            })

        return words_list

    except Exception as e:
        raise Exception(f"Transcription error: {str(e)}")
