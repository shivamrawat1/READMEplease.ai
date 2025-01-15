import markdown
import re
from typing import List, Dict

def generate_blog_html(blog_content: str, screenshots: List[Dict]) -> str:
    """Generate HTML blog with screenshots."""
    try:
        # Extract screenshot markers and their descriptions
        marker_pattern = r'\[SCREENSHOT:(\d+\.?\d*):([^\]]+)\]'
        markers = list(re.finditer(marker_pattern, blog_content))

        # Create a mapping of available screenshots
        screenshot_map = {round(s['timestamp'], 1): s for s in screenshots}

        # Replace markers with actual screenshots
        html_content = blog_content
        for marker in markers:
            timestamp = float(marker.group(1))
            description = marker.group(2)

            # Find closest screenshot by timestamp
            closest_timestamp = min(screenshot_map.keys(),
                                key=lambda x: abs(x - timestamp),
                                default=None)

            if closest_timestamp and abs(closest_timestamp - timestamp) < 5.0:  # Within 5 seconds
                screenshot = screenshot_map[closest_timestamp]
                screenshot_html = f'''
                <div class="blog-image">
                    <img src="data:image/jpeg;base64,{screenshot['image_base64']}"
                         alt="{description.strip()}">
                    <div class="caption">
                        <p>{description.strip()}</p>
                        <span class="timestamp">Timestamp: {screenshot['timestamp']:.2f}s</span>
                    </div>
                </div>
                '''.strip()
            else:
                screenshot_html = f'''
                <div class="blog-image placeholder">
                    <div class="placeholder-content">
                        <p>[Visual example would go here]</p>
                        <p>{description.strip()}</p>
                    </div>
                </div>
                '''.strip()

            html_content = html_content.replace(marker.group(0), screenshot_html)

        # Convert markdown to HTML with styling
        html_content = markdown.markdown(html_content)

        # Add wrapper and styling
        styled_html = f'''
        <div class="blog-post">
            <style>
                .blog-image {{
                    margin: 2em 0;
                    text-align: center;
                }}
                .blog-image img {{
                    max-width: 100%;
                    border-radius: 8px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }}
                .caption {{
                    margin-top: 1em;
                    color: #666;
                }}
                .timestamp {{
                    color: #999;
                    font-size: 0.9em;
                }}
            </style>
            {html_content}
        </div>
        '''.strip()

        return styled_html

    except Exception as e:
        return f"<div class='error'>Error generating blog: {str(e)}</div>"
