import requests

# Endpoint URL
url = "http://127.0.0.1:5000/process_video"

# Path to the video file
video_file_path = "/Users/jeevanbhatta/Downloads/nosuai/sample_videos/EduAccess.mp4"

# Make the POST request
with open(video_file_path, "rb") as video_file:
    files = {"video_file": video_file}
    response = requests.post(url, files=files)

# Print the response
print(response.status_code)
print(response.json())
