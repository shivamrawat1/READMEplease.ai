from notion_client import Client
import requests
from typing import Union, Dict, List
import time
import base64

def create_notion_client(auth_token: str) -> Client:
    """Create a Notion client with the provided authentication token."""
    return Client(auth=auth_token)

def post_to_github(repo_owner: str, repo_name: str, content: str, auth_token: str) -> Dict:
    """
    Create a Pull Request to update README.md in the specified repository.
    
    Args:
        repo_owner: GitHub username or organization name
        repo_name: Repository name
        content: New content for the README
        auth_token: GitHub personal access token with repo scope
    """
    base_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}"
    headers = {
        "Authorization": f"Bearer {auth_token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    try:
        # 1. Get the default branch
        repo_response = requests.get(base_url, headers=headers)
        repo_response.raise_for_status()
        default_branch = repo_response.json()["default_branch"]
        
        # 2. Get current README content and SHA
        readme_response = requests.get(
            f"{base_url}/contents/README.md",
            headers=headers
        )
        readme_response.raise_for_status()
        current_sha = readme_response.json()["sha"]
        
        # 3. Create a new branch
        branch_name = f"update-readme-{int(time.time())}"
        ref_response = requests.post(
            f"{base_url}/git/refs",
            headers=headers,
            json={
                "ref": f"refs/heads/{branch_name}",
                "sha": requests.get(
                    f"{base_url}/git/refs/heads/{default_branch}",
                    headers=headers
                ).json()["object"]["sha"]
            }
        )
        ref_response.raise_for_status()
        
        # 4. Update README in new branch
        update_response = requests.put(
            f"{base_url}/contents/README.md",
            headers=headers,
            json={
                "message": "Update README.md",
                "content": base64.b64encode(content.encode()).decode(),
                "sha": current_sha,
                "branch": branch_name
            }
        )
        update_response.raise_for_status()
        
        # 5. Create Pull Request
        pr_response = requests.post(
            f"{base_url}/pulls",
            headers=headers,
            json={
                "title": "Update README.md",
                "body": "Automated README update",
                "head": branch_name,
                "base": default_branch
            }
        )
        pr_response.raise_for_status()
        
        return pr_response.json()
        
    except Exception as e:
        return {"error": str(e)}

def post_to_notion(page_id: str, content: Union[str, List[Dict]], auth_token: str) -> Dict:
    """
    Post content to a Notion page.
    
    Args:
        page_id: The ID from the Notion page URL (after the last dash)
        content: Text content or structured blocks to append
        auth_token: Notion integration token
    """
    notion = create_notion_client(auth_token)
    
    if isinstance(content, str):
        blocks = [{
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [{
                    "type": "text",
                    "text": {"content": content}
                }]
            }
        }]
    else:
        blocks = content

    try:
        response = notion.blocks.children.append(
            block_id=page_id,
            children=blocks
        )
        return response
    except Exception as e:
        return {"error": str(e)}

def exchange_code_for_token(code: str, client_id: str, client_secret: str) -> str:
    """Exchange OAuth code for access token."""
    response = requests.post(
        'https://github.com/login/oauth/access_token',
        headers={'Accept': 'application/json'},
        data={
            'client_id': client_id,
            'client_secret': client_secret,
            'code': code
        }
    )
    response.raise_for_status()
    return response.json().get('access_token')

def main():
    """Example usage of GitHub README PR creation."""
    github_token = "your-github-token"  # From https://github.com/settings/tokens
    
    # Example README update
    new_content = """# Sample Repository
    
    This is an updated README created via the API.
    
    ## Features
    - Feature 1
    - Feature 2
    
    ## Getting Started
    Clone this repository and...
    """
    
    github_response = post_to_github(
        repo_owner="username",
        repo_name="repository",
        content=new_content,
        auth_token=github_token
    )
    print("GitHub PR Creation Response:", github_response)

if __name__ == "__main__":
    main()
