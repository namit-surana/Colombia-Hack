"""
Configuration settings for Hackathon Judge AI
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Settings:
    # API Keys
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
    ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

    # LLM Configuration
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai")
    LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4-turbo")
    LLM_TEMPERATURE = 0.7
    LLM_MAX_TOKENS = 2000

    # ElevenLabs Configuration
    ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "professional_neutral")
    ELEVENLABS_MODEL = os.getenv("ELEVENLABS_MODEL", "eleven_multilingual_v2")

    # Server Configuration
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", 8000))
    DEBUG = os.getenv("DEBUG", "True").lower() == "true"

    # Storage
    BASE_DIR = Path(__file__).parent.parent.parent
    RESULTS_DIR = BASE_DIR / os.getenv("RESULTS_DIR", "results")
    TEMP_DIR = BASE_DIR / os.getenv("TEMP_DIR", "temp")

    # Agent Configuration
    AGENT_VERBOSE = True
    AGENT_MAX_ITERATIONS = 10

    # GitHub Analysis Configuration
    GITHUB_CLONE_DEPTH = 1  # Shallow clone
    GITHUB_MAX_FILE_SIZE = 1024 * 1024  # 1MB max file size to analyze

    # Voice Agent Configuration
    VOICE_MAX_DURATION = 480  # 8 minutes max
    VOICE_TURN_TIMEOUT = 30  # 30 seconds per turn

    @classmethod
    def validate(cls):
        """Validate required settings"""
        required = {
            "GITHUB_TOKEN": cls.GITHUB_TOKEN,
            "ELEVENLABS_API_KEY": cls.ELEVENLABS_API_KEY,
        }

        # At least one LLM provider required
        if not cls.OPENAI_API_KEY and not cls.ANTHROPIC_API_KEY:
            raise ValueError("Either OPENAI_API_KEY or ANTHROPIC_API_KEY must be set")

        missing = [k for k, v in required.items() if not v]
        if missing:
            raise ValueError(f"Missing required settings: {', '.join(missing)}")

        # Create directories
        cls.RESULTS_DIR.mkdir(exist_ok=True)
        cls.TEMP_DIR.mkdir(exist_ok=True)

        return True

settings = Settings()
