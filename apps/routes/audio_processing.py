from moviepy.editor import VideoFileClip
import subprocess
import os


def extract_audio(video_path, output_audio_path="audio.wav", max_size_mb=25):
    """
    Extract and compress audio from video to stay within API limits.
    """
    try:
        # Direct extraction with compression settings
        subprocess.run(
            [
                "ffmpeg",
                "-i",
                video_path,
                "-vn",  # No video
                "-acodec",
                "pcm_s16le",  # PCM format
                "-ar",
                "16000",  # 16kHz sample rate
                "-ac",
                "1",  # Mono
                "-y",  # Overwrite output file
                output_audio_path,
            ],
            check=True,
            capture_output=True,
        )

        # Check if further compression needed
        if os.path.getsize(output_audio_path) > max_size_mb * 1024 * 1024:
            temp_path = output_audio_path + ".temp"
            os.rename(output_audio_path, temp_path)

            subprocess.run(
                [
                    "ffmpeg",
                    "-i",
                    temp_path,
                    "-ar",
                    "16000",
                    "-ac",
                    "1",
                    "-b:a",
                    "32k",  # Very aggressive compression
                    "-y",
                    output_audio_path,
                ],
                check=True,
                capture_output=True,
            )

            os.remove(temp_path)

        return output_audio_path

    except Exception as e:
        raise Exception(f"Error extracting audio: {str(e)}")
