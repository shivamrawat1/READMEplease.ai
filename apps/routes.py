from app import app
from flask import redirect, request, url_for, session, jsonify, render_template_string
from urllib.parse import urlencode
import os
import secrets
import requests
import base64

# GitHub OAuth Configuration
GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID")
GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET")
GITHUB_REDIRECT_URI = os.getenv("GITHUB_REDIRECT_URI", "http://127.0.0.1:5000/github/callback")

# HTML Template for repository selection
REPO_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>GitHub README Generator</title>
    <style>
        body { font-family: Arial; max-width: 800px; margin: 40px auto; padding: 20px; }
        select { width: 100%; padding: 10px; margin: 20px 0; font-size: 16px; }
        button { background: #2ea44f; color: white; border: none; padding: 10px 20px; 
                 font-size: 16px; cursor: pointer; border-radius: 6px; }
        .message { margin: 20px 0; padding: 10px; border-radius: 4px; }
        .error { background: #ffebee; color: #c62828; }
        .success { background: #e8f5e9; color: #2e7d32; }
    </style>
</head>
<body>
    <h1>Select Repository</h1>
    <div id="message"></div>
    <select id="repoSelect">
        {% for repo in repos %}
            <option value="{{ repo.full_name }}">{{ repo.full_name }}</option>
        {% endfor %}
    </select>
    <button onclick="generateReadme()">Generate README</button>

    <script>
        async function generateReadme() {
            const repo = document.getElementById('repoSelect').value;
            const [owner, name] = repo.split('/');
            
            try {
                const response = await fetch('/github/update-readme', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({repo_owner: owner, repo_name: name})
                });
                
                const data = await response.json();
                const msg = document.getElementById('message');
                
                if (data.error) {
                    msg.className = 'message error';
                    msg.textContent = data.error;
                } else {
                    msg.className = 'message success';
                    msg.innerHTML = `README PR created! <a href="${data.pr_url}" target="_blank">View PR</a>`;
                }
            } catch (error) {
                const msg = document.getElementById('message');
                msg.className = 'message error';
                msg.textContent = 'An error occurred. Please try again.';
            }
        }
    </script>
</body>
</html>
"""

@app.route("/")
def index():
    if 'github_token' not in session:
        return redirect(url_for('github_login'))
    return redirect(url_for('show_repos'))

@app.route("/github/login")
def github_login():
    state = secrets.token_urlsafe(16)
    session['github_oauth_state'] = state
    
    params = {
        "client_id": GITHUB_CLIENT_ID,
        "redirect_uri": GITHUB_REDIRECT_URI,
        "scope": "repo",
        "state": state
    }
    auth_url = f"https://github.com/login/oauth/authorize?{urlencode(params)}"
    return redirect(auth_url)

@app.route("/github/callback")
def github_callback():
    if error := request.args.get("error"):
        return jsonify({"error": error}), 400

    state = request.args.get("state")
    stored_state = session.pop('github_oauth_state', None)
    if not state or state != stored_state:
        return jsonify({"error": "Invalid state parameter"}), 400

    code = request.args.get("code")
    token = exchange_code_for_token(
        code=code,
        client_id=GITHUB_CLIENT_ID,
        client_secret=GITHUB_CLIENT_SECRET
    )
    
    if not token:
        return jsonify({"error": "Failed to obtain access token"}), 400

    session['github_token'] = token
    return redirect(url_for('show_repos'))

@app.route("/github/repos")
def show_repos():
    if 'github_token' not in session:
        return redirect(url_for('github_login'))

    try:
        response = requests.get(
            "https://api.github.com/user/repos",
            headers={
                "Authorization": f"Bearer {session['github_token']}",
                "Accept": "application/vnd.github.v3+json"
            },
            params={"sort": "updated", "per_page": 100}
        )
        response.raise_for_status()
        
        repos = sorted(
            [repo for repo in response.json() if not repo['fork']], 
            key=lambda x: x['full_name'].lower()
        )
        
        return render_template_string(REPO_TEMPLATE, repos=repos)
    except Exception as e:
        return jsonify({"error": f"Failed to fetch repositories: {str(e)}"}), 500

@app.route("/github/update-readme", methods=['POST'])
def update_readme():
    if 'github_token' not in session:
        return jsonify({"error": "Not authenticated"}), 401

    data = request.get_json()
    if not data or 'repo_owner' not in data or 'repo_name' not in data:
        return jsonify({"error": "Missing repository information"}), 400

    try:
        response = post_to_github(
            repo_owner=data['repo_owner'],
            repo_name=data['repo_name'],
            content=f"""# {data['repo_name']}

## Overview
A repository by {data['repo_owner']}.

## Getting Started
```bash
git clone https://github.com/{data['repo_owner']}/{data['repo_name']}.git
cd {data['repo_name']}
```

## Contributing
Feel free to open issues and pull requests!
""",
            oauth_token=session['github_token']
        )
        
        if 'error' in response:
            return jsonify({"error": response['error']}), 500
            
        return jsonify({
            "message": "README update PR created successfully",
            "pr_url": response.get("html_url")
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def exchange_code_for_token(code, client_id, client_secret):
    """Exchange OAuth code for access token."""
    response = requests.post(
        "https://github.com/login/oauth/access_token",
        headers={"Accept": "application/json"},
        data={
            "client_id": client_id,
            "client_secret": client_secret,
            "code": code
        }
    )
    
    if response.status_code == 200:
        return response.json().get("access_token")
    return None

def post_to_github(repo_owner, repo_name, content, oauth_token):
    """Create a pull request with updated README."""
    headers = {
        "Authorization": f"Bearer {oauth_token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    # Get the default branch
    repo_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}"
    repo_info = requests.get(repo_url, headers=headers).json()
    default_branch = repo_info.get("default_branch", "main")
    
    # Create a new branch
    branch_name = f"update-readme-{secrets.token_hex(4)}"
    ref_url = f"{repo_url}/git/refs/heads/{default_branch}"
    ref_response = requests.get(ref_url, headers=headers)
    sha = ref_response.json()["object"]["sha"]
    
    # Create new branch from default branch
    requests.post(
        f"{repo_url}/git/refs",
        headers=headers,
        json={
            "ref": f"refs/heads/{branch_name}",
            "sha": sha
        }
    )
    
    # Get current README if it exists
    readme_url = f"{repo_url}/contents/README.md"
    readme_response = requests.get(readme_url, headers=headers)
    
    # Create or update README
    readme_data = {
        "message": "Update README.md",
        "content": base64.b64encode(content.encode()).decode(),
        "branch": branch_name
    }
    
    if readme_response.status_code == 200:
        readme_data["sha"] = readme_response.json()["sha"]
    
    requests.put(readme_url, headers=headers, json=readme_data)
    
    # Create pull request
    pr_response = requests.post(
        f"{repo_url}/pulls",
        headers=headers,
        json={
            "title": "Update README.md",
            "body": "Automatically generated README update",
            "head": branch_name,
            "base": default_branch
        }
    )
    
    return pr_response.json()