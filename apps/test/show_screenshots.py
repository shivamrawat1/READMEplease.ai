import os
import sys
import json
import base64
from pathlib import Path

# Add the parent directory to Python path to allow imports from apps
project_root = str(Path(__file__).parent.parent.parent)
if project_root not in sys.path:
    sys.path.append(project_root)

# Define paths
SAMPLES_DIR = os.path.join(Path(__file__).parent.parent, "samples")
SCREENSHOTS_FILE = os.path.join(SAMPLES_DIR, "sample_screenshots.json")
OUTPUT_DIR = os.path.join(SAMPLES_DIR, "ss")

def save_screenshots(json_path: str, output_dir: str):
    """
    Read screenshots from JSON file and save them as images.
    
    Args:
        json_path (str): Path to the JSON file containing base64 encoded images
        output_dir (str): Directory where images will be saved
    """
    print(f"Reading screenshots from: {json_path}")
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        # Read the JSON file
        with open(json_path, 'r') as f:
            data = json.load(f)
        
        if not data["success"]:
            print(f"Error in screenshots file: {data.get('error', 'Unknown error')}")
            return
        
        keyword = data["keyword"]
        screenshots = data["screenshots"]
        
        print(f"\nFound {len(screenshots)} screenshots for keyword '{keyword}'")
        
        # Process each screenshot
        for i, screenshot in enumerate(screenshots, 1):
            timestamp = screenshot["timestamp"]
            image_base64 = screenshot["image_base64"]
            
            # Decode base64 string to image data
            image_data = base64.b64decode(image_base64)
            
            # Create filename with timestamp
            filename = f"screenshot_{keyword}_{timestamp:.2f}s.jpg"
            filepath = os.path.join(output_dir, filename)
            
            # Save the image
            with open(filepath, 'wb') as f:
                f.write(image_data)
            
            print(f"Saved screenshot {i}: {filename}")
        
        print(f"\nAll screenshots saved in: {output_dir}")
        
    except FileNotFoundError:
        print(f"Error: Screenshots file not found at {json_path}")
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON file at {json_path}")
    except Exception as e:
        print(f"Error: {str(e)}")

def main():
    # Check if input file exists
    if not os.path.exists(SCREENSHOTS_FILE):
        print(f"Error: Screenshots file not found at {SCREENSHOTS_FILE}")
        return
    
    save_screenshots(SCREENSHOTS_FILE, OUTPUT_DIR)

if __name__ == "__main__":
    main() 