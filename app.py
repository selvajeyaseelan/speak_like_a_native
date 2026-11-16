"""
Native English Speaker – Flask Web App
========================================
Records voice input, rewrites it into natural native English,
and reads it back with a natural voice.

Pipeline:  microphone  →  EURI STT  →  EURI LLM rewrite (3 variants)  →  EURI TTS
All via EURI's OpenAI-compatible API at https://app.euri.ai/api/voice/realtime
"""

import os
import io
import json
import time
import tempfile
import base64
import traceback
from threading import Thread
from dotenv import load_dotenv
from flask import Flask, render_template, request, jsonify
from openai import OpenAI

load_dotenv()

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
EURI_API_KEY = os.environ.get("EURI_API_KEY", "")

if not EURI_API_KEY:
    raise RuntimeError("EURI_API_KEY not set in .env")

# Same base URL for both STT and TTS (as in the original files)
EURI_BASE_URL = "https://api.euron.one/api/v1/euri"
client = OpenAI(api_key=EURI_API_KEY, base_url=EURI_BASE_URL)

print(f"[Config] EURI API configured (base_url={EURI_BASE_URL})")

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024  # 50 MB


# ---------------------------------------------------------------------------
# EURI helpers  (mirrors speech_to_text.py and text to speech.py)
# ---------------------------------------------------------------------------

def euri_transcribe(audio_file_path):
    """Transcribe audio using EURI's OpenAI-compatible STT endpoint."""
    print(f"[STT] Transcribing: {audio_file_path}")
    with open(audio_file_path, "rb") as f:
        result = client.audio.transcriptions.create(
            model="whisper-large-v3",
            file=f,
            language="en",
        )
    return result.text.strip()


def euri_rewrite(transcript):
    """Parse the context and produce 4 direct messages the speaker can say (2 long, 2 short)."""
    print(f"[LLM] Rewriting: {transcript[:80]}...")
    prompt = (
        'I will give you a spoken input that contains context about a situation '
        'and what the speaker wants to say to someone. Your job: intelligently '
        'parse the input, figure out who the message is for and what the speaker '
        'wants to convey to that person, and produce direct-message versions '
        'that the speaker can say to that person. The output must be EXACTLY what '
        'the speaker says to the other person — no advice, no analysis, no '
        'explanation. Just the direct message to speak.'
        '\n\n'
        'Example input: I want my wife to work but she is not working. I have told '
        'her multiple times but she is not listening. How do I tell this to my wife again?'
        '\n\n'
        'Example output: {"rewrites": [{"label":"Detailed","text":"Hey, I really need you to work. I\'ve been telling you this multiple times, and I feel like we\'re going in circles. I understand it\'s not easy, but this is important to me."},{"label":"Detailed","text":"Look, we need to have a real talk about this. I\'ve asked you more than once to find some work, and it\'s starting to weigh on me. I need us to figure something out here."},{"label":"Short","text":"I need you to work — I\'ve told you enough times already."},{"label":"Short","text":"We\'ve been over this — I need you to start working."}]}'
        '\n\n'
        'Rules:'
        '\n'
        '- Extract the core message the speaker needs to convey to the other '
        'person — strip away the context and meta-talk about the situation.'
        '\n'
        '- Write it as a direct message (second person: you), as if speaking '
        'to that person face to face.'
        '\n'
        '- Use a natural conversational tone — phrasal verbs, contractions, '
        'how native speakers actually talk.'
        '\n'
        '- Produce 2 detailed versions (3-5 sentences, more context and emotion) '
        'labelled "Detailed", and 2 short versions (1-2 sentences) labelled "Short".'
        '\n'
        '- Return EXACTLY this JSON format (no markdown, no other text):'
        '\n'
        '  {"rewrites": [{"label":"Detailed","text":"..."},{"label":"Detailed","text":"..."},{"label":"Short","text":"..."},{"label":"Short","text":"..."}]}'
        '\n\n'
        f'Input: {transcript}'
    )
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.8,
    )
    text = resp.choices[0].message.content.strip()

    # Strip markdown code fences if present
    if text.startswith("```"):
        text = text.split("\n", 1)[-1]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()

    result = json.loads(text)
    return result.get("rewrites", [text])


