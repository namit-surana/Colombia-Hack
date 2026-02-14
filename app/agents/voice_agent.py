"""
Agent 3: Interactive Voice Presentation Evaluator
with ElevenLabs Realtime Speech-to-Text (Scribe v2)
"""
import asyncio
import base64
import json
import logging
from typing import Dict, Any, Optional, List

import websockets as ws
from fastapi import WebSocket

from app.config import settings, VOICE_AGENT_PROMPT
from app.utils import save_analysis

logger = logging.getLogger(__name__)

ELEVENLABS_STT_URL = "wss://api.elevenlabs.io/v1/speech-to-text/realtime"


class RealtimeTranscriptionSession:
    """Manages a WebSocket connection to ElevenLabs Realtime STT."""

    def __init__(
        self,
        api_key: str,
        model_id: str = "scribe_v2_realtime",
        language_code: Optional[str] = None,
    ):
        self.api_key = api_key
        self.model_id = model_id
        self.language_code = language_code
        self._ws = None
        self.committed_segments: List[str] = []

    async def connect(self):
        """Open WebSocket to ElevenLabs Realtime STT."""
        params = f"model_id={self.model_id}"
        if self.language_code:
            params += f"&language_code={self.language_code}"

        url = f"{ELEVENLABS_STT_URL}?{params}"
        headers = {"xi-api-key": self.api_key}

        self._ws = await ws.connect(url, additional_headers=headers)
        logger.info("Connected to ElevenLabs Realtime STT")

    async def send_audio(self, audio_bytes: bytes):
        """Send raw audio as a base64-encoded input_audio_chunk."""
        if not self._ws:
            raise RuntimeError("Not connected")

        message = {
            "message_type": "input_audio_chunk",
            "audio_base_64": base64.b64encode(audio_bytes).decode(),
        }
        await self._ws.send(json.dumps(message))

    async def receive_events(self):
        """Async generator that yields parsed server events."""
        if not self._ws:
            raise RuntimeError("Not connected")

        try:
            async for raw in self._ws:
                event = json.loads(raw)
                msg_type = event.get("message_type", "")

                if msg_type == "committed_transcript":
                    text = event.get("text", "")
                    if text:
                        self.committed_segments.append(text)

                yield event
        except ws.exceptions.ConnectionClosed:
            logger.info("ElevenLabs STT connection closed")

    @property
    def full_transcript(self) -> str:
        return " ".join(self.committed_segments)

    async def close(self):
        if self._ws:
            await self._ws.close()
            self._ws = None


