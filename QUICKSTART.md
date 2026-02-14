# 🚀 Quick Start Guide

Get your Hackathon Judge AI up and running in 5 minutes!

## Step 1: Install Dependencies

```bash
# Create virtual environment
python -m venv venv

# Activate it
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# Install packages
pip install -r requirements.txt
```

## Step 2: Set Up API Keys

1. Copy the example environment file:
```bash
cp .env.example .env
```

2. Edit `.env` and add your API keys:

```env
# Get from: https://github.com/settings/tokens
GITHUB_TOKEN=ghp_your_token_here

# Get from: https://elevenlabs.io/app/settings
ELEVENLABS_API_KEY=sk_your_key_here

# Get from: https://platform.openai.com/api-keys
OPENAI_API_KEY=sk-your_key_here
```

## Step 3: Run the Server

```bash
python -m app.main
```

Server starts at: http://localhost:8000

## Step 4: Test the API

Open another terminal and run:

```bash
python test_api.py
```

Or visit in your browser:
- http://localhost:8000 - API info
- http://localhost:8000/health - Health check
- http://localhost:8000/docs - Interactive API docs (Swagger UI)

## Step 5: Make Your First Request

```bash
curl -X POST "http://localhost:8000/api/analyze/github" \
  -H "Content-Type: application/json" \
  -d '{
    "team_id": "team_001",
    "github_url": "https://github.com/fastapi/fastapi"
  }'
```

## What's Next?

1. **Analyze a PPT**: Upload a presentation file
2. **Analyze Voice**: Submit a transcription
3. **Get Questions**: Retrieve generated questions for judges

Check the full [README.md](README.md) for detailed documentation!

## Common Issues

**Problem**: `ModuleNotFoundError`
**Solution**: Make sure you activated the virtual environment

**Problem**: `Configuration error`
**Solution**: Check your `.env` file has all required API keys

**Problem**: Server won't start
**Solution**: Check if port 8000 is already in use

## Need Help?

- Check [README.md](README.md) for full documentation
- View API docs: http://localhost:8000/docs
- Open an issue on GitHub

Happy judging! 🏆
