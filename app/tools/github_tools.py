"""
GitHub analysis tools
"""
import os
import tempfile
from pathlib import Path
from typing import Dict, Any, Optional
from github import Github, GithubException
import git
from app.config import settings


class GitHubAnalyzer:
    """Tools for analyzing GitHub repositories"""

    def __init__(self):
        self.client = Github(settings.GITHUB_TOKEN)

    def extract_repo_info(self, github_url: str) -> Optional[tuple[str, str]]:
        """
        Extract owner and repo name from GitHub URL

        Args:
            github_url: GitHub repository URL

        Returns:
            (owner, repo) or None
        """
        try:
            # Handle different URL formats
            # https://github.com/owner/repo
            # https://github.com/owner/repo.git
            # github.com/owner/repo
            url = github_url.replace('https://', '').replace('http://', '').replace('.git', '')
            parts = url.split('/')

            if 'github.com' in parts[0]:
                owner = parts[1]
                repo = parts[2]
                return owner, repo

            return None
        except Exception as e:
            print(f"Error extracting repo info: {e}")
            return None

    def get_repository_stats(self, github_url: str) -> Dict[str, Any]:
        """
        Get repository statistics using GitHub API

        Args:
            github_url: GitHub repository URL

        Returns:
            Dictionary with repository stats
        """
        try:
            repo_info = self.extract_repo_info(github_url)
            if not repo_info:
                return {"error": "Invalid GitHub URL"}

            owner, repo_name = repo_info
            repo = self.client.get_repo(f"{owner}/{repo_name}")

            # Get basic stats
            stats = {
                "name": repo.name,
                "description": repo.description,
                "stars": repo.stargazers_count,
                "forks": repo.forks_count,
                "watchers": repo.watchers_count,
                "open_issues": repo.open_issues_count,
                "created_at": repo.created_at.isoformat() if repo.created_at else None,
                "updated_at": repo.updated_at.isoformat() if repo.updated_at else None,
                "language": repo.language,
                "languages": repo.get_languages(),
                "size_kb": repo.size,
                "default_branch": repo.default_branch,
                "has_wiki": repo.has_wiki,
                "has_issues": repo.has_issues,
            }

            # Get commit count
            try:
                commits = list(repo.get_commits()[:100])  # Get last 100 commits
                stats["commit_count"] = len(commits)
                stats["recent_commits"] = [
                    {
                        "sha": c.sha[:7],
                        "message": c.commit.message.split('\n')[0][:100],
                        "author": c.commit.author.name if c.commit.author else "Unknown",
                        "date": c.commit.author.date.isoformat() if c.commit.author else None
                    }
                    for c in commits[:10]
                ]
            except:
                stats["commit_count"] = 0
                stats["recent_commits"] = []

            # Get contributors
            try:
                contributors = list(repo.get_contributors()[:10])
                stats["contributor_count"] = len(contributors)
                stats["top_contributors"] = [
                    {"login": c.login, "contributions": c.contributions}
                    for c in contributors[:5]
                ]
            except:
                stats["contributor_count"] = 0
                stats["top_contributors"] = []

            # Get README
            try:
                readme = repo.get_readme()
                stats["readme_content"] = readme.decoded_content.decode('utf-8')[:5000]  # First 5000 chars
                stats["has_readme"] = True
            except:
                stats["readme_content"] = ""
                stats["has_readme"] = False

            return stats

        except GithubException as e:
            return {"error": f"GitHub API error: {str(e)}"}
        except Exception as e:
            return {"error": f"Error analyzing repository: {str(e)}"}

    def clone_and_analyze_structure(self, github_url: str) -> Dict[str, Any]:
        """
        Clone repository and analyze file structure

        Args:
            github_url: GitHub repository URL

        Returns:
            Dictionary with file structure analysis
        """
        temp_dir = None
        try:
            # Create temporary directory
            temp_dir = tempfile.mkdtemp(dir=settings.TEMP_DIR)

            # Clone repository (shallow)
            print(f"Cloning repository to {temp_dir}...")
            repo = git.Repo.clone_from(
                github_url,
                temp_dir,
                depth=settings.GITHUB_CLONE_DEPTH
            )

            # Analyze structure
            analysis = self._analyze_directory_structure(Path(temp_dir))

            return analysis

        except git.GitCommandError as e:
            return {"error": f"Git clone error: {str(e)}"}
        except Exception as e:
            return {"error": f"Error analyzing structure: {str(e)}"}
        finally:
            # Cleanup
            if temp_dir and os.path.exists(temp_dir):
                import shutil
                try:
                    shutil.rmtree(temp_dir)
                except:
                    pass

    def _analyze_directory_structure(self, repo_path: Path) -> Dict[str, Any]:
        """Analyze repository directory structure"""
        analysis = {
            "total_files": 0,
            "total_lines": 0,
            "file_types": {},
            "directories": [],
            "key_files": {},
            "structure": {}
        }

        # Common important files to look for
        important_files = {
            "README.md", "README.txt", "README",
            "package.json", "requirements.txt", "Pipfile", "pyproject.toml",
            "docker-compose.yml", "Dockerfile",
            ".gitignore", "LICENSE",
            "main.py", "app.py", "index.js", "server.js"
        }

        for file_path in repo_path.rglob('*'):
            # Skip .git directory
            if '.git' in file_path.parts:
                continue

            if file_path.is_file():
                analysis["total_files"] += 1

                # File extension
                ext = file_path.suffix or "no_extension"
                analysis["file_types"][ext] = analysis["file_types"].get(ext, 0) + 1

                # Check for important files
                if file_path.name in important_files:
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read(2000)  # First 2000 chars
                        analysis["key_files"][file_path.name] = content
                    except:
                        pass

                # Count lines for code files
                if ext in ['.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.cpp', '.c', '.go', '.rs']:
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            lines = len(f.readlines())
                            analysis["total_lines"] += lines
                    except:
                        pass

            elif file_path.is_dir():
                rel_path = file_path.relative_to(repo_path)
                if rel_path.parts[0] != '.git':
                    analysis["directories"].append(str(rel_path))

        return analysis


# Convenience function for CrewAI tools
def analyze_github_repo(github_url: str) -> str:
    """
    Analyze GitHub repository (for use as CrewAI tool)

    Args:
        github_url: GitHub repository URL

    Returns:
        str: JSON string with analysis
    """
    import json
    analyzer = GitHubAnalyzer()

    # Get stats via API
    stats = analyzer.get_repository_stats(github_url)

    # Get structure by cloning
    structure = analyzer.clone_and_analyze_structure(github_url)

    result = {
        "repository_stats": stats,
        "code_structure": structure
    }

    return json.dumps(result, indent=2)