def generate_speech_euri(text):
    """Generate speech using EURI TTS (matches text_to_speech.py pattern).
    Returns raw audio bytes."""
    print(f"[TTS] Generating speech for: '{text}'")
    response = client.audio.speech.create(
        model="euri-speech",
        voice="nova",
        input=text,
        response_format="mp3",
        speed=1.0,
    )
    # response is an httpx Response-like object with .content
    return response.content


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/rewrite", methods=["POST"])
def rewrite_only():
    """
    Accept a text transcript directly (from browser Web Speech API) and skip STT.
    1. Rewrite with LLM.
    2. Return text-only results (TTS is generated on-demand via /tts).
    """
    data = request.get_json()
    if not data or "text" not in data:
        return jsonify({"error": "No text provided"}), 400

    transcript = data["text"].strip()
    if not transcript:
        return jsonify({"error": "Empty text"}), 400

    # --- Rewrite ---
    try:
        print(f"[Rewrite] Rewriting with EURI LLM...")
        rewrites = euri_rewrite(transcript)
        print(f"[Rewrite] Rewrite result: {rewrites}")
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": f"Rewrite failed: {e}"}), 500

    # Return text-only results (no TTS pre-generation)
    results = []
    for i, rw in enumerate(rewrites):
        rewrite_text = rw.get("text", "") if isinstance(rw, dict) else str(rw)
        label = rw.get("label", "") if isinstance(rw, dict) else ""
        results.append({
            "number": i + 1,
            "label": label,
            "text": rewrite_text,
        })

    return jsonify({
        "transcript": transcript,
        "results": results,
        "method": "browser-stt+euri-llm",
    })


@app.route("/tts", methods=["POST"])
def tts():
    """On-demand TTS: receive text, generate speech, return audio as base64."""
    data = request.get_json()
    if not data or "text" not in data:
        return jsonify({"error": "No text provided"}), 400

    text = data["text"].strip()
    if not text:
        return jsonify({"error": "Empty text"}), 400

    try:
        print(f"[TTS] On-demand TTS for: '{text[:60]}...'")
        wav_bytes = generate_speech_euri(text)
        audio_b64 = base64.b64encode(wav_bytes).decode("ascii")
        return jsonify({"audio": audio_b64, "format": "mp3"})
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": f"TTS failed: {e}"}), 500


@app.route("/process", methods=["POST"])
def process():
    """
    Fallback: receive a WebM audio upload, transcribe with Whisper, rewrite, TTS.
    Used when Web Speech API is not available.
    """
    if "audio" not in request.files:
        return jsonify({"error": "No audio file"}), 400

    audio_file = request.files["audio"]
    webm_bytes = audio_file.read()
    print(f"[Process] Received {len(webm_bytes)} bytes of audio")

    # Save to temp file for STT
    tmp_path = os.path.join(tempfile.gettempdir(), f"input_{int(time.time())}.webm")
    try:
        with open(tmp_path, "wb") as f:
            f.write(webm_bytes)

        # --- Step 1: Transcribe ---
        try:
            print(f"[Process] Step 1: Transcribing with EURI STT...")
            transcript = euri_transcribe(tmp_path)
            print(f"[Process] Transcription result: '{transcript}'")
        except Exception as e:
            traceback.print_exc()
            print(f"[Process] Transcription error: {e}")
            return jsonify({"error": f"Transcription failed: {e}"}), 500

        if not transcript:
            return jsonify({"error": "Could not detect speech. Try again."}), 400

        # --- Step 2: Rewrite ---
        try:
            print(f"[Process] Step 2: Rewriting with EURI LLM...")
            rewrites = euri_rewrite(transcript)
            print(f"[Process] Rewrite result: {rewrites}")
        except Exception as e:
            traceback.print_exc()
            print(f"[Process] Rewrite error: {e}")
            return jsonify({"error": f"Rewrite failed: {e}"}), 500

        # Return text-only results (no TTS pre-generation)
        results = []
        for i, rewrite_obj in enumerate(rewrites):
            rewrite_text = rewrite_obj.get("text", "") if isinstance(rewrite_obj, dict) else str(rewrite_obj)
            label = rewrite_obj.get("label", "") if isinstance(rewrite_obj, dict) else ""
            results.append({
                "number": i + 1,
                "label": label,
                "text": rewrite_text,
            })

        print(f"[Process] Done. Returning {len(results)} results")

        return jsonify({
            "transcript": transcript,
            "results": results,
            "method": "euri-stt+euri-llm",
        })
    finally:
        # Clean up temp file
        try:
            os.remove(tmp_path)
        except OSError:
            pass


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
