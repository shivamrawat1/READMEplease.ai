import markdown
import re
from typing import List, Dict

def generate_blog_html(blog_content: str, screenshots: List[Dict]) -> str:
    """Generate HTML blog with screenshots."""
    try:
        # Extract screenshot markers and their times
        marker_pattern = r'\[SCREENSHOT:(\d+):([^\]]+)\]'
        markers = re.finditer(marker_pattern, blog_content)

        # Replace markers with actual screenshots
        html_content = blog_content
        for i, marker in enumerate(markers):
            timestamp = int(marker.group(1))
            description = marker.group(2)

            # Find closest screenshot to this timestamp
            closest_screenshot = None
            if screenshots:
                closest_screenshot = min(
                    screenshots,
                    key=lambda x: abs(x['timestamp'] - timestamp)
                )

            if closest_screenshot:
                screenshot_html = f"""
                <div class="blog-image">
                    <img src="data:image/jpeg;base64,{closest_screenshot['image_base64']}"
                         alt="{description}">
                    <div class="caption">
                        <p>{description}</p>
                        <span class="timestamp">Timestamp: {closest_screenshot['timestamp']:.2f}s</span>
                    </div>
                </div>
                """
            else:
                # Placeholder image if no screenshot available
                screenshot_html = f"""
                <div class="blog-image placeholder">
                    <div class="placeholder-content">
                        <p>[Visual example would go here]</p>
                        <p>{description}</p>
                    </div>
                </div>
                """

            html_content = html_content.replace(marker.group(0), screenshot_html)

        # Convert to HTML with styling
        styled_html = f"""
        <div class="blog-post">
            <style>
                .blog-image {{ margin: 2em 0; text-align: center; }}
                .blog-image img {{ max-width: 100%; border-radius: 8px; }}
                .caption {{ margin-top: 1em; color: #666; }}
                .placeholder {{
                    background: #f5f5f5;
                    padding: 2em;
                    border-radius: 8px;
                    border: 2px dashed #ccc;
                }}
                .placeholder-content {{
                    color: #666;
                    font-style: italic;
                }}
            </style>
            {markdown.markdown(html_content)}
        </div>
        """

        return styled_html

    except Exception as e:
        return f"<div class='error'>Error generating blog: {str(e)}</div>"
