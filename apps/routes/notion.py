from app import app
from flask import redirect, request, url_for, session, jsonify, render_template
from urllib.parse import urlencode
import os
import secrets
import requests
from notion_client import Client

# Notion OAuth Configuration
NOTION_CLIENT_ID = os.getenv("NOTION_CLIENT_ID")
NOTION_CLIENT_SECRET = os.getenv("NOTION_CLIENT_SECRET")
NOTION_REDIRECT_URI = os.getenv("NOTION_REDIRECT_URI", "http://127.0.0.1:5000/notion/callback")

@app.route("/notion/login")
def notion_login():
    """Start Notion OAuth flow."""
    state = secrets.token_urlsafe(16)
    session['notion_oauth_state'] = state
    
    params = {
        "client_id": NOTION_CLIENT_ID,
        "redirect_uri": NOTION_REDIRECT_URI,
        "response_type": "code",
        "owner": "user",
        "state": state
    }
    auth_url = f"https://api.notion.com/v1/oauth/authorize?{urlencode(params)}"
    return redirect(auth_url)

@app.route("/notion/callback")
def notion_callback():
    """Handle Notion OAuth callback."""
    if error := request.args.get("error"):
        return jsonify({"error": error}), 400

    state = request.args.get("state")
    stored_state = session.pop('notion_oauth_state', None)
    if not state or state != stored_state:
        return jsonify({"error": "Invalid state parameter"}), 400

    code = request.args.get("code")
    
    response = requests.post(
        "https://api.notion.com/v1/oauth/token",
        auth=(NOTION_CLIENT_ID, NOTION_CLIENT_SECRET),
        json={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": NOTION_REDIRECT_URI
        }
    )
    
    if response.status_code != 200:
        return jsonify({"error": "Failed to obtain access token"}), 400
        
    token_data = response.json()
    session['notion_token'] = token_data['access_token']
    session['notion_workspace_id'] = token_data['workspace_id']
    
    return redirect(url_for('show_notion_pages'))

@app.route("/notion/pages")
def show_notion_pages():
    """Show list of user's Notion pages."""
    if 'notion_token' not in session:
        return redirect(url_for('notion_login'))

    notion = Client(auth=session['notion_token'])
    
    try:
        response = notion.search(
            filter={"property": "object", "value": "page"}
        )
        
        pages = response['results']
        return render_template('notion.html', pages=pages)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/notion/create-content", methods=['POST'])
def create_notion_content():
    """Create content in selected Notion page."""
    if 'notion_token' not in session:
        return jsonify({"error": "Not authenticated"}), 401

    data = request.get_json()
    if not data or 'page_id' not in data:
        return jsonify({"error": "Missing page ID"}), 400

    notion = Client(auth=session['notion_token'])
    
    try:
        # Create content in the selected page
        notion.blocks.children.append(
            block_id=data['page_id'],
            children=[
                {
                    "object": "block",
                    "type": "heading_1",
                    "heading_1": {
                        "rich_text": [{"type": "text", "text": {"content": "Generated Content"}}]
                    }
                },
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{"type": "text", "text": {"content": "This content was automatically generated."}}]
                    }
                }
            ]
        )
        
        return jsonify({"message": "Content created successfully!"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
