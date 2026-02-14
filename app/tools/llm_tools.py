"""
LLM integration tools
"""
import json
from typing import Dict, Any, List
from app.config import settings


class LLMClient:
    """Client for LLM API calls"""

    def __init__(self):
        self.provider = settings.LLM_PROVIDER
        self.model = settings.LLM_MODEL

        if self.provider == "openai":
            from openai import OpenAI
            self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        elif self.provider == "anthropic":
            from anthropic import Anthropic
            self.client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        else:
            raise ValueError(f"Unsupported LLM provider: {self.provider}")

    def generate_completion(self, prompt: str, system_prompt: str = None, temperature: float = None) -> str:
        """
        Generate completion from LLM

        Args:
            prompt: User prompt
            system_prompt: System prompt (optional)
            temperature: Temperature setting (optional)

        Returns:
            str: Generated text
        """
        if temperature is None:
            temperature = settings.LLM_TEMPERATURE

        try:
            if self.provider == "openai":
                messages = []
                if system_prompt:
                    messages.append({"role": "system", "content": system_prompt})
                messages.append({"role": "user", "content": prompt})

                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=settings.LLM_MAX_TOKENS
                )
                return response.choices[0].message.content

            elif self.provider == "anthropic":
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=settings.LLM_MAX_TOKENS,
                    temperature=temperature,
                    system=system_prompt if system_prompt else "",
                    messages=[
                        {"role": "user", "content": prompt}
                    ]
                )
                return response.content[0].text

        except Exception as e:
            return f"Error generating completion: {str(e)}"

    def analyze_with_context(self, context: str, question: str, system_prompt: str = None) -> str:
        """
        Analyze data with context and question

        Args:
            context: Context data (e.g., code, presentation content)
            question: Question to answer
            system_prompt: System prompt for role definition

        Returns:
            str: Analysis result
        """
        prompt = f"""
Context:
{context}

Question:
{question}

Please provide a detailed, structured analysis.
"""
        return self.generate_completion(prompt, system_prompt)

    def extract_structured_data(self, text: str, schema: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract structured data from text using LLM

        Args:
            text: Text to analyze
            schema: Expected output schema

        Returns:
            Dictionary with extracted data
        """
        prompt = f"""
Extract information from the following text and return it in JSON format according to this schema:

Schema:
{json.dumps(schema, indent=2)}

Text:
{text}

Return ONLY valid JSON matching the schema.
"""

        response = self.generate_completion(prompt)

        # Try to parse JSON
        try:
            # Find JSON in response (may have extra text)
            start = response.find('{')
            end = response.rfind('}') + 1
            if start != -1 and end > start:
                json_str = response[start:end]
                return json.loads(json_str)
            else:
                return {"error": "No JSON found in response"}
        except json.JSONDecodeError as e:
            return {"error": f"JSON parse error: {str(e)}", "raw_response": response}


class QuestionGenerator:
    """Generate intelligent questions using LLM"""

    def __init__(self):
        self.llm = LLMClient()

    def generate_questions(
        self,
        github_analysis: Dict[str, Any],
        ppt_analysis: Dict[str, Any],
        voice_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate categorized questions from all analyses

        Args:
            github_analysis: GitHub analysis data
            ppt_analysis: PPT analysis data
            voice_analysis: Voice analysis data

        Returns:
            Dictionary with generated questions
        """
        # Prepare context
        context = f"""
# GitHub Analysis Summary:
{json.dumps(github_analysis, indent=2)}

# Presentation (PPT) Analysis Summary:
{json.dumps(ppt_analysis, indent=2)}

# Voice Presentation Analysis Summary:
{json.dumps(voice_analysis, indent=2)}
"""

        prompt = """
Based on the three analyses provided (GitHub code, PPT presentation, and voice presentation), generate intelligent questions for hackathon judges to ask the team.

Your task:
1. Cross-reference information across all three sources
2. Identify inconsistencies (e.g., claims in PPT not supported by code)
3. Find gaps (important information missing)
4. Detect unvalidated claims (metrics without evidence)
5. Generate specific, actionable questions

Generate questions in these categories:
- Technical (code quality, architecture, implementation)
- Business (market, revenue model, competitive advantage)
- Innovation (novel approaches, creativity)
- Feasibility (timeline, resources, challenges)

For each question, provide:
- The question text
- Priority (high/medium/low)
- Reason (why this question is important)
- Sources (which analyses contributed: github/ppt/voice)

Return ONLY valid JSON in this exact format:
{
  "questions_by_category": {
    "technical": [
      {
        "question": "Your question here",
        "priority": "high",
        "reason": "Why this matters",
        "sources": ["ppt", "github"]
      }
    ],
    "business": [...],
    "innovation": [...],
    "feasibility": [...]
  },
  "overall_assessment": {
    "technical_score": 8.5,
    "business_score": 7.0,
    "presentation_score": 8.0,
    "overall_score": 7.83
  },
  "key_strengths": ["strength 1", "strength 2"],
  "key_concerns": ["concern 1", "concern 2"]
}
"""

        response = self.llm.generate_completion(prompt, system_prompt=context)

        # Parse JSON response
        try:
            # Extract JSON
            start = response.find('{')
            end = response.rfind('}') + 1
            if start != -1 and end > start:
                json_str = response[start:end]
                return json.loads(json_str)
            else:
                return self._generate_fallback_questions()
        except Exception as e:
            print(f"Error parsing LLM response: {e}")
            return self._generate_fallback_questions()

    def _generate_fallback_questions(self) -> Dict[str, Any]:
        """Generate basic fallback questions if LLM fails"""
        return {
            "questions_by_category": {
                "technical": [
                    {
                        "question": "Can you walk us through your technical architecture?",
                        "priority": "high",
                        "reason": "Understanding core implementation",
                        "sources": ["github"]
                    }
                ],
                "business": [
                    {
                        "question": "Who is your target customer?",
                        "priority": "high",
                        "reason": "Understanding market focus",
                        "sources": ["ppt"]
                    }
                ],
                "innovation": [
                    {
                        "question": "What makes your solution unique?",
                        "priority": "medium",
                        "reason": "Understanding differentiation",
                        "sources": ["ppt", "voice"]
                    }
                ],
                "feasibility": [
                    {
                        "question": "What are your next steps after the hackathon?",
                        "priority": "low",
                        "reason": "Understanding commitment",
                        "sources": ["voice"]
                    }
                ]
            },
            "overall_assessment": {
                "technical_score": 0,
                "business_score": 0,
                "presentation_score": 0,
                "overall_score": 0
            },
            "key_strengths": [],
            "key_concerns": ["Unable to generate detailed analysis"]
        }

    def format_for_voice(self, questions: Dict[str, Any]) -> str:
        """
        Format questions as voice script for ElevenLabs TTS

        Args:
            questions: Generated questions dictionary

        Returns:
            str: Voice-ready script
        """
        script_parts = ["Great presentation, team! I have a few questions for you."]

        # Get high priority questions from each category
        question_num = 1
        for category in ["technical", "business", "innovation", "feasibility"]:
            category_questions = questions.get("questions_by_category", {}).get(category, [])

            # Get high priority questions
            high_priority = [q for q in category_questions if q.get("priority") == "high"]

            for q in high_priority[:2]:  # Max 2 per category
                script_parts.append(f"\n\nQuestion {question_num}: {q['question']}")
                question_num += 1

                if question_num > 5:  # Max 5 questions total
                    break

            if question_num > 5:
                break

        script_parts.append("\n\nThank you for your time!")

        return " [PAUSE] ".join(script_parts)


# Convenience functions
def get_llm_client() -> LLMClient:
    """Get LLM client instance"""
    return LLMClient()


def generate_questions_from_analyses(
    github_analysis: Dict[str, Any],
    ppt_analysis: Dict[str, Any],
    voice_analysis: Dict[str, Any]
) -> Dict[str, Any]:
    """Generate questions from all analyses"""
    generator = QuestionGenerator()
    return generator.generate_questions(github_analysis, ppt_analysis, voice_analysis)
