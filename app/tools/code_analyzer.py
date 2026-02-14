"""
Code analysis tools
"""
import json
from typing import Dict, Any
from pathlib import Path


class CodeAnalyzer:
    """Tools for analyzing code quality and complexity"""

    def analyze_code_metrics(self, code_structure: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze code metrics from repository structure

        Args:
            code_structure: Repository structure data

        Returns:
            Dictionary with code metrics
        """
        metrics = {
            "complexity_score": 0,
            "organization_score": 0,
            "documentation_score": 0,
            "best_practices_score": 0,
            "overall_quality": 0
        }

        # Check file organization
        metrics["organization_score"] = self._analyze_organization(code_structure)

        # Check documentation
        metrics["documentation_score"] = self._analyze_documentation(code_structure)

        # Check best practices
        metrics["best_practices_score"] = self._analyze_best_practices(code_structure)

        # Calculate overall quality (average)
        scores = [
            metrics["organization_score"],
            metrics["documentation_score"],
            metrics["best_practices_score"]
        ]
        metrics["overall_quality"] = sum(scores) / len(scores) if scores else 0

        return metrics

    def _analyze_organization(self, structure: Dict[str, Any]) -> float:
        """Analyze code organization (0-10)"""
        score = 5.0  # Base score

        # Good indicators
        directories = structure.get("directories", [])

        # Check for common good patterns
        good_patterns = ["src", "lib", "tests", "docs", "components", "utils", "services"]
        found_patterns = sum(1 for pattern in good_patterns if any(pattern in d for d in directories))

        score += min(found_patterns * 0.5, 3.0)  # Up to +3 for good structure

        # Check for modular structure (multiple directories)
        if len(directories) > 5:
            score += 1.0

        # Penalize if too flat (all files in root)
        if len(directories) < 2 and structure.get("total_files", 0) > 10:
            score -= 2.0

        return min(max(score, 0), 10)

    def _analyze_documentation(self, structure: Dict[str, Any]) -> float:
        """Analyze documentation quality (0-10)"""
        score = 0.0

        key_files = structure.get("key_files", {})

        # Check for README
        if any("README" in f for f in key_files.keys()):
            readme_content = next((v for k, v in key_files.items() if "README" in k), "")
            if len(readme_content) > 500:
                score += 5.0  # Good README
            elif len(readme_content) > 100:
                score += 3.0  # Basic README
            else:
                score += 1.0  # Minimal README

        # Check for license
        if "LICENSE" in key_files:
            score += 1.0

        # Check for documentation directory
        directories = structure.get("directories", [])
        if any("doc" in d.lower() for d in directories):
            score += 2.0

        # Check for API documentation markers
        if any(".md" in d for d in directories):
            score += 2.0

        return min(score, 10)

    def _analyze_best_practices(self, structure: Dict[str, Any]) -> float:
        """Analyze best practices adherence (0-10)"""
        score = 5.0  # Base score

        key_files = structure.get("key_files", {})

        # Check for dependency management
        if any(f in key_files for f in ["package.json", "requirements.txt", "Pipfile", "pyproject.toml"]):
            score += 2.0

        # Check for .gitignore
        if ".gitignore" in key_files:
            score += 1.0

        # Check for tests
        directories = structure.get("directories", [])
        if any("test" in d.lower() for d in directories):
            score += 2.0

        # Check for Docker
        if any(f in key_files for f in ["Dockerfile", "docker-compose.yml"]):
            score += 1.0

        # Penalize if no dependency management
        if not any(f in key_files for f in ["package.json", "requirements.txt", "Pipfile", "pyproject.toml", "go.mod", "Cargo.toml"]):
            score -= 2.0

        return min(max(score, 0), 10)

    def identify_tech_stack(self, structure: Dict[str, Any]) -> Dict[str, Any]:
        """
        Identify technology stack from repository

        Args:
            structure: Repository structure data

        Returns:
            Dictionary with tech stack information
        """
        tech_stack = {
            "languages": [],
            "frameworks": [],
            "tools": [],
            "databases": []
        }

        # Identify from file types
        file_types = structure.get("file_types", {})

        # Languages
        language_map = {
            ".py": "Python",
            ".js": "JavaScript",
            ".ts": "TypeScript",
            ".jsx": "React (JavaScript)",
            ".tsx": "React (TypeScript)",
            ".java": "Java",
            ".cpp": "C++",
            ".c": "C",
            ".go": "Go",
            ".rs": "Rust",
            ".rb": "Ruby",
            ".php": "PHP",
            ".swift": "Swift",
            ".kt": "Kotlin"
        }

        for ext, lang in language_map.items():
            if ext in file_types:
                tech_stack["languages"].append(lang)

        # Identify frameworks from key files
        key_files = structure.get("key_files", {})

        if "package.json" in key_files:
            content = key_files["package.json"].lower()
            if "react" in content:
                tech_stack["frameworks"].append("React")
            if "vue" in content:
                tech_stack["frameworks"].append("Vue.js")
            if "angular" in content:
                tech_stack["frameworks"].append("Angular")
            if "express" in content:
                tech_stack["frameworks"].append("Express.js")
            if "next" in content:
                tech_stack["frameworks"].append("Next.js")

        if "requirements.txt" in key_files or "pyproject.toml" in key_files:
            content_req = key_files.get("requirements.txt", "").lower()
            content_proj = key_files.get("pyproject.toml", "").lower()
            content = content_req + content_proj

            if "django" in content:
                tech_stack["frameworks"].append("Django")
            if "flask" in content:
                tech_stack["frameworks"].append("Flask")
            if "fastapi" in content:
                tech_stack["frameworks"].append("FastAPI")

        # Tools
        if "Dockerfile" in key_files:
            tech_stack["tools"].append("Docker")
        if ".github" in str(structure.get("directories", [])):
            tech_stack["tools"].append("GitHub Actions")

        return tech_stack


# Convenience function
def analyze_code_quality(code_structure_json: str) -> str:
    """
    Analyze code quality from structure data

    Args:
        code_structure_json: JSON string with code structure

    Returns:
        str: JSON string with quality analysis
    """
    analyzer = CodeAnalyzer()

    structure = json.loads(code_structure_json)
    metrics = analyzer.analyze_code_metrics(structure)
    tech_stack = analyzer.identify_tech_stack(structure)

    result = {
        "code_metrics": metrics,
        "tech_stack": tech_stack
    }

    return json.dumps(result, indent=2)
