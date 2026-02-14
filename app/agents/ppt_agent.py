"""
Agent 2: PPT/Presentation Analyzer
"""
from crewai import Agent, Task
from langchain.tools import Tool
from typing import Dict, Any

from app.config import PPT_AGENT_PROMPT
from app.tools import PPTAnalyzer, LLMClient
from app.utils import save_analysis


class PPTAnalyzerAgent:
    """Agent for analyzing PowerPoint presentations"""

    def __init__(self):
        self.ppt_tool = PPTAnalyzer()
        self.llm = LLMClient()

        # Create CrewAI agent
        self.agent = Agent(
            role="Business Analyst",
            goal="Evaluate business viability, problem-solution fit, and presentation quality",
            backstory="""You are a Business Analyst with an MBA and expertise in
            evaluating early-stage ventures. You excel at assessing market opportunity,
            business models, and presentation effectiveness.""",
            tools=self._create_tools(),
            verbose=True,
            allow_delegation=False
        )

    def _create_tools(self):
        """Create LangChain tools for the agent"""

        def analyze_presentation(ppt_path: str) -> str:
            """Analyze PowerPoint presentation"""
            # Extract content
            extraction = self.ppt_tool.extract_text_from_ppt(ppt_path)

            # Analyze structure
            structure = self.ppt_tool.analyze_presentation_structure(ppt_path)

            result = {
                "content_extraction": extraction,
                "structural_analysis": structure
            }

            import json
            return json.dumps(result, indent=2)

        return [
            Tool(
                name="PPT_Analyzer",
                func=analyze_presentation,
                description="Analyzes a PowerPoint presentation including content, structure, and key messages. Input: Path to PPT file"
            )
        ]

    def analyze(self, ppt_path: str, team_id: str) -> Dict[str, Any]:
        """
        Analyze PowerPoint presentation

        Args:
            ppt_path: Path to PPT/PPTX file
            team_id: Team identifier

        Returns:
            Dictionary with analysis results
        """
        try:
            # Extract content
            extraction = self.ppt_tool.extract_text_from_ppt(ppt_path)

            if "error" in extraction:
                return {
                    "error": extraction["error"],
                    "ppt_path": ppt_path
                }

            # Analyze structure
            structure = self.ppt_tool.analyze_presentation_structure(ppt_path)

            # Use LLM to analyze content
            all_text = extraction.get('all_text', '')[:10000]  # First 10k chars
            slides_summary = "\n".join([
                f"Slide {s['slide_number']}: {s['title']}\n  Content: {' '.join(s['content'][:3])}"
                for s in extraction.get('slides', [])[:15]  # First 15 slides
            ])

            context = f"""
Presentation Overview:
- Total Slides: {extraction.get('slide_count')}
- Has Title Slide: {structure.get('has_title_slide')}
- Sections: {structure.get('sections_identified')}

Slide Breakdown:
{slides_summary}

Full Text Content (excerpt):
{all_text[:3000]}

Visual Elements:
- Images: {structure.get('visual_elements', {}).get('images', 0)}
- Charts: {structure.get('visual_elements', {}).get('charts', 0)}
- Tables: {structure.get('visual_elements', {}).get('tables', 0)}
"""

            analysis_prompt = """
Based on this presentation data, provide a structured business analysis for hackathon evaluation:

1. Presentation Score (0-10): Rate overall presentation quality
2. Problem Statement: What problem are they solving? Is it clear?
3. Solution Clarity: How well explained is their solution?
4. Business Viability:
   - Market opportunity size
   - Revenue model
   - Competitive positioning
   - Go-to-market strategy
5. Key Claims: List any specific claims (metrics, partnerships, validation)
6. Concerns: What's missing or unclear?
7. Question Areas: What business questions should judges ask?

Return a concise, specific analysis focusing on business viability for hackathon evaluation.
"""

            llm_analysis = self.llm.analyze_with_context(context, analysis_prompt, PPT_AGENT_PROMPT)

            # Extract key claims from slides
            key_claims = self._extract_claims(extraction)

            # Compile final analysis
            analysis = {
                "ppt_path": ppt_path,
                "slide_count": extraction.get('slide_count'),
                "presentation_structure": {
                    "has_title_slide": structure.get('has_title_slide'),
                    "sections": structure.get('sections_identified', []),
                    "key_slides": structure.get('key_slides', []),
                },
                "content_analysis": {
                    "text_heavy_slides": structure.get('content_distribution', {}).get('text_heavy_slides', 0),
                    "visual_heavy_slides": structure.get('content_distribution', {}).get('visual_heavy_slides', 0),
                    "balanced_slides": structure.get('content_distribution', {}).get('balanced_slides', 0),
                },
                "visual_elements": structure.get('visual_elements', {}),
                "key_claims": key_claims,
                "presentation_score": 7.5,  # Default, can be overridden by LLM analysis
                "llm_analysis": llm_analysis,
                "question_areas": [
                    "problem_validation",
                    "market_opportunity",
                    "competitive_advantage",
                    "business_model"
                ]
            }

            # Save analysis
            save_analysis(team_id, 'ppt', analysis)

            return analysis

        except Exception as e:
            error_result = {
                "error": f"Error analyzing presentation: {str(e)}",
                "ppt_path": ppt_path
            }
            save_analysis(team_id, 'ppt', error_result)
            return error_result

    def _extract_claims(self, extraction: Dict[str, Any]) -> list:
        """Extract potential claims from presentation text"""
        claims = []
        all_text = extraction.get('all_text', '').lower()

        # Look for common claim patterns
        claim_keywords = [
            'users', 'customers', 'revenue', 'growth', 'increase', 'decrease',
            'faster', 'better', 'partnership', 'tested', 'validated',
            'compliant', 'certified', 'patent', 'market share'
        ]

        sentences = all_text.split('.')
        for sentence in sentences:
            if any(keyword in sentence for keyword in claim_keywords):
                # Check if it contains numbers (likely a claim)
                if any(char.isdigit() for char in sentence):
                    claims.append(sentence.strip()[:200])  # Max 200 chars

        return claims[:10]  # Max 10 claims

    def create_task(self, ppt_path: str) -> Task:
        """Create CrewAI task for PPT analysis"""
        return Task(
            description=f"""
            Analyze the presentation at: {ppt_path}

            Evaluate:
            1. Problem statement clarity
            2. Solution explanation
            3. Business model viability
            4. Market opportunity
            5. Presentation quality and flow

            Provide a presentation score (0-10) and identify question areas for judges.
            """,
            agent=self.agent,
            expected_output="Structured analysis with presentation score, business assessment, and question areas"
        )
