from openai import OpenAI
import os


def generate_blog_from_transcript(transcript_text: str) -> dict:
    """Generate a blog post with screenshot markers."""
    try:
        client = OpenAI()

        system_prompt = """You are an expert technical writer. When writing about technical
        concepts or visual elements, mark where screenshots would be helpful using this format:
        [SCREENSHOT:timestamp:description]

        For example: [SCREENSHOT:30:Example of the edge detection output showing clear ball boundaries]

        Add 3-5 such markers at key points in the explanation."""

        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Create a technical blog post from this transcript with appropriate screenshot markers:\n\n{transcript_text}"}
            ],
            temperature=0.7,
        )

        return {
            "success": True,
            "blog_content": response.choices[0].message.content,
            "has_markers": "[SCREENSHOT:" in response.choices[0].message.content
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
