from openai import OpenAI
from typing import List, Dict
import re

def analyze_content(transcript_words: List[Dict]) -> dict:
    """Analyze transcript content to identify meaningful moments."""
    try:
        # Group words into coherent segments based on natural pauses
        PAUSE_THRESHOLD = 1.0  # 1 second pause indicates potential new segment
        segments = []
        current_segment = []

        for i, word in enumerate(transcript_words):
            current_segment.append(word)

            # Check for natural pause or end of transcript
            is_last_word = i == len(transcript_words) - 1
            next_word_gap = (transcript_words[i + 1]["start"] - word["end"]) if not is_last_word else 0

            if next_word_gap > PAUSE_THRESHOLD or is_last_word:
                if current_segment:
                    segment_text = " ".join([w["word"] for w in current_segment])
                    segments.append({
                        "text": segment_text,
                        "start": current_segment[0]["start"],
                        "end": current_segment[-1]["end"]
                    })
                    current_segment = []

        # Use GPT to identify segments with visual demonstrations
        client = OpenAI()
        meaningful_moments = []

        for segment in segments:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": """
                     Analyze if this segment describes a visual demonstration or key concept.
                     Look for phrases like:
                     - "as you can see"
                     - "here's how"
                     - "this shows"
                     - "in this example"
                     - "demonstration of"
                     - Visual descriptions of algorithms or processes
                     """},
                    {"role": "user", "content": f"Is this segment describing something visual that should be captured as a screenshot? Only respond with YES or NO:\n{segment['text']}"}
                ],
                temperature=0.3,
            )

            if "YES" in response.choices[0].message.content.upper():
                # Calculate middle of segment for timestamp
                timestamp = (segment["start"] + segment["end"]) / 2
                meaningful_moments.append({
                    "timestamp": timestamp,
                    "text": segment["text"]
                })

        return {
            "success": True,
            "moments": meaningful_moments
        }

    except Exception as e:
        return {"success": False, "error": str(e)}
