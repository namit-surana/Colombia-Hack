# 🏆 Hackathon Judge AI

A sophisticated multi-agent AI system for evaluating hackathon projects through comprehensive analysis of code, presentations, and live pitch delivery.

## 🌟 Features

- **4 Specialized AI Agents** powered by CrewAI
  - 🔍 **GitHub Analyzer**: Evaluates code quality, architecture, and technical innovation
  - 📊 **PPT Analyzer**: Assesses business viability and presentation quality
  - 🎤 **Voice Evaluator**: Analyzes live presentations using ElevenLabs Conversational AI
  - 🎯 **Orchestrator**: Synthesizes analyses and generates intelligent questions

- **4 RESTful APIs** for seamless integration
- **Real-time Voice Interaction** via ElevenLabs Agents
- **Cross-referenced Analysis** to identify inconsistencies
- **Intelligent Question Generation** for judges
- **Voice-ready Scripts** for automated Q&A

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────┐
│          FastAPI Server (4 Endpoints)           │
└─────────────────────────────────────────────────┘
                    │
    ┌───────────────┼───────────────┐
    │               │               │
    ▼               ▼               ▼
┌────────┐    ┌────────┐    ┌────────────┐
│GitHub  │    │  PPT   │    │   Voice    │
│Agent   │    │ Agent  │    │   Agent    │
└────────┘    └────────┘    └────────────┘
    │               │               │
    └───────────────┼───────────────┘
                    ▼
            ┌──────────────┐
            │ Orchestrator │
            │    Agent     │
            └──────────────┘
```

## 📋 Prerequisites

- Python 3.9+
- GitHub Personal Access Token
- ElevenLabs API Key
- OpenAI API Key (or Anthropic Claude API Key)

## 🚀 Quick Start

### 1. Clone Repository

```bash
git clone <your-repo-url>
cd Hackthon_Judge
```

### 2. Create Virtual Environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment

Create a `.env` file in the root directory:

```bash
cp .env.example .env
```

Edit `.env` and add your API keys:

```env
# Required
GITHUB_TOKEN=ghp_your_github_token_here
ELEVENLABS_API_KEY=sk_your_elevenlabs_key_here
OPENAI_API_KEY=sk-your_openai_key_here

# Optional (if using Claude instead)
ANTHROPIC_API_KEY=sk-ant-your_anthropic_key_here

# Configuration
LLM_PROVIDER=openai  # or 'anthropic'
LLM_MODEL=gpt-4-turbo  # or 'claude-sonnet-4'
```

### 5. Run Server

```bash
python -m app.main

# Or use uvicorn directly
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Server will start at: `http://localhost:8000`

## 📡 API Endpoints

### 1. Analyze GitHub Repository

```bash
POST http://localhost:8000/api/analyze/github
Content-Type: application/json

{
  "team_id": "team_123",
  "github_url": "https://github.com/username/repo"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "GitHub analysis completed",
  "data": {
    "team_id": "team_123",
    "saved_to": "results/team_123/github.json",
    "analysis_summary": {
      "technical_score": 8.5,
      "tech_stack": {...},
      "code_quality": {...}
    }
  }
}
```

### 2. Analyze PowerPoint Presentation

```bash
POST http://localhost:8000/api/analyze/ppt?team_id=team_123
Content-Type: multipart/form-data

file: <upload .pptx file>
```

**Response:**
```json
{
  "status": "success",
  "message": "PPT analysis completed",
  "data": {
    "team_id": "team_123",
    "saved_to": "results/team_123/ppt.json",
    "analysis_summary": {
      "presentation_score": 7.8,
      "slide_count": 12,
      "key_claims": 5
    }
  }
}
```

### 3. Analyze Voice Presentation

```bash
POST http://localhost:8000/api/analyze/voice
Content-Type: application/json

{
  "team_id": "team_123",
  "transcription": "Our team built an AI-powered healthcare platform..."
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Voice analysis completed",
  "data": {
    "team_id": "team_123",
    "saved_to": "results/team_123/voice.json",
    "analysis_summary": {
      "delivery_score": 8.2,
      "word_count": 850,
      "key_points": 5
    }
  }
}
```

### 4. Get Generated Questions

```bash
GET http://localhost:8000/api/questions/team_123
```

**Response:**
```json
{
  "status": "success",
  "team_id": "team_123",
  "overall_assessment": {
    "technical_score": 8.5,
    "business_score": 7.8,
    "presentation_score": 8.2,
    "overall_score": 8.17
  },
  "questions_by_category": {
    "technical": [
      {
        "question": "You mentioned HIPAA compliance - what encryption methods did you implement?",
        "priority": "high",
        "reason": "Critical claim requiring validation",
        "sources": ["ppt", "github"]
      }
    ],
    "business": [...],
    "innovation": [...],
    "feasibility": [...]
  },
  "voice_script": "Great presentation! I have a few questions...",
  "summary": {...}
}
```

## 🎯 Usage Example

### Complete Workflow

