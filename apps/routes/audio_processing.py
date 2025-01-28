from moviepy.editor import VideoFileClip
import subprocess
import os


def extract_audio(video_path, output_audio_path="audio.wav", max_size_mb=25):
    """
    Extract and compress audio from video to stay within API limits.
    """
    try:
        # First pass - extract with high quality
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

        # Check if compression needed
        current_size = os.path.getsize(output_audio_path) / (1024 * 1024)  # Size in MB
        if current_size > max_size_mb:
            # Calculate target bitrate to achieve desired file size
            target_bitrate = int((max_size_mb * 8 * 1024) / (current_size / max_size_mb))  # in kbps
            temp_path = output_audio_path + ".temp"
            os.rename(output_audio_path, temp_path)

            subprocess.run(
                [
                    "ffmpeg",
                    "-i",
                    temp_path,
                    "-ar",
                    "16000",  # Keep 16kHz sample rate
                    "-ac",
                    "1",  # Keep mono
                    "-b:a",
                    f"{target_bitrate}k",  # Dynamic bitrate based on target size
                    "-acodec",
                    "libmp3lame",  # Use MP3 for better compression
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
