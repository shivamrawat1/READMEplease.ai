import os
import uuid
from moviepy.editor import VideoFileClip

def convert_video_to_audio(video_file):
    """
    Converts a video file to an audio file.
    Returns the path to the generated audio file.
    """
    temp_video_path = None
    temp_audio_path = None

    try:
        # Save the video file temporarily
        temp_video_path = f"/tmp/{uuid.uuid4().hex}.mp4"
        video_file.save(temp_video_path)

        # Extract audio from the video and save to a temporary file
        temp_audio_path = f"/tmp/{uuid.uuid4().hex}.wav"
        clip = VideoFileClip(temp_video_path)
        clip.audio.write_audiofile(temp_audio_path)  # Save audio as a file
        clip.close()

        return temp_audio_path

    except Exception as e:
        raise Exception(f"Error in convert_video_to_audio: {str(e)}")

    finally:
        # Clean up the temporary video file
        if temp_video_path and os.path.exists(temp_video_path):
            os.remove(temp_video_path)