```python
import requests

BASE_URL = "http://localhost:8000"
team_id = "team_innovators"

# Step 1: Analyze GitHub
github_response = requests.post(
    f"{BASE_URL}/api/analyze/github",
    json={
        "team_id": team_id,
        "github_url": "https://github.com/team/project"
    }
)

# Step 2: Analyze PPT
with open("presentation.pptx", "rb") as f:
    ppt_response = requests.post(
        f"{BASE_URL}/api/analyze/ppt",
        params={"team_id": team_id},
        files={"file": f}
    )

# Step 3: Analyze Voice
voice_response = requests.post(
    f"{BASE_URL}/api/analyze/voice",
    json={
        "team_id": team_id,
        "transcription": "Our team built..."
    }
)

# Step 4: Get Questions
questions_response = requests.get(
    f"{BASE_URL}/api/questions/{team_id}"
)

questions = questions_response.json()
print(f"Overall Score: {questions['overall_assessment']['overall_score']}")
print(f"Questions: {len(questions['questions_by_category']['technical'])}")
```

## 📁 Project Structure

```
Hackthon_Judge/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application
│   ├── agents/                 # AI Agents
│   │   ├── github_agent.py     # Agent 1
│   │   ├── ppt_agent.py        # Agent 2
│   │   ├── voice_agent.py      # Agent 3
│   │   └── orchestrator_agent.py # Agent 4
│   ├── tools/                  # Agent tools
│   │   ├── github_tools.py
│   │   ├── ppt_tools.py
│   │   ├── code_analyzer.py
│   │   └── llm_tools.py
│   ├── config/                 # Configuration
│   │   ├── settings.py
│   │   └── prompts.py
│   └── utils/                  # Utilities
│       └── file_manager.py
├── results/                    # JSON storage
│   └── {team_id}/
│       ├── github.json
│       ├── ppt.json
│       └── voice.json
├── temp/                       # Temporary files
├── .env                        # Environment variables
├── .env.example               # Environment template
├── requirements.txt           # Dependencies
├── README.md                  # This file
└── docker-compose.yml         # Docker setup (optional)
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `GITHUB_TOKEN` | GitHub Personal Access Token | ✅ |
| `ELEVENLABS_API_KEY` | ElevenLabs API Key | ✅ |
| `OPENAI_API_KEY` | OpenAI API Key | ✅* |
| `ANTHROPIC_API_KEY` | Anthropic Claude API Key | ✅* |
| `LLM_PROVIDER` | `openai` or `anthropic` | ❌ |
| `LLM_MODEL` | Model to use | ❌ |
| `HOST` | Server host | ❌ |
| `PORT` | Server port | ❌ |

*At least one LLM provider (OpenAI or Anthropic) is required.

### Getting API Keys

1. **GitHub Token**: https://github.com/settings/tokens
   - Needs `repo` scope for public repos

2. **ElevenLabs**: https://elevenlabs.io/app/settings
   - Sign up and get API key from settings

3. **OpenAI**: https://platform.openai.com/api-keys
   - Create account and generate API key

4. **Anthropic** (optional): https://console.anthropic.com/
   - Alternative to OpenAI

## 🐳 Docker Deployment (Optional)

```bash
# Build and run with Docker Compose
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

## 📊 Output Format

Each agent saves its analysis as JSON in `results/{team_id}/`:

### github.json
```json
{
  "agent": "github",
  "analyzed_at": "2026-02-13T10:30:00Z",
  "technical_score": 8.5,
  "tech_stack": {...},
  "code_quality": {...},
  "question_areas": [...]
}
```

### ppt.json
```json
{
  "agent": "ppt",
  "analyzed_at": "2026-02-13T10:32:00Z",
  "presentation_score": 7.8,
  "key_claims": [...],
  "question_areas": [...]
}
```

### voice.json
```json
{
  "agent": "voice",
  "analyzed_at": "2026-02-13T10:35:00Z",
  "delivery_score": 8.2,
  "transcription": "...",
  "key_verbal_points": [...],
  "question_areas": [...]
}
```

## 🧪 Testing

### Test Individual Endpoints

```bash
# Health check
curl http://localhost:8000/health

# API info
curl http://localhost:8000/

# Team status
curl http://localhost:8000/api/teams/team_123/status
```

### Using Postman/Insomnia

Import the API collection (if provided) or manually create requests for the 4 endpoints.

## 🛠️ Troubleshooting

### Common Issues

**Issue**: `ModuleNotFoundError: No module named 'app'`
```bash
# Solution: Run from project root
cd Hackthon_Judge
python -m app.main
```

**Issue**: `Configuration error: Missing required settings`
```bash
# Solution: Check .env file has all required keys
cp .env.example .env
# Edit .env and add your API keys
```

**Issue**: `GitHub API rate limit exceeded`
```bash
# Solution: Use authenticated token (not just any token)
# Ensure GITHUB_TOKEN in .env is valid
```

**Issue**: `Error analyzing PPT: invalid file`
```bash
# Solution: Ensure file is .pptx format (not .ppt)
# Convert old .ppt files to .pptx
```

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📝 License

This project is licensed under the MIT License.

## 👥 Authors

- Your Name - Initial work

## 🙏 Acknowledgments

- **CrewAI** - Multi-agent orchestration
- **ElevenLabs** - Voice AI platform
- **FastAPI** - Modern web framework
- **OpenAI/Anthropic** - LLM providers

## 📞 Support

For issues and questions:
- Open an issue on GitHub
- Contact: your-email@example.com

---

**Built with ❤️ for Hackathon Organizers**