class VoiceEvaluatorAgent:
    """Agent for voice-based presentation evaluation
    with ElevenLabs Realtime STT integration."""

    def __init__(self):
        self.api_key = settings.ELEVENLABS_API_KEY or ""
        self.stt_model = settings.ELEVENLABS_STT_MODEL

    async def create_conversation_session(
        self, team_id: str
    ) -> Dict[str, Any]:
        """Return session info for a realtime voice session."""
        return {
            "session_id": f"voice_{team_id}",
            "status": "ready",
            "websocket_url": (
                f"ws://localhost:{settings.PORT}/ws/voice/{team_id}"
            ),
            "audio_format": "pcm_16000",
            "instructions": (
                "Connect to the WebSocket and stream raw PCM audio "
                "(16kHz, 16-bit, mono) as binary frames. "
                "Send {\"type\": \"stop\"} as text to end the session."
            ),
        }

    async def run_realtime_session(
        self, team_id: str, client_ws: WebSocket
    ) -> Dict[str, Any]:
        """
        Bridge audio between a client WebSocket and ElevenLabs
        Realtime STT, then analyse the resulting transcript.

        Args:
            team_id: Team identifier
            client_ws: The FastAPI WebSocket from the client

        Returns:
            Analysis dictionary
        """
        stt = RealtimeTranscriptionSession(
            api_key=self.api_key,
            model_id=self.stt_model,
        )

        try:
            await stt.connect()
        except Exception as e:
            logger.error(f"Failed to connect to ElevenLabs STT: {e}")
            return {"error": f"STT connection failed: {e}"}

        stop_event = asyncio.Event()

        async def forward_audio():
            """Read audio from client, forward to ElevenLabs."""
            try:
                while not stop_event.is_set():
                    message = await client_ws.receive()

                    if message.get("bytes"):
                        await stt.send_audio(message["bytes"])
                    elif message.get("text"):
                        data = json.loads(message["text"])
                        if data.get("type") == "stop":
                            stop_event.set()
                            break
            except Exception:
                stop_event.set()

        async def forward_transcripts():
            """Read events from ElevenLabs, forward to client."""
            try:
                async for event in stt.receive_events():
                    if stop_event.is_set():
                        break

                    msg_type = event.get("message_type", "")

                    if msg_type == "partial_transcript":
                        await client_ws.send_json({
                            "type": "partial_transcript",
                            "text": event.get("text", ""),
                        })
                    elif msg_type == "committed_transcript":
                        await client_ws.send_json({
                            "type": "committed_transcript",
                            "text": event.get("text", ""),
                        })
                    elif msg_type == "session_started":
                        logger.info(
                            f"STT session started for team {team_id}"
                        )
                    elif msg_type.endswith("_error"):
                        await client_ws.send_json({
                            "type": "error",
                            "message": event.get("error", msg_type),
                        })
            except Exception:
                stop_event.set()

        audio_task = asyncio.create_task(forward_audio())
        transcript_task = asyncio.create_task(forward_transcripts())

        # Wait for either task to finish (client disconnect or stop)
        _done, pending = await asyncio.wait(
            [audio_task, transcript_task],
            return_when=asyncio.FIRST_COMPLETED,
        )
        stop_event.set()
        for task in pending:
            task.cancel()

        await stt.close()

        # Analyse whatever transcript was collected
        transcript = stt.full_transcript
        if transcript.strip():
            analysis = self.analyze_from_transcription(
                transcript, team_id
            )
        else:
            analysis = {
                "error": "No speech detected during session",
                "transcription": "",
            }
            save_analysis(team_id, 'voice', analysis)

        return analysis

    def analyze_from_transcription(
        self, transcription: str, team_id: str
    ) -> Dict[str, Any]:
        """
        Analyze presentation from transcription text.

        Args:
            transcription: Full transcription of presentation
            team_id: Team identifier

        Returns:
            Dictionary with analysis results
        """
        try:
            from app.tools import LLMClient

            llm = LLMClient()

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
                VOICE_AGENT_PROMPT,
            )

            word_count = len(transcription.split())
            has_enthusiasm = any(
                word in transcription.lower()
                for word in ['excited', 'proud', 'amazing', 'great']
            )
            has_metrics = any(char.isdigit() for char in transcription)

            analysis = {
                "transcription": transcription,
                "word_count": word_count,
                "delivery_score": 7.5,
                "communication_quality": {
                    "clarity": "Good" if word_count > 200 else "Brief",
                    "confidence": (
                        "High" if has_enthusiasm else "Moderate"
                    ),
                    "has_metrics": has_metrics,
                },
                "key_verbal_points": self._extract_key_points(
                    transcription
                ),
                "verbal_claims": self._extract_verbal_claims(
                    transcription
                ),
                "llm_analysis": llm_analysis,
                "question_areas": [
                    "presentation_depth",
                    "verbal_claims_validation",
                    "team_knowledge",
                ],
            }

            save_analysis(team_id, 'voice', analysis)
            return analysis

        except Exception as e:
            error_result = {
                "error": f"Error analyzing voice presentation: {e}",
                "transcription": transcription[:500],
            }
            save_analysis(team_id, 'voice', error_result)
            return error_result

    def _extract_key_points(self, text: str) -> list:
        """Extract key points from transcription."""
        sentences = text.split('.')
        key_points = []

        keywords = [
            'we built', 'our solution', 'we solve', 'our approach',
            'key feature', 'main benefit', 'we use', 'developed',
        ]

        for sentence in sentences:
            if any(kw in sentence.lower() for kw in keywords):
                key_points.append(sentence.strip()[:200])

        return key_points[:5]

    def _extract_verbal_claims(self, text: str) -> list:
        """Extract claims from transcription."""
        claims = []
        sentences = text.split('.')

        claim_patterns = [
            'users', 'customers', 'tested', 'validated',
            'partnership', 'compliant', 'faster', 'better',
            'improve', 'reduce',
        ]

        for sentence in sentences:
            sentence_lower = sentence.lower()
            if any(char.isdigit() for char in sentence):
                if any(p in sentence_lower for p in claim_patterns):
                    claims.append(sentence.strip()[:200])

        return claims[:5]

    def create_mock_analysis(self, team_id: str) -> Dict[str, Any]:
        """Create mock analysis for testing."""
        mock_analysis = {
            "mock_data": True,
            "delivery_score": 8.0,
            "transcription": (
                "This is a mock transcription. "
                "Team presented their healthcare AI solution..."
            ),
            "communication_quality": {
                "clarity": "Very clear",
                "confidence": "High",
                "concerns": [],
            },
            "key_verbal_points": [
                "Built AI-powered healthcare platform",
                "Tested with 50 beta users",
                "HIPAA compliant implementation",
            ],
            "verbal_claims": [
                "40% faster than existing solutions",
                "Partnership discussions with Hospital XYZ",
            ],
            "question_areas": [
                "beta_testing_results",
                "hipaa_compliance_details",
                "partnership_status",
            ],
        }

        save_analysis(team_id, 'voice', mock_analysis)
        return mock_analysis


def analyze_transcription(
    transcription: str, team_id: str
) -> Dict[str, Any]:
    """Convenience function for simple transcription analysis."""
    agent = VoiceEvaluatorAgent()
    return agent.analyze_from_transcription(transcription, team_id)
