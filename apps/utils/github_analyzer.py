from github import Github
import os
from typing import List, Dict
from openai import OpenAI
import requests
import base64
import re
import json
import asyncio
import aiohttp
from functools import lru_cache
from dotenv import load_dotenv

class GitHubAnalyzer:
    def __init__(self, repo_url: str):
        # Force reload environment variables
        load_dotenv(override=True, verbose=True)
        
        self.repo_url = repo_url
        self.repo_api_url = self._get_api_url()
        
        # Get API key from environment and print for debugging
        openai_api_key = os.getenv('OPENAI_API_KEY')
        if not openai_api_key:
            raise ValueError("OPENAI_API_KEY not found")
        print(f"GitHubAnalyzer loaded API Key: {openai_api_key[:10]}...")
        
        # Initialize with explicit API key
        self.client = OpenAI(api_key=openai_api_key)
        
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
        self.has_video_explanation = False

    def _get_api_url(self):
        """Convert GitHub URL to API URL."""
        if "github.com/" in self.repo_url:
            repo_path = self.repo_url.split("github.com/")[-1].replace(".git", "")
            return f"https://api.github.com/repos/{repo_path}"
        else:
            raise ValueError("Invalid GitHub URL")

    @lru_cache(maxsize=128)
    def _fetch_repo_data(self):
        """Fetch repository metadata with caching."""
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

    async def _fetch_url(self, session, url):
        """Fetch a URL asynchronously."""
        async with session.get(url, headers=self.headers) as response:
            return await response.json()

    async def _fetch_root_files_async(self):
        """Fetch root directory files asynchronously."""
        async with aiohttp.ClientSession() as session:
            response = await self._fetch_url(session, f"{self.repo_api_url}/contents")
            return [f for f in response if f["type"] == "file"]

    def _fetch_root_files(self):
        """Fetch root directory files."""
        return asyncio.run(self._fetch_root_files_async())

    async def _fetch_languages_async(self):
        """Fetch repository languages asynchronously."""
        async with aiohttp.ClientSession() as session:
            response = await self._fetch_url(session, f"{self.repo_api_url}/languages")
            return list(response.keys())

    def _get_languages(self) -> List[str]:
        """Get repository languages."""
        return asyncio.run(self._fetch_languages_async())

    def generate_section(self, section_name: str) -> dict:
        """Generate a specific README section based on repository analysis."""
        try:
            # Base repo info with enhanced metadata
            repo_info = {
                "name": self.repo_data.get("name"),
                "description": self.repo_data.get("description"),
                "languages": self.languages,
                "repo_url": self.repo_url,
                "repo_path": "/".join(self.repo_url.split("/")[-2:]),
                "tagline": self._generate_tagline(),
                "tech_stack_badges": self._generate_tech_stack_badges(self._analyze_tech_stack()["languages"])
            }

            # Add section-specific data
            if section_name in ["structure", "getting_started", "features"]:
                repo_info.update({
                    "tech_stack": self._analyze_tech_stack(),
                    "directory_structure": self._get_directory_structure(),
                    "directory_tree": self._generate_directory_tree(),
                    "file_descriptions": self._generate_file_descriptions()
                })

            prompt = self._get_section_prompt(section_name, repo_info)
            
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a technical documentation expert. Generate detailed, accurate, and specific documentation based on the repository data provided. Focus on practical examples and clear explanations."},
                    {"role": "user", "content": prompt},
                    {"role": "user", "content": f"Repository data:\n{json.dumps(repo_info, indent=2)}"}
                ],
                temperature=0.7,
                max_tokens=1500
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
            "header": """Create a stylish header section with:
                1. Repository name in large heading with a matching icon
                2. A brief tagline
                3. Status badges for license, last commit, top language, and language count
                4. Built with badges for the tech stack
                
                Use this format:
                [<img src="https://raw.githubusercontent.com/PKief/vscode-material-icon-theme/ec559a9f6bfd399b82bb44393651661b08aaf7ba/icons/folder-markdown-open.svg" align="right" width="25%">]()

                # `{name}`

                #### {tagline}

                <p align="left">
                    <img src="https://img.shields.io/github/license/{repo_path}?style=for-the-badge&logo=opensourceinitiative&logoColor=white" alt="license">
                    <img src="https://img.shields.io/github/last-commit/{repo_path}?style=for-the-badge&logo=git&logoColor=white" alt="last-commit">
                    <img src="https://img.shields.io/github/languages/top/{repo_path}?style=for-the-badge" alt="repo-top-language">
                    <img src="https://img.shields.io/github/languages/count/{repo_path}?style=for-the-badge" alt="repo-language-count">
                </p>

                <p align="left">
                    <em>Built with:</em>
                </p>
                <p align="left">
                    {tech_stack_badges}
                </p>
                <br>""",

            "video_demo": """Create a Demo section with:
                1. Screenshots from the video
                2. Clear explanations for each feature shown
                3. Step-by-step walkthrough
                
                Use this format:
                ## 🎥 Demo & Features Walkthrough
                
                <details open>
                <summary>View Demo</summary>
                <br>
                
                {screenshots_and_explanations}
                
                </details>""",

            "toc": """Generate a Table of Contents with:
                1. Clean numbered sections
                2. Emoji icons for each section
                3. Links to all major sections
                
                Use this format:
                ## 🔗 Table of Contents
                
                I. [📍 Overview](#-overview)
                II. [👾 Features](#-features)
                III. [📁 Project Structure](#-project-structure)
                IV. [🚀 Getting Started](#-getting-started)
                V. [📌 Project Roadmap](#-project-roadmap)
                VI. [🔰 Contributing](#-contributing)
                VII. [🎗 License](#-license)
                VIII. [🙌 Acknowledgments](#-acknowledgments)""",

            "features": """Create a detailed Features table with:
                1. Feature categories with icons
                2. Detailed summaries in bullet points
                3. Technical capabilities
                
                Use this format:
                ## 👾 Features

                |    | Feature       | Summary     |
                |:---|:---:         |:---         |
                | ⚙️ | **Architecture** | <ul><li>Key architecture points</li></ul> |
                | 🔩 | **Code Quality** | <ul><li>Quality features</li></ul> |
                | 📄 | **Documentation**| <ul><li>Documentation features</li></ul> |
                {additional_features}""",

            "structure": """Create a Project Structure section with:
                1. Visual directory tree
                2. Detailed file index with descriptions
                3. Collapsible sections
                
                Use this format:
                ## 📁 Project Structure

                ```sh
                {directory_tree}
                ```

                ### 📂 Project Index
                <details open>
                    <summary><b><code>{name}</code></b></summary>
                    {file_descriptions}
                </details>""",

            "getting_started": """Create a Getting Started guide with:
                1. Prerequisites with badges
                2. Installation steps with code blocks
                3. Usage examples
                4. Testing instructions
                
                Use this format:
                ## 🚀 Getting Started

                ### ☑️ Prerequisites
                {prerequisites}

                ### ⚙️ Installation
                {installation_steps}

                ### 🤖 Usage
                {usage_examples}

                ### 🧪 Testing
                {testing_instructions}""",

            "roadmap": """Create a Roadmap section based on:
                1. Current project state
                2. Planned features
                3. Known issues or limitations
                4. Future improvements
                
                Use this format:
                # Roadmap
                
                - [x] Feature 1 - Completed
                - [ ] Feature 2 - In Progress
                - [ ] Feature 3 - Planned
                
                ## Upcoming Features
                1. Feature description
                2. ...""",
            
            "contributing": """Create a Contributing guide that includes:
                1. Code of conduct
                2. Development setup
                3. Pull request process
                4. Coding standards
                
                Based on tech stack: {tech_stack}
                
                Use this format:
                # Contributing
                
                ## Development Setup
                ```bash
                # Setup commands...
                ```
                
                ## Guidelines
                1. Guideline 1
                2. ...""",
            
            "license": """Create a License section that:
                1. States the project license
                2. Includes year and copyright holders
                3. Links to full license file
                
                Use this format:
                # License
                
                This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.""",
            
            "acknowledgments": """Create an Acknowledgments section that includes:
                1. Contributors and maintainers
                2. Third-party libraries used: {dependencies}
                3. Inspirations and references
                4. Special thanks
                
                Use this format:
                # Acknowledgments
                
                ## Contributors
                - Contributor 1
                - ...
                
                ## Built With
                - Technology 1
                - ..."""
        }
        
        try:
            prompt = base_prompts.get(section_name, "Create a detailed section based on the repository content.")
            return prompt.format(**repo_info)
        except Exception as e:
            return base_prompts.get(section_name)

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

    def _fetch_repo_files(self):
        """Fetch all relevant repository files recursively."""
        try:
            def should_analyze_file(file_name: str) -> bool:
                """Determine if a file should be analyzed based on its name."""
                # Files to exclude
                exclude_patterns = [
                    r'\.git',
                    r'\.env',
                    r'__pycache__',
                    r'\.pyc$',
                    r'\.pyo$',
                    r'\.pyd$',
                    r'\.so$',
                    r'\.dll$',
                    r'\.dylib$',
                    r'\.log$',
                    r'\.pot$',
                    r'\.po$',
                    r'\.mo$',
                    r'\.coverage$',
                    r'\.pytest_cache',
                    r'\.DS_Store',
                    r'node_modules',
                    r'\.vscode',
                    r'\.idea',
                    r'\.vs',
                    r'dist',
                    r'build',
                    r'\.cache',
                    r'\.sass-cache',
                    r'\.next',
                    r'\.nuxt',
                    r'\.serverless',
                    r'\.webpack',
                    r'coverage',
                    r'\.nyc_output',
                    r'\.lock$',
                    r'package-lock\.json$',
                    r'yarn\.lock$',
                ]
                
                return not any(re.search(pattern, file_name) for pattern in exclude_patterns)

            def fetch_directory_contents(path=""):
                """Recursively fetch directory contents."""
                files = []
                try:
                    response = requests.get(f"{self.repo_api_url}/contents/{path}", headers=self.headers)
                    if response.status_code == 200:
                        contents = response.json()
                        if isinstance(contents, list):
                            for item in contents:
                                if should_analyze_file(item["name"]):
                                    if item["type"] == "file":
                                        files.append(item)
                                    elif item["type"] == "dir":
                                        files.extend(fetch_directory_contents(f"{path}/{item['name']}" if path else item["name"]))
                except Exception as e:
                    print(f"Error fetching directory contents for {path}: {str(e)}")
                return files

            return fetch_directory_contents()
        except Exception as e:
            print(f"Error in _fetch_repo_files: {str(e)}")
            return []

    def _analyze_file_content(self, file_content: str, file_name: str) -> dict:
        """Analyze file content to extract meaningful information."""
        try:
            info = {
                "type": None,
                "description": "",
                "key_elements": [],
                "dependencies": [],
                "functions": [],
                "classes": [],
                "configs": {}
            }

            # Determine file type and extract relevant information
            if file_name.endswith(('.py', '.js', '.ts', '.java', '.go', '.rb')):
                info["type"] = "source"
                # Extract functions, classes, and imports
                if file_name.endswith('.py'):
                    info.update(self._analyze_python_file(file_content))
                elif file_name.endswith(('.js', '.ts')):
                    info.update(self._analyze_javascript_file(file_content))
                # Add more language analyzers as needed
                
            elif file_name.endswith(('Dockerfile', 'docker-compose.yml', 'docker-compose.yaml')):
                info["type"] = "docker"
                info.update(self._analyze_docker_file(file_content))
                
            elif file_name.endswith(('.yml', '.yaml', '.json', '.toml', '.ini')):
                info["type"] = "config"
                info.update(self._analyze_config_file(file_content))
                
            elif file_name.endswith(('.md', '.rst', '.txt')):
                info["type"] = "documentation"
                info["description"] = "Documentation file containing project information"
                
            return info
        except Exception as e:
            print(f"Error analyzing file {file_name}: {str(e)}")
            return {}

    def _analyze_python_file(self, content: str) -> dict:
        """Analyze Python file content."""
        import ast
        try:
            tree = ast.parse(content)
            functions = []
            classes = []
            imports = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    functions.append({
                        "name": node.name,
                        "args": [arg.arg for arg in node.args.args],
                        "docstring": ast.get_docstring(node) or ""
                    })
                elif isinstance(node, ast.ClassDef):
                    classes.append({
                        "name": node.name,
                        "methods": [m.name for m in node.body if isinstance(m, ast.FunctionDef)],
                        "docstring": ast.get_docstring(node) or ""
                    })
                elif isinstance(node, (ast.Import, ast.ImportFrom)):
                    if isinstance(node, ast.Import):
                        imports.extend(n.name for n in node.names)
                    else:
                        imports.extend(f"{node.module}.{n.name}" for n in node.names)
            
            return {
                "functions": functions,
                "classes": classes,
                "dependencies": imports
            }
        except Exception:
            return {"functions": [], "classes": [], "dependencies": []}

    def _analyze_javascript_file(self, content: str) -> dict:
        """Basic JavaScript/TypeScript file analysis."""
        import re
        
        # Simple regex patterns for demonstration
        function_pattern = r'(?:function\s+(\w+)|const\s+(\w+)\s*=\s*(?:async\s*)?\()'
        class_pattern = r'class\s+(\w+)'
        import_pattern = r'(?:import\s+{\s*([^}]+)\s*}|import\s+(\w+))\s+from\s+[\'"]([^\'"]+)[\'"]'
        
        functions = re.findall(function_pattern, content)
        classes = re.findall(class_pattern, content)
        imports = re.findall(import_pattern, content)
        
        return {
            "functions": [f[0] or f[1] for f in functions],
            "classes": classes,
            "dependencies": [i[2] for i in imports]
        }

    def _analyze_docker_file(self, content: str) -> dict:
        """Analyze Dockerfile content."""
        import re
        
        base_image = re.search(r'FROM\s+([^\s]+)', content)
        expose_ports = re.findall(r'EXPOSE\s+(\d+)', content)
        env_vars = re.findall(r'ENV\s+(\w+)(?:\s+|=)', content)
        
        return {
            "base_image": base_image.group(1) if base_image else None,
            "exposed_ports": expose_ports,
            "environment_variables": env_vars,
            "configs": {
                "base_image": base_image.group(1) if base_image else None,
                "ports": expose_ports,
                "env_vars": env_vars
            }
        }

    def _analyze_config_file(self, content: str) -> dict:
        """Analyze configuration file content."""
        try:
            if content.startswith('{'):
                # JSON file
                import json
                data = json.loads(content)
            else:
                # YAML file
                import yaml
                data = yaml.safe_load(content)
            
            return {
                "configs": data
            }
        except Exception:
            return {"configs": {}}

    def _get_directory_structure(self) -> Dict:
        """Get enhanced directory structure with file analysis."""
        files = self._fetch_repo_files()
        structure = {}
        
        for file in files:
            path_parts = file["path"].split('/')
            current_dict = structure
            
            # Build directory structure
            for part in path_parts[:-1]:
                if part not in current_dict:
                    current_dict[part] = {}
                current_dict = current_dict[part]
            
            # Add file with analysis
            content = self._get_file_content(file["download_url"])
            if content:
                current_dict[path_parts[-1]] = self._analyze_file_content(content, file["name"])
        
        return structure

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

    def _generate_tech_stack_badges(self, tech_stack):
        """Generate badge markdown for technologies."""
        badge_template = '<img src="https://img.shields.io/badge/{tech}-{color}.svg?style=for-the-badge&logo={tech}&logoColor=white" alt="{tech}">'
        badges = []
        
        for tech in tech_stack:
            color = self._get_tech_color(tech)
            badges.append(badge_template.format(tech=tech, color=color))
        
        return "\n\t".join(badges)

    def _get_tech_color(self, tech):
        """Get brand color for technology."""
        colors = {
            "Go": "00ADD8",
            "Python": "3776AB",
            "JavaScript": "F7DF1E",
            "Docker": "2496ED",
            "React": "61DAFB",
            # Add more technology colors as needed
        }
        return colors.get(tech, "gray")

    def _generate_directory_tree(self) -> str:
        """Generate a visual directory tree."""
        try:
            def create_tree(path="", prefix="", is_last=True):
                result = []
                items = self._get_directory_contents(f"{self.repo_api_url}/contents/{path}")
                
                for i, item in enumerate(items):
                    is_last_item = i == len(items) - 1
                    current_prefix = "└── " if is_last_item else "├── "
                    
                    result.append(f"{prefix}{current_prefix}{item['name']}")
                    
                    if item['type'] == 'dir':
                        new_prefix = prefix + ("    " if is_last_item else "│   ")
                        result.extend(create_tree(
                            f"{path}/{item['name']}" if path else item['name'],
                            new_prefix,
                            is_last_item
                        ))
                
                return result

            tree = [self.repo_data.get("name", "project-root") + "/"]
            tree.extend(create_tree())
            return "\n".join(tree)
        except Exception:
            return f"{self.repo_data.get('name', 'project-root')}/\n└── ..."

    def _generate_file_descriptions(self) -> str:
        """Generate file descriptions."""
        try:
            descriptions = []
            for file in self.root_files:
                name = file["name"]
                content = self._get_file_content(file["download_url"])
                
                # Generate a brief description based on file type and content
                if name.endswith(('.md', '.txt')):
                    desc = "Documentation file"
                elif name.endswith(('.py', '.js', '.go', '.java')):
                    desc = "Source code file containing application logic"
                elif name.endswith(('Dockerfile', 'docker-compose.yml')):
                    desc = "Docker configuration for containerization"
                elif name.endswith(('.json', '.yaml', '.yml')):
                    desc = "Configuration file"
                elif name.endswith(('.gitignore', '.env.example')):
                    desc = "Development configuration file"
                else:
                    desc = "Project file"

                descriptions.append(f"- `{name}`: {desc}")

            return "\n".join(descriptions)
        except Exception:
            return "- Project files and directories"

    def _generate_tagline(self) -> str:
        """Generate a tagline for the repository."""
        try:
            description = self.repo_data.get("description", "")
            if description:
                # Use the first sentence of the description or first 100 characters
                tagline = description.split('.')[0][:100]
            else:
                # Generate a generic tagline based on the repository name and language
                main_language = self.languages[0] if self.languages else "Software"
                name = self.repo_data.get("name", "").replace("-", " ").replace("_", " ").title()
                tagline = f"A {main_language} project for {name}!"
            
            return tagline
        except Exception:
            return "Innovative Software Solution"

    def generate_readme(self, selected_sections: List[str], video_explanation: str = None) -> dict:
        """Generate complete README with selected sections and video explanation."""
        try:
            content = []
            
            # Set video explanation flag
            self.has_video_explanation = bool(video_explanation)
            
            # Always start with header
            header = self.generate_section("header")
            if header["success"]:
                content.append(header["content"])

            # Add video explanation if available
            if video_explanation:
                content.append("\n## 📹 Project Overview\n")
                content.append(video_explanation)
                content.append("\n---\n")

            # Generate table of contents based on selected sections
            toc_content = self._generate_toc(selected_sections)
            content.append(toc_content)
            content.append("\n---\n")

            # Generate selected sections
            for section in selected_sections:
                section_content = self.generate_section(section)
                if section_content["success"]:
                    content.append(section_content["content"])
                    content.append("\n---\n")

            return {
                "success": True,
                "content": "\n".join(content)
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def _generate_toc(self, selected_sections: List[str]) -> str:
        """Generate table of contents based on selected sections."""
        section_emojis = {
            "overview": "📍",
            "features": "👾",
            "structure": "📁",
            "getting_started": "🚀",
            "roadmap": "📌",
            "contributing": "🔰",
            "license": "🎗",
            "acknowledgments": "🙌"
        }

        toc_items = []
        if hasattr(self, 'has_video_explanation') and self.has_video_explanation:
            toc_items.append("I. [📹 Project Overview](#-project-overview)")
            counter = 2
        else:
            counter = 1

        for section in selected_sections:
            if section in section_emojis:
                emoji = section_emojis[section]
                title = section.replace('_', ' ').title()
                toc_items.append(f"{counter}. [{emoji} {title}](#{section.lower()})")
                counter += 1

        return """## 🔗 Table of Contents\n\n""" + "\n".join(toc_items) 