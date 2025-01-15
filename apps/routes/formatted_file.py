import os
import base64
import json
import openai
import language_tool_python

# Directory to temporarily save decoded images
IMAGE_DIR = '../static/images'
os.makedirs(IMAGE_DIR, exist_ok=True)

# Initialize grammar/spell checker
tool = language_tool_python.LanguageTool('en-US')

# Set OpenAI API Key
openai.api_key = os.getenv("OPENAI_API_KEY")

def correct_text(text):
    """
    Corrects spelling and grammar in a text using LanguageTool.
    """
    return tool.correct(text)

def save_images_from_screenshots(screenshots):
    """
    Saves base64-encoded images to disk and returns their file paths.
    """
    image_paths = []
    for idx, screenshot in enumerate(screenshots):
        # Handle strings if `screenshots` is not a list of dictionaries
        if isinstance(screenshot, str):
            try:
                screenshot_data = json.loads(screenshot)
            except json.JSONDecodeError:
                print(f"Invalid JSON string at index {idx}")
                continue
        else:
            screenshot_data = screenshot

        timestamp = screenshot_data.get("timestamp", "")
        image_base64 = screenshot_data.get("image_base64", "")
        if not image_base64:
            continue

        image_path = os.path.join(IMAGE_DIR, f"screenshot_{idx}.png")
        with open(image_path, "wb") as image_file:
            image_file.write(base64.b64decode(image_base64))

        image_paths.append({"timestamp": timestamp, "path": image_path})
    return image_paths


def refine_text_with_llm(text):
    """
    Refines the input text using OpenAI's GPT with the updated API, 
    asking for Markdown formatting, improved clarity, and proper structure.
    """
    try:
        response = openai.ChatCompletion.acreate(  # Use `acreate` for the latest API
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a text editor and formatter specialized in creating well-structured Markdown documents. "
                        "Your task is to improve clarity, grammar, and readability while formatting the text as Markdown. "
                        "Use appropriate headings, paragraphs, bullet points, or numbered lists where necessary. "
                        "If the text mentions images, include a Markdown placeholder for the image (e.g., `![Alt text](path/to/image)`)."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        "Format the following text into Markdown, improving clarity and grammar. "
                        "Use headings, subheadings, and bullet points where appropriate:\n\n"
                        f"{text}"
                    ),
                },
            ],
            max_tokens=800,  # Adjust token limit as needed
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error using LLM: {e}")
        return text  # Fallback to the original text



def format_paragraphs_with_images(transcription, images):
    """
    Formats paragraphs with sentences and aligns images logically.
    """
    paragraphs = []
    current_paragraph = []
    last_end_time = 0
    sentence_endings = [".", "?", "!"]

    for word_data in transcription:
        word = word_data["word"]
        start = word_data["start"]
        end = word_data["end"]
        
        if start - last_end_time > 2 and current_paragraph:
            paragraphs.append(" ".join(current_paragraph))
            current_paragraph = []

        current_paragraph.append(word)
        last_end_time = end

        if word[-1] in sentence_endings:
            paragraphs.append(" ".join(current_paragraph))
            current_paragraph = []

    if current_paragraph:
        paragraphs.append(" ".join(current_paragraph))

    markdown = []
    image_idx = 0
    for i, paragraph in enumerate(paragraphs):
        refined_paragraph = refine_text_with_llm(paragraph)  # Use LLM for refinement
        markdown.append(refined_paragraph)

        if image_idx < len(images) and float(images[image_idx]["timestamp"]) <= last_end_time:
            img_path = images[image_idx]["path"]
            markdown.append(f"![Screenshot]({img_path})")
            image_idx += 1

    return "\n\n".join(markdown)

def convert_to_markdown(transcription, screenshots):
    """
    Combines transcription and screenshots into Markdown format, using LLM for text enhancement.
    """
    images = save_images_from_screenshots(screenshots)
    return format_paragraphs_with_images(transcription, images)
