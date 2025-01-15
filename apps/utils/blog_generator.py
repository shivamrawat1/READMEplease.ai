from openai import OpenAI
import os


def generate_blog_from_transcript(transcript_text: str, timestamps: list = None) -> dict:
    """Generate a blog post with screenshot markers using actual timestamps."""
    try:
        client = OpenAI()

        # Create timestamp guidance
        timestamp_guidance = ""
        if timestamps:
            timestamp_str = ", ".join([f"{t:.2f}s" for t in timestamps])
            timestamp_guidance = f"\nUse these exact timestamps for screenshots: {timestamp_str}"

        system_prompt = f"""You are an expert technical writer. When writing about technical
        concepts or visual elements, mark where screenshots should be embedded using this format:

        <screenshot time="timestamp" description="description"/>

        For example:
        <screenshot time="30.20" description="Edge detection example showing boundary detection"/>

        Only use timestamps from this list: {timestamp_guidance}
        Keep descriptions short and focused on visual elements.

        Your output should be valid HTML/Markdown mixed content."""

        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Create a technical blog post from this transcript with screenshot markers at the provided timestamps:\n\n{transcript_text}"}
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
