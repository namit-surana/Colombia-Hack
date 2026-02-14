"""
Agent 1: GitHub Code Analyzer
"""
from crewai import Agent, Task
from langchain.tools import Tool
from typing import Dict, Any

from app.config import GITHUB_AGENT_PROMPT
from app.tools import GitHubAnalyzer, CodeAnalyzer, LLMClient
from app.utils import save_analysis


class GitHubAnalyzerAgent:
    """Agent for analyzing GitHub repositories"""

    def __init__(self):
        self.github_tool = GitHubAnalyzer()
        self.code_tool = CodeAnalyzer()
        self.llm = LLMClient()

        # Create CrewAI agent
        self.agent = Agent(
            role="Senior Code Architect",
            goal="Analyze GitHub repository for technical quality, architecture, and innovation",
            backstory="""You are a Senior Code Architect with 15 years of experience
            evaluating software projects. You excel at identifying code quality issues,
            architectural patterns, and innovative technical approaches.""",
            tools=self._create_tools(),
            verbose=True,
            allow_delegation=False
        )

    def _create_tools(self):
        """Create LangChain tools for the agent"""

        def analyze_repo(github_url: str) -> str:
            """Analyze GitHub repository"""
            # Get repository stats
            stats = self.github_tool.get_repository_stats(github_url)

            # Get code structure
            structure = self.github_tool.clone_and_analyze_structure(github_url)

            # Analyze code quality
            metrics = self.code_tool.analyze_code_metrics(structure)
            tech_stack = self.code_tool.identify_tech_stack(structure)

            result = {
                "repository_stats": stats,
                "code_structure": structure,
                "code_metrics": metrics,
                "tech_stack": tech_stack
            }

            import json
            return json.dumps(result, indent=2)

        return [
            Tool(
                name="GitHub_Repository_Analyzer",
                func=analyze_repo,
                description="Analyzes a GitHub repository including stats, code structure, and quality metrics. Input: GitHub URL"
            )
        ]

    def analyze(self, github_url: str, team_id: str) -> Dict[str, Any]:
        """
        Analyze GitHub repository

        Args:
            github_url: GitHub repository URL
            team_id: Team identifier

        Returns:
            Dictionary with analysis results
        """
        try:
            # Get repository data
            stats = self.github_tool.get_repository_stats(github_url)

            if "error" in stats:
                return {
                    "error": stats["error"],
                    "github_url": github_url
                }

            structure = self.github_tool.clone_and_analyze_structure(github_url)

            if "error" in structure:
                structure = {"error": structure["error"], "directories": [], "total_files": 0}

            # Analyze code quality
            metrics = self.code_tool.analyze_code_metrics(structure)
            tech_stack = self.code_tool.identify_tech_stack(structure)

            # Use LLM to generate detailed analysis
            context = f"""
Repository Statistics:
- Name: {stats.get('name')}
- Description: {stats.get('description')}
- Stars: {stats.get('stars')}
- Language: {stats.get('language')}
- Languages: {stats.get('languages')}
- Commits: {stats.get('commit_count')}
- Contributors: {stats.get('contributor_count')}

Code Structure:
- Total Files: {structure.get('total_files')}
- Total Lines: {structure.get('total_lines')}
- File Types: {structure.get('file_types')}
- Directories: {len(structure.get('directories', []))}

Code Metrics:
- Organization Score: {metrics.get('organization_score')}/10
- Documentation Score: {metrics.get('documentation_score')}/10
- Best Practices Score: {metrics.get('best_practices_score')}/10
- Overall Quality: {metrics.get('overall_quality')}/10

Tech Stack:
- Languages: {tech_stack.get('languages')}
- Frameworks: {tech_stack.get('frameworks')}

README Preview:
{stats.get('readme_content', 'No README')[:1000]}
"""

            analysis_prompt = """
Based on this GitHub repository data, provide a structured analysis for hackathon evaluation:

1. Technical Score (0-10): Rate overall technical quality
2. Architecture Pattern: Identify the architectural approach (e.g., MVC, microservices, monolithic)
3. Code Quality Assessment:
   - Organization: How well is code structured?
   - Best Practices: Does it follow modern best practices?
   - Concerns: Any red flags or issues?
4. Innovation Highlights: What's technically innovative or impressive?
5. Question Areas: What technical questions should judges ask?

Return a concise, specific analysis focusing on what matters for hackathon evaluation.
"""

            llm_analysis = self.llm.analyze_with_context(context, analysis_prompt, GITHUB_AGENT_PROMPT)

            # Compile final analysis
            analysis = {
                "github_url": github_url,
                "repository_stats": {
                    "name": stats.get('name'),
                    "description": stats.get('description'),
                    "stars": stats.get('stars'),
                    "commits": stats.get('commit_count'),
                    "contributors": stats.get('contributor_count'),
                    "languages": stats.get('languages'),
                    "has_readme": stats.get('has_readme'),
                },
                "code_structure": {
                    "total_files": structure.get('total_files', 0),
                    "total_lines": structure.get('total_lines', 0),
                    "directories_count": len(structure.get('directories', [])),
                    "file_types": structure.get('file_types', {}),
                },
                "code_quality": {
                    "organization_score": metrics.get('organization_score'),
                    "documentation_score": metrics.get('documentation_score'),
                    "best_practices_score": metrics.get('best_practices_score'),
                    "overall_quality": metrics.get('overall_quality'),
                },
                "tech_stack": tech_stack,
                "technical_score": metrics.get('overall_quality'),  # Use overall quality as technical score
                "llm_analysis": llm_analysis,
                "question_areas": [
                    "architecture_decisions",
                    "code_quality",
                    "scalability",
                    "tech_stack_choices"
                ]
            }

            # Save analysis
            save_analysis(team_id, 'github', analysis)

            return analysis

        except Exception as e:
            error_result = {
                "error": f"Error analyzing GitHub repository: {str(e)}",
                "github_url": github_url
            }
            save_analysis(team_id, 'github', error_result)
            return error_result

    def create_task(self, github_url: str) -> Task:
        """Create CrewAI task for GitHub analysis"""
        return Task(
            description=f"""
            Analyze the GitHub repository at: {github_url}

            Evaluate:
            1. Code quality and organization
            2. Technical architecture
            3. Tech stack choices
            4. Innovation and implementation
            5. Documentation quality

            Provide a technical score (0-10) and identify question areas for judges.
            """,
            agent=self.agent,
            expected_output="Structured analysis with technical score, architecture assessment, and question areas"
        )
