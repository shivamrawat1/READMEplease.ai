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
        self.has_video_explanation = False

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
                model="gpt-4",
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