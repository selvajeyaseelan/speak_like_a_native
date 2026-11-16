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
   - **Audio visualizer:** animated bars appear below the record button while the mic is active. They pulse when you speak and go flat when you pause — so you can see the app is listening.
2. Tap **Stop & Process** → the app sends your audio to EURI's Whisper for transcription, then uses EURI's LLM to extract and rewrite your message as 4 natural alternatives (2 detailed, 2 short)
3. The first detailed (long) alternative **auto-generates speech on demand** and plays aloud
4. Tap **Listen** on any alternative to hear it (audio is generated only when you click), or **Copy** to grab the text
5. **History panel:** tap "History" below the alternatives to expand a collapsible list of your last 20 requests. Tap any past entry to re-process it instantly.

## Features
| Feature | What it does |
|---|---|
| Audio visualizer | Animated bars pulse while you speak (Web Audio API analyser; random fallback if unavailable) |
| History | Last 20 transcripts saved in browser `localStorage`. Click any entry to re-send it to the server |
| Lazy TTS | Audio is generated only when you tap "Listen", so text appears ~4x faster |

## Versioning
- Current branch: **main**
- Baseline (before animation+history): commit `996d1c1`
- To revert to baseline: `git reset --hard 996d1c1`
- Remote mirror: `https://github.com/selvajeyaseelan/speak_like_a_native`

## Files
| File | Purpose |
|---|---|
| `app.py` | Flask server — run this |
| `requirements.txt` | Python dependencies |
| `.env` | Your EURI API key (never commit a real key) |
| `templates/index.html` | Frontend UI |
| `test_euri.py` | API connectivity test |
