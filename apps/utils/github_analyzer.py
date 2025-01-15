from github import Github
import os
from typing import List, Dict
from openai import OpenAI
import requests
import base64
import re
import json

class GitHubAnalyzer:
    def __init__(self, repo_url: str):
        self.repo_url = repo_url
        self.repo_api_url = self._get_api_url()
        self.client = OpenAI()
        
        # Base headers required for GitHub API
        self.headers = {
            'User-Agent': 'Documentation-Generator',
            'Accept': 'application/vnd.github.v3+json'
        }
        
        # Add GitHub token if available
        github_token = os.getenv('GITHUB_TOKEN')
        if github_token and github_token != "your_github_token":  # Check if token is valid
            self.headers['Authorization'] = f"token {github_token}"
            print("Using authenticated GitHub API requests")
        else:
            print("Using unauthenticated GitHub API requests (rate limits apply)")
        
        # Only fetch what's needed initially
        self.repo_data = self._fetch_repo_data()
        self.languages = self._get_languages()  # Cache languages
        self.root_files = self._fetch_root_files()  # Only fetch root files initially

    def _get_api_url(self):
        """Convert GitHub URL to API URL."""
        if "github.com/" in self.repo_url:
            repo_path = self.repo_url.split("github.com/")[-1].replace(".git", "")
            return f"https://api.github.com/repos/{repo_path}"
        else:
            raise ValueError("Invalid GitHub URL")

    def _fetch_repo_data(self):
        """Fetch repository metadata."""
        try:
            response = requests.get(self.repo_api_url, headers=self.headers)
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 403:
                # Handle rate limiting
                reset_time = response.headers.get('X-RateLimit-Reset')
                remaining = response.headers.get('X-RateLimit-Remaining')
                message = f"GitHub API rate limit reached. Remaining: {remaining}"
                if reset_time:
                    import datetime
                    reset_datetime = datetime.datetime.fromtimestamp(int(reset_time))
                    message += f", Resets at: {reset_datetime}"
                raise Exception(message)
            elif response.status_code == 404:
                raise Exception("Repository not found. Please check the URL.")
            else:
                raise Exception(f"GitHub API error: {response.status_code}")
        except requests.exceptions.RequestException as e:
            raise Exception(f"Network error: {str(e)}")

    def _fetch_root_files(self):
        """Fetch only root directory files."""
        try:
            response = requests.get(f"{self.repo_api_url}/contents", headers=self.headers)
            if response.status_code == 200:
                return [f for f in response.json() if f["type"] == "file"]
            return []
        except:
            return []

    def generate_section(self, section_name: str) -> dict:
        """Generate a specific README section based on repository analysis."""
        try:
            # Only gather info needed for this specific section
            repo_info = {
                "name": self.repo_data.get("name"),
                "description": self.repo_data.get("description"),
                "languages": self.languages
            }

            # Add section-specific data only if needed
            if section_name == "installation":
                repo_info["dependencies"] = self._get_dependencies()
                repo_info["installation_files"] = self._find_installation_files()
                repo_info["tech_stack"] = self._analyze_tech_stack()
            elif section_name == "api":
                repo_info["api_routes"] = self._find_routes()
                repo_info["tech_stack"] = self._analyze_tech_stack()
            elif section_name == "architecture":
                repo_info["dependencies"] = self._get_dependencies()
                repo_info["tech_stack"] = self._analyze_tech_stack()
                repo_info["directory_structure"] = self._get_directory_structure()
            elif section_name == "usage":
                repo_info["tech_stack"] = self._analyze_tech_stack()
                repo_info["directory_structure"] = self._get_directory_structure()
                repo_info["example_files"] = self._find_example_files()

            prompt = self._get_section_prompt(section_name, repo_info)
            
            # Use GPT-4 for better quality, but with optimized parameters
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a technical documentation expert. Generate detailed, accurate, and specific documentation based on the repository data provided. Focus on practical examples and clear explanations."},
                    {"role": "user", "content": prompt},
                    {"role": "user", "content": f"Repository data:\n{json.dumps(repo_info, indent=2)}"}
                ],
                temperature=0.7,
                max_tokens=1500  # Increased but still limited
            )
            
            return {
                "success": True,
                "content": response.choices[0].message.content
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def _get_section_prompt(self, section_name: str, repo_info: dict) -> str:
        """Get the appropriate prompt for each section."""
        base_prompts = {
            "installation": """Create a detailed Installation section for {name} that includes:
                1. Step-by-step installation instructions using actual dependencies: {dependencies}
                2. Environment setup requirements based on the tech stack: {tech_stack}
                3. Configuration steps if needed
                4. Verification steps to ensure successful installation
                
                Make it specific to this project's actual requirements.
                Use proper markdown formatting with code blocks for commands.""",
            
            "usage": """Create a comprehensive Usage section for {name} that includes:
                1. Practical examples using actual project files
                2. Common use cases based on the project structure
                3. Configuration options with real examples
                4. Tips and best practices specific to this project
                
                Project description: {description}
                Languages: {languages}
                Examples found: {example_files}
                
                Focus on real-world applications and clear examples.
                Use proper markdown formatting with code blocks.""",
            
            "api": """Create a detailed API Documentation section that includes:
                1. Complete endpoint documentation: {api_routes}
                2. Request/response formats with examples
                3. Authentication methods if present
                4. Error handling and status codes
                
                Tech stack: {tech_stack}
                
                Use only actual endpoints found in the code.
                Include curl examples and response schemas.""",
            
            "architecture": """Create a detailed Project Architecture section that includes:
                1. System design overview based on: {directory_structure}
                2. Component interactions and data flow
                3. Technology choices and their justification: {tech_stack}
                4. Dependencies and their purposes: {dependencies}
                
                Project context:
                - Name: {name}
                - Description: {description}
                - Languages: {languages}
                
                Focus on the actual implementation and design decisions.
                Include diagrams descriptions if relevant."""
        }
        
        try:
            prompt = base_prompts.get(section_name, "Create a detailed section based on the repository content.")
            return prompt.format(**repo_info)
        except Exception as e:
            return base_prompts.get(section_name)

    def _get_languages(self) -> List[str]:
        """Get repository languages."""
        try:
            response = requests.get(f"{self.repo_api_url}/languages", headers=self.headers)
            if response.status_code == 200:
                return list(response.json().keys())
        except:
            pass
        return []

    def _get_dependencies(self) -> List[str]:
        """Get project dependencies from root-level dependency files only."""
        dependencies = []
        dependency_files = ["requirements.txt", "package.json", "setup.py"]
        
        for file in self.root_files:
            if file["name"].lower() in dependency_files:
                content = self._get_file_content(file["download_url"])
                if content:
                    dependencies.extend(self._parse_dependencies(content, file["name"]))
        return list(set(dependencies))[:10]  # Limit to top 10 dependencies

    def _get_file_content(self, url: str) -> str:
        """Fetch file content from URL."""
        try:
            response = requests.get(url, headers=self.headers)
            if response.status_code == 200:
                return response.text
        except:
            pass
        return ""

    def _parse_dependencies(self, content: str, filename: str) -> List[str]:
        """Parse dependencies from different file types."""
        if filename == "requirements.txt":
            return [line.split('==')[0] for line in content.splitlines() if line and not line.startswith('#')]
        elif filename == "package.json":
            try:
                data = json.loads(content)
                return list(data.get("dependencies", {}).keys()) + list(data.get("devDependencies", {}).keys())
            except:
                return []
        return []

    def _get_directory_structure(self) -> Dict:
        """Get simplified directory structure (max 2 levels deep)."""
        def create_tree(files, depth=0):
            if depth >= 2:  # Limit depth to 2 levels
                return "..."
            
            tree = {}
            for file in files:
                if file["type"] == "dir" and depth < 2:
                    contents = self._get_directory_contents(file["url"])
                    if contents:
                        tree[file["name"]] = create_tree(contents, depth + 1)
                else:
                    tree[file["name"]] = None
            return tree

        try:
            response = requests.get(f"{self.repo_api_url}/contents", headers=self.headers)
            if response.status_code == 200:
                return create_tree(response.json())
            return {}
        except:
            return {}

    def _get_directory_contents(self, url: str) -> Dict:
        """Get contents of a directory."""
        try:
            response = requests.get(url, headers=self.headers)
            if response.status_code == 200:
                files = response.json()
                return {f["name"]: None if f["type"] == "file" else self._get_directory_contents(f["url"]) 
                       for f in files}
        except:
            pass
        return {}

    def _find_routes(self) -> List[Dict]:
        """Find API routes in the codebase."""
        routes = []
        for file in self.files:
            if file["name"].endswith((".py", ".js", ".ts")):
                content = self._get_file_content(file["download_url"])
                routes.extend(self._parse_routes(content))
        return routes

    def _parse_routes(self, content: str) -> List[Dict]:
        """Parse routes from file content."""
        routes = []
        # Flask route pattern
        flask_pattern = r'@app\.route\([\'"]([^\'"]+)[\'"](,\s*methods=\[([^\]]+)\])?\)'
        matches = re.finditer(flask_pattern, content)
        for match in matches:
            routes.append({
                "path": match.group(1),
                "methods": match.group(3).replace("'", "").replace('"', "").split(", ") if match.group(3) else ["GET"]
            })
        return routes

    def _find_installation_files(self) -> List[str]:
        """Find files related to installation."""
        return [f["name"] for f in self.files if f["name"].lower() in [
            "requirements.txt", "setup.py", "package.json", "dockerfile", "docker-compose.yml",
            "makefile", "install.sh", "setup.sh"
        ]]

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

    def _find_example_files(self) -> List[Dict]:
        """Find example files and their content."""
        example_files = []
        example_patterns = [
            'example', 'demo', 'sample', 'test', 'main.py', 'index.js',
            'app.py', 'server.py', 'client.py'
        ]
        
        for file in self.root_files:
            name = file["name"].lower()
            if any(pattern in name for pattern in example_patterns):
                content = self._get_file_content(file["download_url"])
                if content:
                    example_files.append({
                        "name": file["name"],
                        "content": content[:1000]  # Limit content size
                    })
        return example_files[:3]  # Limit to 3 examples 