"""
Agent 4: Orchestrator/Judge Agent - Question Generator
"""
from crewai import Agent, Task
from typing import Dict, Any, Optional

from app.config import ORCHESTRATOR_AGENT_PROMPT, VOICE_SCRIPT_TEMPLATE
from app.tools import QuestionGenerator, LLMClient
from app.utils import get_all_analyses


class OrchestratorAgent:
    """Agent for orchestrating analyses and generating questions"""

    def __init__(self):
        self.question_gen = QuestionGenerator()
        self.llm = LLMClient()

        # Create CrewAI agent
        self.agent = Agent(
            role="Head Judge & Question Generator",
            goal="Synthesize all analyses and generate intelligent, targeted questions for judges",
            backstory="""You are the Head Judge with years of experience evaluating
            hackathon projects. You excel at cross-referencing information, identifying
            inconsistencies, and asking probing questions that reveal true depth.""",
            verbose=True,
            allow_delegation=False
        )

    def generate_questions(self, team_id: str) -> Dict[str, Any]:
        """
        Generate questions from all analyses

        Args:
            team_id: Team identifier

        Returns:
            Dictionary with questions and assessment
        """
        try:
            # Load all analyses
            analyses = get_all_analyses(team_id)

            github_analysis = analyses.get('github')
            ppt_analysis = analyses.get('ppt')
            voice_analysis = analyses.get('voice')

            # Check if we have enough data
            available = [name for name, data in analyses.items() if data is not None]

            if not available:
                return {
                    "error": "No analyses available for this team",
                    "team_id": team_id
                }

            # Handle missing analyses
            if not github_analysis:
                github_analysis = {"status": "not_available"}
            if not ppt_analysis:
                ppt_analysis = {"status": "not_available"}
            if not voice_analysis:
                voice_analysis = {"status": "not_available"}

            # Generate questions using LLM
            questions = self.question_gen.generate_questions(
                github_analysis,
                ppt_analysis,
                voice_analysis
            )

            # Add metadata
            questions['team_id'] = team_id
            questions['analyses_used'] = available
            questions['all_analyses_complete'] = len(available) == 3

            # Generate voice script
            voice_script = self._format_voice_script(questions)
            questions['voice_script'] = voice_script

            # Add summary
            questions['summary'] = self._generate_summary(questions, available)

            return questions

        except Exception as e:
            return {
                "error": f"Error generating questions: {str(e)}",
                "team_id": team_id
            }

    def _format_voice_script(self, questions: Dict[str, Any]) -> str:
        """
        Format questions as voice script for ElevenLabs TTS

        Args:
            questions: Generated questions dictionary

        Returns:
            Voice script string
        """
        script_parts = ["Great presentation, team! I have a few questions for you."]

        question_num = 1
        categories = ["technical", "business", "innovation", "feasibility"]

        for category in categories:
            category_questions = questions.get("questions_by_category", {}).get(category, [])

            # Get high priority questions first
            high_priority = [q for q in category_questions if q.get("priority") == "high"]

            for q in high_priority[:2]:  # Max 2 high-priority per category
                script_parts.append(f"\n\nQuestion {question_num}: {q['question']}")
                question_num += 1

                if question_num > 6:  # Max 6 questions total
                    break

            if question_num > 6:
                break

        script_parts.append("\n\nThank you for your time!")

        return " [PAUSE] ".join(script_parts)

    def _generate_summary(self, questions: Dict[str, Any], available_analyses: list) -> Dict[str, Any]:
        """Generate executive summary"""
        assessment = questions.get('overall_assessment', {})

        return {
            "analyses_completed": available_analyses,
            "overall_score": assessment.get('overall_score', 0),
            "recommendation": self._get_recommendation(assessment.get('overall_score', 0)),
            "total_questions": sum(
                len(questions.get('questions_by_category', {}).get(cat, []))
                for cat in ['technical', 'business', 'innovation', 'feasibility']
            ),
            "high_priority_questions": sum(
                1 for cat in ['technical', 'business', 'innovation', 'feasibility']
                for q in questions.get('questions_by_category', {}).get(cat, [])
                if q.get('priority') == 'high'
            ),
            "key_strengths": questions.get('key_strengths', []),
            "key_concerns": questions.get('key_concerns', [])
        }

    def _get_recommendation(self, overall_score: float) -> str:
        """Get recommendation based on overall score"""
        if overall_score >= 8.5:
            return "Top tier - Strong candidate for winning"
        elif overall_score >= 7.5:
            return "High quality - Competitive project"
        elif overall_score >= 6.5:
            return "Good project - Above average"
        elif overall_score >= 5.0:
            return "Decent effort - Room for improvement"
        else:
            return "Needs significant work"

    def cross_reference_analyses(
        self,
        github_analysis: Dict[str, Any],
        ppt_analysis: Dict[str, Any],
        voice_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Cross-reference all analyses to find inconsistencies and gaps

        Args:
            github_analysis: GitHub analysis data
            ppt_analysis: PPT analysis data
            voice_analysis: Voice analysis data

        Returns:
            Dictionary with cross-reference findings
        """
        findings = {
            "inconsistencies": [],
            "gaps": [],
            "validated_claims": [],
            "unvalidated_claims": []
        }

        # Check for tech stack consistency
        github_tech = set(github_analysis.get('tech_stack', {}).get('languages', []))
        ppt_sections = str(ppt_analysis.get('llm_analysis', '')).lower()

        for tech in github_tech:
            if tech.lower() not in ppt_sections:
                findings["gaps"].append(f"Technology {tech} used in code but not mentioned in presentation")

        # Check for claims validation
        ppt_claims = ppt_analysis.get('key_claims', [])
        voice_claims = voice_analysis.get('verbal_claims', [])

        for claim in ppt_claims + voice_claims:
            # Simple validation - check if numbers/metrics are mentioned consistently
            if any(char.isdigit() for char in claim):
                findings["unvalidated_claims"].append(claim)

        return findings

    def create_task(self, team_id: str) -> Task:
        """Create CrewAI task for orchestration"""
        return Task(
            description=f"""
            Generate intelligent questions for team {team_id} by:

            1. Reading all available analyses (GitHub, PPT, Voice)
            2. Cross-referencing information across sources
            3. Identifying inconsistencies and gaps
            4. Generating categorized, prioritized questions
            5. Creating voice script for judges

            Focus on questions that probe depth, validate claims, and reveal true understanding.
            """,
            agent=self.agent,
            expected_output="Structured questions by category with priorities, voice script, and overall assessment"
        )


# Convenience function
def generate_questions_for_team(team_id: str) -> Dict[str, Any]:
    """
    Generate questions for a team

    Args:
        team_id: Team identifier

    Returns:
        Questions and assessment dictionary
    """
    orchestrator = OrchestratorAgent()
    return orchestrator.generate_questions(team_id)
