"""
Test script for Hackathon Judge AI API

This script demonstrates how to use all 4 API endpoints.
"""
import requests
import json
import time

BASE_URL = "http://localhost:8000"


def test_health():
    """Test health endpoint"""
    print("\n" + "="*60)
    print("Testing Health Endpoint")
    print("="*60)

    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")


def test_github_analysis(team_id: str, github_url: str):
    """Test GitHub analysis endpoint"""
    print("\n" + "="*60)
    print("Testing GitHub Analysis")
    print("="*60)

    payload = {
        "team_id": team_id,
        "github_url": github_url
    }

    print(f"Request: POST {BASE_URL}/api/analyze/github")
    print(f"Payload: {json.dumps(payload, indent=2)}")

    response = requests.post(
        f"{BASE_URL}/api/analyze/github",
        json=payload
    )

    print(f"\nStatus: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")


def test_ppt_analysis(team_id: str, ppt_path: str):
    """Test PPT analysis endpoint"""
    print("\n" + "="*60)
    print("Testing PPT Analysis")
    print("="*60)

    print(f"Request: POST {BASE_URL}/api/analyze/ppt")
    print(f"File: {ppt_path}")

    try:
        with open(ppt_path, 'rb') as f:
            files = {'file': (ppt_path, f, 'application/vnd.openxmlformats-officedocument.presentationml.presentation')}
            params = {'team_id': team_id}

            response = requests.post(
                f"{BASE_URL}/api/analyze/ppt",
                params=params,
                files=files
            )

        print(f"\nStatus: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except FileNotFoundError:
        print(f"Error: File not found: {ppt_path}")
        print("Please provide a valid PPT/PPTX file path")


def test_voice_analysis(team_id: str, transcription: str):
    """Test voice analysis endpoint"""
    print("\n" + "="*60)
    print("Testing Voice Analysis")
    print("="*60)

    payload = {
        "team_id": team_id,
        "transcription": transcription
    }

    print(f"Request: POST {BASE_URL}/api/analyze/voice")
    print(f"Transcription length: {len(transcription)} characters")

    response = requests.post(
        f"{BASE_URL}/api/analyze/voice",
        json=payload
    )

    print(f"\nStatus: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")


def test_get_questions(team_id: str):
    """Test question generation endpoint"""
    print("\n" + "="*60)
    print("Testing Question Generation")
    print("="*60)

    print(f"Request: GET {BASE_URL}/api/questions/{team_id}")

    response = requests.get(f"{BASE_URL}/api/questions/{team_id}")

    print(f"\nStatus: {response.status_code}")

    if response.status_code == 200:
        result = response.json()
        print(f"\nOverall Score: {result.get('overall_assessment', {}).get('overall_score', 'N/A')}")
        print(f"Analyses Available: {result.get('analyses_available', [])}")

        # Print questions by category
        questions = result.get('questions_by_category', {})
        for category, qs in questions.items():
            print(f"\n{category.upper()} Questions ({len(qs)}):")
            for i, q in enumerate(qs[:3], 1):  # Show first 3
                print(f"  {i}. [{q.get('priority')}] {q.get('question')}")

        print(f"\nVoice Script Preview:")
        print(result.get('voice_script', '')[:300] + "...")
    else:
        print(f"Response: {json.dumps(response.json(), indent=2)}")


def test_team_status(team_id: str):
    """Test team status endpoint"""
    print("\n" + "="*60)
    print("Testing Team Status")
    print("="*60)

    response = requests.get(f"{BASE_URL}/api/teams/{team_id}/status")

    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")


def main():
    """Run all tests"""
    print("\n" + "🏆"*30)
    print(" "*20 + "Hackathon Judge AI - API Test")
    print("🏆"*30)

    # Configuration
    TEAM_ID = "test_team_001"
    GITHUB_URL = "https://github.com/fastapi/fastapi"  # Example public repo
    PPT_PATH = "sample_presentation.pptx"  # Update with actual path
    TRANSCRIPTION = """
    Hello judges! Our team has built an innovative AI-powered solution for healthcare.
    We identified that 40% of hospital data is siloed across different systems, causing
    inefficiencies and potential errors. Our solution uses machine learning to unify
    patient records in real-time. We've tested with 50 beta users at Hospital XYZ and
    received positive feedback. Our tech stack includes React for the frontend, FastAPI
    for the backend, and PostgreSQL for data storage. We're HIPAA compliant and have
    implemented end-to-end encryption. Thank you!
    """

    # Test 1: Health check
    test_health()

    # Wait a bit
    time.sleep(1)

    # Test 2: GitHub analysis
    test_github_analysis(TEAM_ID, GITHUB_URL)

    # Wait for analysis to complete
    time.sleep(2)

    # Test 3: Team status
    test_team_status(TEAM_ID)

    # Test 4: PPT analysis (skip if file doesn't exist)
    # Uncomment when you have a PPT file
    # test_ppt_analysis(TEAM_ID, PPT_PATH)

    # Test 5: Voice analysis
    test_voice_analysis(TEAM_ID, TRANSCRIPTION)

    # Wait for analysis to complete
    time.sleep(2)

    # Test 6: Get questions
    test_get_questions(TEAM_ID)

    print("\n" + "="*60)
    print("All tests completed!")
    print("="*60)
    print(f"\nResults saved in: results/{TEAM_ID}/")
    print("- github.json")
    print("- ppt.json (if PPT was analyzed)")
    print("- voice.json")
    print("\n")


if __name__ == "__main__":
    try:
        main()
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Could not connect to server")
        print("Make sure the server is running:")
        print("  python -m app.main")
        print(f"  or visit: {BASE_URL}\n")
    except Exception as e:
        print(f"\n❌ Error: {e}\n")
