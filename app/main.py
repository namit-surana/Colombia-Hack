"""
Hackathon Judge AI - Main FastAPI Application
"""
import os
import shutil
from pathlib import Path
from typing import Optional
from datetime import datetime

from fastapi import FastAPI, File, UploadFile, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.config import settings
from app.agents import (
    GitHubAnalyzerAgent,
    PPTAnalyzerAgent,
    VoiceEvaluatorAgent,
    OrchestratorAgent,
    generate_questions_for_team
)
from app.utils import check_analyses_complete

# Validate settings on startup
try:
    settings.validate()
except ValueError as e:
    print(f"Configuration error: {e}")
    print("Please check your .env file and ensure all required variables are set.")
    exit(1)

# Initialize FastAPI app
app = FastAPI(
    title="Hackathon Judge AI",
    description="Multi-agent system for evaluating hackathon projects",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize agents (singleton pattern)
github_agent = GitHubAnalyzerAgent()
ppt_agent = PPTAnalyzerAgent()
voice_agent = VoiceEvaluatorAgent()
orchestrator_agent = OrchestratorAgent()


# Request/Response Models
class GitHubAnalyzeRequest(BaseModel):
    team_id: str
    github_url: str


class VoiceAnalyzeRequest(BaseModel):
    team_id: str
    transcription: Optional[str] = None


class APIResponse(BaseModel):
    status: str
    message: str
    data: Optional[dict] = None


# ============================================================================
# API ENDPOINT 1: POST /api/analyze/github
# ============================================================================
@app.post("/api/analyze/github", response_model=APIResponse)
async def analyze_github(request: GitHubAnalyzeRequest):
    """
    Analyze GitHub repository

    Args:
        request: GitHub analysis request with team_id and github_url

    Returns:
        APIResponse with analysis results
    """
    try:
        print(f"[GitHub Agent] Starting analysis for team: {request.team_id}")
        print(f"[GitHub Agent] Repository: {request.github_url}")

        # Run GitHub analysis
        result = github_agent.analyze(request.github_url, request.team_id)

        if "error" in result:
            return APIResponse(
                status="error",
                message=result["error"],
                data=result
            )

        return APIResponse(
            status="success",
            message="GitHub analysis completed successfully",
            data={
                "team_id": request.team_id,
                "saved_to": f"results/{request.team_id}/github.json",
                "analysis_summary": {
                    "technical_score": result.get("technical_score"),
                    "tech_stack": result.get("tech_stack"),
                    "code_quality": result.get("code_quality")
                }
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing GitHub: {str(e)}")


# ============================================================================
# API ENDPOINT 2: POST /api/analyze/ppt
# ============================================================================
@app.post("/api/analyze/ppt", response_model=APIResponse)
async def analyze_ppt(team_id: str, file: UploadFile = File(...)):
    """
    Analyze PowerPoint presentation

    Args:
        team_id: Team identifier
        file: Uploaded PPT/PPTX file

    Returns:
        APIResponse with analysis results
    """
    try:
        print(f"[PPT Agent] Starting analysis for team: {team_id}")
        print(f"[PPT Agent] File: {file.filename}")

        # Validate file type
        if not file.filename.endswith(('.ppt', '.pptx')):
            raise HTTPException(status_code=400, detail="File must be PPT or PPTX format")

        # Save uploaded file temporarily
        temp_dir = settings.TEMP_DIR
        temp_path = temp_dir / f"{team_id}_{file.filename}"

        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Run PPT analysis
        result = ppt_agent.analyze(str(temp_path), team_id)

        # Clean up temp file
        try:
            os.remove(temp_path)
        except:
            pass

        if "error" in result:
            return APIResponse(
                status="error",
                message=result["error"],
                data=result
            )

        return APIResponse(
            status="success",
            message="PPT analysis completed successfully",
            data={
                "team_id": team_id,
                "saved_to": f"results/{team_id}/ppt.json",
                "analysis_summary": {
                    "presentation_score": result.get("presentation_score"),
                    "slide_count": result.get("slide_count"),
                    "key_claims": len(result.get("key_claims", []))
                }
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing PPT: {str(e)}")


# ============================================================================
# API ENDPOINT 3: POST /api/analyze/voice
# ============================================================================
@app.post("/api/analyze/voice", response_model=APIResponse)
async def analyze_voice(request: VoiceAnalyzeRequest):
    """
    Analyze voice presentation

    Args:
        request: Voice analysis request with team_id and optional transcription

    Returns:
        APIResponse with analysis results or WebSocket session info
    """
    try:
        print(f"[Voice Agent] Starting analysis for team: {request.team_id}")

        if request.transcription:
            # Analyze from provided transcription
            print(f"[Voice Agent] Analyzing from transcription ({len(request.transcription)} chars)")

            result = voice_agent.analyze_from_transcription(
                request.transcription,
                request.team_id
            )

            if "error" in result:
                return APIResponse(
                    status="error",
                    message=result["error"],
                    data=result
                )

            return APIResponse(
                status="success",
                message="Voice analysis completed successfully",
                data={
                    "team_id": request.team_id,
                    "saved_to": f"results/{request.team_id}/voice.json",
                    "analysis_summary": {
                        "delivery_score": result.get("delivery_score"),
                        "word_count": result.get("word_count"),
                        "key_points": len(result.get("key_verbal_points", []))
                    }
                }
            )
        else:
            # For live conversation, return session info
            session = await voice_agent.create_conversation_session(request.team_id)

            if "error" in session:
                return APIResponse(
                    status="error",
                    message=session["error"],
                    data=session
                )

            return APIResponse(
                status="session_created",
                message="Voice session created. Connect via WebSocket for live conversation.",
                data=session
            )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error with voice analysis: {str(e)}")


# ============================================================================
# WebSocket for Voice Streaming (Optional - for live presentations)
# ============================================================================
@app.websocket("/ws/voice/{team_id}")
async def voice_websocket(websocket: WebSocket, team_id: str):
    """
    WebSocket endpoint for real-time voice conversation

    Note: This is a placeholder. Full implementation requires ElevenLabs WebSocket integration.
    """
    await websocket.accept()

    try:
        await websocket.send_json({
            "type": "connected",
            "message": "Connected to voice session",
            "team_id": team_id
        })

        # Placeholder for bidirectional audio streaming
        while True:
            data = await websocket.receive_text()

            # Echo back (replace with actual ElevenAgents integration)
            await websocket.send_json({
                "type": "echo",
                "message": f"Received: {data}"
            })

    except WebSocketDisconnect:
        print(f"[WebSocket] Client disconnected: {team_id}")
        # Save conversation analysis here
        await websocket.close()


# ============================================================================
# API ENDPOINT 4: GET /api/questions/{team_id}
# ============================================================================
@app.get("/api/questions/{team_id}")
async def get_questions(team_id: str):
    """
    Generate and retrieve questions for a team

    Args:
        team_id: Team identifier

    Returns:
        Generated questions and overall assessment
    """
    try:
        print(f"[Orchestrator Agent] Generating questions for team: {team_id}")

        # Check which analyses are available
        all_complete, available = check_analyses_complete(team_id)

        if not available:
            raise HTTPException(
                status_code=404,
                detail=f"No analyses found for team {team_id}. Please submit inputs first."
            )

        # Generate questions
        questions = generate_questions_for_team(team_id)

        if "error" in questions:
            raise HTTPException(status_code=500, detail=questions["error"])

        return {
            "status": "success",
            "team_id": team_id,
            "analyses_complete": all_complete,
            "analyses_available": available,
            "generated_at": datetime.utcnow().isoformat(),
            **questions
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating questions: {str(e)}")


# ============================================================================
# Health Check & Info Endpoints
# ============================================================================
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "name": "Hackathon Judge AI",
        "version": "1.0.0",
        "description": "Multi-agent system for evaluating hackathon projects",
        "endpoints": {
            "github_analysis": "POST /api/analyze/github",
            "ppt_analysis": "POST /api/analyze/ppt",
            "voice_analysis": "POST /api/analyze/voice",
            "get_questions": "GET /api/questions/{team_id}",
            "voice_websocket": "WS /ws/voice/{team_id}"
        },
        "agents": ["GitHub Analyzer", "PPT Analyzer", "Voice Evaluator", "Orchestrator"],
        "status": "operational"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "agents": {
            "github": "ready",
            "ppt": "ready",
            "voice": "ready",
            "orchestrator": "ready"
        }
    }


@app.get("/api/teams/{team_id}/status")
async def get_team_status(team_id: str):
    """Get status of analyses for a team"""
    all_complete, available = check_analyses_complete(team_id)

    return {
        "team_id": team_id,
        "all_analyses_complete": all_complete,
        "analyses_available": available,
        "analyses_pending": list(set(['github', 'ppt', 'voice']) - set(available))
    }


# ============================================================================
# Run Server
# ============================================================================
if __name__ == "__main__":
    import uvicorn

    print("=" * 60)
    print("🏆 Hackathon Judge AI - Starting Server")
    print("=" * 60)
    print(f"Host: {settings.HOST}:{settings.PORT}")
    print(f"Debug: {settings.DEBUG}")
    print(f"LLM Provider: {settings.LLM_PROVIDER}")
    print(f"LLM Model: {settings.LLM_MODEL}")
    print("=" * 60)

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
