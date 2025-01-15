from github import Github
import os
from typing import List, Dict
from openai import OpenAI
import requests
import base64
import re

class GitHubAnalyzer:
    def __init__(self, repo_url: str):
        self.repo_url = repo_url
        self.repo_api_url = self._get_api_url()
        self.client = OpenAI()

    def _get_api_url(self):
        """Convert GitHub URL to API URL."""
        if "github.com/" in self.repo_url:
            repo_path = self.repo_url.split("github.com/")[-1].replace(".git", "")
            return f"https://api.github.com/repos/{repo_path}"
        else:
            raise ValueError("Invalid GitHub URL")

    def generate_section(self, section_name: str) -> dict:
        """Generate a specific README section based on repository analysis."""
        prompts = {
            "installation": """Create an Installation section for a README.md file. Include:
                - Prerequisites
                - Step-by-step installation instructions
                - Any environment setup needed
                Based on the repository structure and dependencies.
                """,
            "usage": """Create a Usage section for a README.md file. Include:
                - Basic usage examples
                - Common commands or operations
                - Configuration options
                Based on the main functionality of the application.
                """,
            "api": """Create an API Documentation section for a README.md file. Include:
                - Available endpoints
                - Request/response formats
                - Authentication requirements
                Based on the API implementation in the code.
                """,
            "architecture": """Create a Project Architecture section for a README.md file. Include:
                - High-level system design
                - Key components and their interactions
                - Technology stack
                Based on the project structure and dependencies.
                """,
            "contributing": """Create a Contributing section for a README.md file. Include:
                - How to set up the development environment
                - Coding standards
                - Pull request process
                Based on the project's structure and existing patterns.
                """
        }

        try:
            # Get relevant repository data based on section
            repo_data = self._get_section_data(section_name)
            
            # Generate section content using OpenAI
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": prompts[section_name]},
                    {"role": "user", "content": f"Generate README section based on this repository data:\n{repo_data}"}
                ],
                temperature=0.7
            )

            return {
                "success": True,
                "content": response.choices[0].message.content,
                "section": section_name
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "section": section_name
            }

    def _get_section_data(self, section_name: str) -> dict:
        """Gather relevant repository data for section generation."""
        # Get basic repo info
        repo_info = requests.get(self.repo_api_url).json()
        
        data = {
            "name": repo_info.get("name"),
            "description": repo_info.get("description"),
            "languages": self._get_languages(),
            "dependencies": self._get_dependencies(),
            "directory_structure": self._get_directory_structure(),
        }

        if section_name == "api":
            data["routes"] = self._find_routes()
        elif section_name == "architecture":
            data["tech_stack"] = self._analyze_tech_stack()

        return data

    def _get_languages(self) -> List[str]:
        """Get repository languages."""
        languages_url = f"{self.repo_api_url}/languages"
        return list(requests.get(languages_url).json().keys())

    def _get_dependencies(self) -> List[str]:
        """Extract dependencies from requirements.txt or package.json."""
        try:
            contents_url = f"{self.repo_api_url}/contents/requirements.txt"
            response = requests.get(contents_url)
            if response.status_code == 200:
                content = base64.b64decode(response.json()["content"]).decode()
                return [line.strip() for line in content.split("\n") if line.strip()]
        except:
            pass
        return []

    def _get_directory_structure(self, path="") -> Dict:
        """Generate a directory structure of the repository."""
        try:
            contents_url = f"{self.repo_api_url}/contents/{path}"
            contents = requests.get(contents_url).json()
            
            structure = {}
            for item in contents:
                if item["type"] == "dir":
                    structure[item["name"]] = self._get_directory_structure(item["path"])
                else:
                    structure[item["name"]] = item["type"]
            
            return structure
        except:
            return {}

    def _find_routes(self) -> List[Dict]:
        """Find and analyze API routes in the codebase."""
        routes = []
        try:
            # Look for common API file patterns
            for file_pattern in ["app.py", "routes.py", "views.py", "api.py"]:
                contents_url = f"{self.repo_api_url}/contents/{file_pattern}"
                response = requests.get(contents_url)
                if response.status_code == 200:
                    content = base64.b64decode(response.json()["content"]).decode()
                    # Basic route detection - can be enhanced
                    route_patterns = [
                        r"@\w+\.route\(['\"]([^'\"]+)['\"]",  # Flask
                        r"path\(['\"]([^'\"]+)['\"]",  # Django
                    ]
                    for pattern in route_patterns:
                        routes.extend(re.findall(pattern, content))
        except:
            pass
        return routes

    def _analyze_tech_stack(self) -> Dict:
        """Analyze the technology stack used in the repository."""
        return {
            "languages": self._get_languages(),
            "frameworks": self._detect_frameworks(),
            "databases": self._detect_databases()
        }

    def _detect_frameworks(self) -> List[str]:
        """Detect frameworks from requirements.txt or similar files."""
        frameworks = []
        dependencies = self._get_dependencies()
        
        # Common framework patterns
        framework_patterns = {
            "flask": "Flask",
            "django": "Django",
            "fastapi": "FastAPI",
            "pytorch": "PyTorch",
            "tensorflow": "TensorFlow",
            "react": "React",
            "vue": "Vue.js",
            "angular": "Angular"
        }
        
        for dep in dependencies:
            for pattern, framework in framework_patterns.items():
                if pattern in dep.lower():
                    frameworks.append(framework)
        
        return list(set(frameworks))

    def _detect_databases(self) -> List[str]:
        """Detect databases from requirements.txt or similar files."""
        databases = []
        dependencies = self._get_dependencies()
        
        # Common database patterns
        db_patterns = {
            "psycopg": "PostgreSQL",
            "pymongo": "MongoDB",
            "mysql": "MySQL",
            "sqlite": "SQLite",
            "redis": "Redis"
        }
        
        for dep in dependencies:
            for pattern, db in db_patterns.items():
                if pattern in dep.lower():
                    databases.append(db)
        
        return list(set(databases)) 