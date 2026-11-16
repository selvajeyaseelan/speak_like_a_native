# Native English Speaker — How to Run

## Prerequisites
- **Python 3.12+** installed
- **EURI API key** at https://euron.one (OpenAI-compatible endpoint)

## One-Time Setup
1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
2. Put your API key in `.env` (already included):
   ```
   EURI_API_KEY=sk-euri-xxxxx
   ```

## Run the App
```
python app.py
```
That's the only file you need to run.

- **On this laptop:** open http://127.0.0.1:5000/ in any browser
- **On your iPhone** (same WiFi network): open http://192.168.29.159:5000/ in Safari or Chrome

## How It Works
1. Tap **Record** → speak your situation/context into the microphone
2. Tap **Stop & Process** → the app sends your audio to EURI's Whisper for transcription, then uses EURI's LLM to extract and rewrite your message as 4 natural alternatives (2 detailed, 2 short)
3. The first detailed (long) alternative **auto-generates speech on demand** and plays aloud
4. Tap **Listen** on any alternative to hear it (audio is generated only when you click), or **Copy** to grab the text

## Performance
- **Latency improvement (v2):** TTS audio is now generated **on-demand** (lazy) rather than pre-generating all 4 alternatives. The initial response shows text alternatives ~4x faster. Audio is fetched from the server only when you tap "Listen".
- Browser STT (Chrome) is the fastest path — it uses your browser's built-in speech recognition with no upload.

## Versioning
- Current version: **lazy-tts** branch (fast text-first responses)
- Previous version: **pre-lazy-tts** branch (all audio pre-generated)
- To revert: `git checkout pre-lazy-tts`

## Files
| File | Purpose |
|---|---|
| `app.py` | Flask server — run this |
| `requirements.txt` | Python dependencies |
| `.env` | Your EURI API key (never commit a real key) |
| `templates/index.html` | Frontend UI |
| `test_euri.py` | API connectivity test |
