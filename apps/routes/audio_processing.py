from moviepy.editor import VideoFileClip

def extract_audio(video_path, output_audio_path="audio.wav"):
    video = VideoFileClip(video_path)
    video.audio.write_audiofile(output_audio_path)
    return output_audio_path
