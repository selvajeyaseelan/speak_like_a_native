"""Test the Native English Speaker API endpoints."""
import requests

BASE_URL = "http://127.0.0.1:5000"


def test_euri_api():
    """Test the /rewrite endpoint returns text results with the right fields."""
    sample_text = "I am going to market"
    resp = requests.post(
        f"{BASE_URL}/rewrite",
        json={"text": sample_text},
        timeout=120,
        headers={"Content-Type": "application/json"},
    )
    data = resp.json()
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {data}"
    assert data["transcript"] == sample_text
    assert "results" in data
    assert len(data["results"]) > 0
    # Results should have text but no pre-generated audio
    first = data["results"][0]
    assert "text" in first, f"Result missing 'text': {first}"
    assert first.get("audio") is None, f"Result should not have pre-generated audio: {first}"
    print("test_euri_api PASSED")


def test_tts_endpoint():
    """Test the /tts endpoint returns audio for a given text."""
    resp = requests.post(
        f"{BASE_URL}/tts",
        json={"text": "Hello, this is a test."},
        timeout=60,
        headers={"Content-Type": "application/json"},
    )
    data = resp.json()
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {data}"
    assert "audio" in data, f"Missing 'audio' in response: {data}"
    assert len(data["audio"]) > 0, "Audio data should not be empty"
    print("test_tts_endpoint PASSED")


if __name__ == "__main__":
    test_tts_endpoint()
    test_euri_api()
    print("All tests PASSED")