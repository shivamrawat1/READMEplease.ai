import markdown
import re
from typing import List, Dict
from markdown.extensions import Extension
from markdown.preprocessors import Preprocessor
from .cloud_storage import CloudStorage

class HTMLPreservationExtension(Extension):
    def extendMarkdown(self, md):
        md.preprocessors.register(HTMLPreservationPreprocessor(md), 'html_preservation', 175)

class HTMLPreservationPreprocessor(Preprocessor):
    def run(self, lines):
        new_lines = []
        for line in lines:
            if '<div class="blog-image">' in line:
                new_lines.extend(['', line, ''])
            else:
                new_lines.append(line)
        return new_lines

def generate_markdown_content(blog_content: str, screenshots: List[Dict]) -> dict:
    """Generate markdown content with cloud-hosted image references."""
    try:
        if not blog_content:
            return {
                "raw": "Error: No blog content provided",
                "html": "<p>Error: No blog content provided</p>"
            }
            
        if not screenshots:
            return {
                "raw": blog_content,
                "html": markdown.markdown(blog_content)
            }

        # Initialize cloud storage
        cloud_storage = CloudStorage()
        
        # Create a mapping of available screenshots
        screenshot_map = {round(s['timestamp'], 1): s for s in screenshots}
        
        # Extract screenshot markers and their descriptions
        marker_pattern = r'<screenshot\s+time="([\d.]+)"\s+description="([^"]+)"\s*/>'
        markers = list(re.finditer(marker_pattern, blog_content))

        # Create two versions: one for markdown file and one for HTML preview
        markdown_content = blog_content
        html_content = blog_content

        for marker in markers:
            timestamp = float(marker.group(1))
            description = marker.group(2)

            closest_timestamp = min(screenshot_map.keys(),
                                key=lambda x: abs(x - timestamp),
                                default=None)

            if closest_timestamp and abs(closest_timestamp - timestamp) < 5.0:
                screenshot = screenshot_map[closest_timestamp]
                
                # Upload image and get URL
                filename = f"screenshot_{closest_timestamp:.2f}.jpg"
                image_url = cloud_storage.upload_image(screenshot['image_base64'], filename)
                
                if image_url:
                    # Use cloud URL for both markdown and HTML
                    markdown_image = f"\n\n![{description.strip()}]({image_url})\n"
                    markdown_image += f"*{description.strip()}*\n\n"
                    
                    html_image = f'''
<div class="blog-image">
    <img src="{image_url}"
         alt="{description.strip()}">
    <div class="caption">
        <p>{description.strip()}</p>
    </div>
</div>
'''
                else:
                    markdown_image = f"\n\n[Image upload failed: {description.strip()}]\n\n"
                    html_image = f'\n<div class="placeholder">[Image upload failed: {description.strip()}]</div>\n'
            else:
                markdown_image = f"\n\n[Image placeholder: {description.strip()}]\n\n"
                html_image = f'\n<div class="placeholder">[Image placeholder: {description.strip()}]</div>\n'

            markdown_content = markdown_content.replace(marker.group(0), markdown_image)
            html_content = html_content.replace(marker.group(0), html_image)

        html_content = markdown.markdown(
            html_content,
            extensions=['extra', HTMLPreservationExtension()],
            output_format='html5'
        )

        return {
            "raw": markdown_content,
            "html": html_content
        }

    except Exception as e:
        return {
            "raw": f"Error generating markdown: {str(e)}",
            "html": f"<p>Error generating markdown: {str(e)}</p>"
        }
