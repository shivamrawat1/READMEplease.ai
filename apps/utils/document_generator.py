from openai import OpenAI
import os


def generate_document_from_transcript(transcript_text: str, timestamps: list = None) -> dict:
    """Generate an explanatory document with screenshot markers using actual timestamps."""
    try:
        client = OpenAI()

        # Create timestamp guidance (for placement only)
        timestamp_guidance = ""
        if timestamps:
            timestamp_str = ", ".join([f"{t:.2f}s" for t in timestamps])
            timestamp_guidance = f"\nUse these exact timestamps for screenshots: {timestamp_str}"

        system_prompt = f"""You are an expert technical writer. When writing about technical
        concepts or visual elements, mark where screenshots should be embedded using this format:

        <screenshot time="timestamp" description="description"/>

        For example:
        <screenshot time="30.20" description="The interface showing the main dashboard"/>

        Only use timestamps from this list: {timestamp_guidance}
        Focus descriptions on what is being shown, not when it appears.
        Keep descriptions clear and concise.
        Write in a clear, instructional style suitable for technical documentation.

        Your output should be valid HTML/Markdown mixed content."""

        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Create a technical explanation document from this transcript with screenshot markers at the provided timestamps:\n\n{transcript_text}"}
            ],
            temperature=0.7,
        )

        return {
            "success": True,
            "document_content": response.choices[0].message.content,
            "has_markers": "<screenshot" in response.choices[0].message.content
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
