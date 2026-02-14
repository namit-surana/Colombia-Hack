"""
Agent 3: Interactive Voice Presentation Evaluator (ElevenAgents)
"""
import asyncio
from typing import Dict, Any, Optional
from elevenlabs.client import ElevenLabs
from elevenlabs.conversational_ai.conversation import Conversation

from app.config import settings, VOICE_AGENT_PROMPT
from app.utils import save_analysis


class VoiceEvaluatorAgent:
    """Agent for conducting interactive voice-based presentation evaluation using ElevenAgents"""

    def __init__(self):
        self.client = ElevenLabs(api_key=settings.ELEVENLABS_API_KEY)
        self.agent_config = {
            "name": "Hackathon Presentation Evaluator",
            "prompt": VOICE_AGENT_PROMPT,
            "first_message": "Hello team! I'm ready to hear your presentation. Please introduce yourselves and your project!",
            "language": "en",
            "voice_id": settings.ELEVENLABS_VOICE_ID,
            "model": settings.ELEVENLABS_MODEL,
        }

    async def create_conversation_session(self, team_id: str) -> Dict[str, Any]:
        """
        Create ElevenAgents conversation session

        Args:
            team_id: Team identifier

        Returns:
            Dictionary with session information
        """
        try:
            # Note: This is a placeholder for the actual ElevenLabs Conversational AI SDK
            # The actual implementation will depend on the ElevenLabs SDK version you're using

            # For now, we'll return session info that can be used with WebSocket
            session_info = {
                "session_id": f"voice_{team_id}",
                "agent_id": f"eval_agent_{team_id}",
                "status": "ready",
                "websocket_url": f"ws://localhost:8000/ws/voice/{team_id}",
                "instructions": "Connect to WebSocket to start voice conversation"
            }

            return session_info

        except Exception as e:
            return {"error": f"Error creating voice session: {str(e)}"}

    def analyze_from_transcription(self, transcription: str, team_id: str) -> Dict[str, Any]:
        """
        Analyze presentation from transcription (fallback when not using live conversation)

        Args:
            transcription: Full transcription of presentation
            team_id: Team identifier

        Returns:
            Dictionary with analysis results
        """
        try:
            from app.tools import LLMClient

            llm = LLMClient()

            # Analyze transcription
            analysis_prompt = """
Based on this presentation transcription, provide a structured analysis for hackathon evaluation:

1. Delivery Score (0-10): Rate communication quality
2. Key Points Mentioned: List main points covered verbally
3. Communication Quality:
   - Clarity: How clear was the explanation?
   - Confidence: How confident did they sound?
   - Concerns: Any issues (rushed, vague, uncertain)?
4. Verbal Claims: List specific claims made (users, metrics, partnerships)
5. Additional Information: Anything mentioned that might not be in slides?
6. Question Areas: What should judges probe based on verbal presentation?

Return a concise, specific analysis.
"""

            llm_analysis = llm.analyze_with_context(
                f"Transcription:\n{transcription}",
                analysis_prompt,
                VOICE_AGENT_PROMPT
            )

            # Basic sentiment analysis
            word_count = len(transcription.split())
            has_enthusiasm = any(word in transcription.lower() for word in ['excited', 'proud', 'amazing', 'great'])
            has_metrics = any(char.isdigit() for char in transcription)

            analysis = {
                "transcription": transcription,
                "word_count": word_count,
                "delivery_score": 7.5,  # Default, can be refined
                "communication_quality": {
                    "clarity": "Good" if word_count > 200 else "Brief",
                    "confidence": "High" if has_enthusiasm else "Moderate",
                    "has_metrics": has_metrics
                },
                "key_verbal_points": self._extract_key_points(transcription),
                "verbal_claims": self._extract_verbal_claims(transcription),
                "llm_analysis": llm_analysis,
                "question_areas": [
                    "presentation_depth",
                    "verbal_claims_validation",
                    "team_knowledge"
                ]
            }

            # Save analysis
            save_analysis(team_id, 'voice', analysis)

            return analysis

        except Exception as e:
            error_result = {
                "error": f"Error analyzing voice presentation: {str(e)}",
                "transcription": transcription[:500]
            }
            save_analysis(team_id, 'voice', error_result)
            return error_result

    async def analyze_from_conversation(
        self,
        conversation_id: str,
        team_id: str
    ) -> Dict[str, Any]:
        """
        Analyze completed ElevenAgents conversation

        Args:
            conversation_id: ElevenAgents conversation ID
            team_id: Team identifier

        Returns:
            Dictionary with analysis results
        """
        try:
            # Note: Placeholder for actual ElevenLabs Conversational AI SDK
            # In production, you would retrieve the conversation data from ElevenLabs

            # For now, return a structured analysis template
            analysis = {
                "conversation_id": conversation_id,
                "platform": "elevenlabs_agents",
                "delivery_score": 8.0,
                "conversation_metadata": {
                    "duration_seconds": 0,
                    "agent_turns": 0,
                    "team_turns": 0
                },
                "full_transcript": [],
                "agent_questions_asked": [],
                "team_responses_quality": {
                    "technical_depth": "Good",
                    "validation_evidence": "Moderate",
                    "business_clarity": "Good"
                },
                "conversation_quality": {
                    "natural_flow": True,
                    "clarity": "high",
                    "engagement": "high"
                },
                "insights": {
                    "strengths": [],
                    "concerns": [],
                    "red_flags": []
                },
                "question_areas": [
                    "follow_up_needed",
                    "clarification_required"
                ]
            }

            # Save analysis
            save_analysis(team_id, 'voice', analysis)

            return analysis

        except Exception as e:
            error_result = {
                "error": f"Error analyzing conversation: {str(e)}",
                "conversation_id": conversation_id
            }
            save_analysis(team_id, 'voice', error_result)
            return error_result

    def _extract_key_points(self, text: str) -> list:
        """Extract key points from transcription"""
        # Simple extraction based on sentence structure
        sentences = text.split('.')
        key_points = []

        keywords = ['we built', 'our solution', 'we solve', 'our approach',
                   'key feature', 'main benefit', 'we use', 'developed']

        for sentence in sentences:
            if any(keyword in sentence.lower() for keyword in keywords):
                key_points.append(sentence.strip()[:200])

        return key_points[:5]  # Max 5 key points

    def _extract_verbal_claims(self, text: str) -> list:
        """Extract claims from transcription"""
        claims = []
        sentences = text.split('.')

        claim_patterns = [
            'users', 'customers', 'tested', 'validated', 'partnership',
            'compliant', 'faster', 'better', 'improve', 'reduce'
        ]

        for sentence in sentences:
            sentence_lower = sentence.lower()
            # Look for sentences with numbers and claim keywords
            if any(char.isdigit() for char in sentence):
                if any(pattern in sentence_lower for pattern in claim_patterns):
                    claims.append(sentence.strip()[:200])

        return claims[:5]  # Max 5 claims

    def create_mock_analysis(self, team_id: str) -> Dict[str, Any]:
        """
        Create mock analysis for testing without actual voice conversation

        Args:
            team_id: Team identifier

        Returns:
            Mock analysis dictionary
        """
        mock_analysis = {
            "mock_data": True,
            "delivery_score": 8.0,
            "transcription": "This is a mock transcription. Team presented their healthcare AI solution...",
            "communication_quality": {
                "clarity": "Very clear",
                "confidence": "High",
                "concerns": []
            },
            "key_verbal_points": [
                "Built AI-powered healthcare platform",
                "Tested with 50 beta users",
                "HIPAA compliant implementation"
            ],
            "verbal_claims": [
                "40% faster than existing solutions",
                "Partnership discussions with Hospital XYZ"
            ],
            "question_areas": [
                "beta_testing_results",
                "hipaa_compliance_details",
                "partnership_status"
            ]
        }

        save_analysis(team_id, 'voice', mock_analysis)
        return mock_analysis


# Convenience function for simple transcription analysis
def analyze_transcription(transcription: str, team_id: str) -> Dict[str, Any]:
    """
    Analyze presentation from transcription

    Args:
        transcription: Presentation transcription text
        team_id: Team identifier

    Returns:
        Analysis dictionary
    """
    agent = VoiceEvaluatorAgent()
    return agent.analyze_from_transcription(transcription, team_id)
