"""
Speech-to-text for the engine. Audio in, plain text out.

The engine itself never sees audio: the caller transcribes first, then passes
the text to engine.ask() exactly like a typed question.

Backends (choose with the ASR_BACKEND env var, default "gemini"):
  gemini  - sends the audio to the same Gemini model you already use.
            No extra install. Audio leaves your server.
  whisper - runs OpenAI Whisper locally (pip install openai-whisper).
            Audio stays on your machine. Slower, needs more setup.

Requires ffmpeg on the system (macOS: brew install ffmpeg), because browsers
record webm/mp4 and both backends are fed a 16 kHz mono wav.
"""

import base64
import os
import subprocess
import tempfile

from langchain_core.messages import HumanMessage

from .rag import get_response_text

ASR_BACKEND = os.getenv("ASR_BACKEND", "gemini").lower()
WHISPER_MODEL_SIZE = os.getenv("WHISPER_MODEL", "small")

_whisper_model = None  # loaded once, on first use


def _to_wav(src_path):
    """Convert any audio file to 16 kHz mono wav. Returns the new file's path."""
    fd, wav_path = tempfile.mkstemp(suffix=".wav")
    os.close(fd)
    try:
        result = subprocess.run(
            ["ffmpeg", "-y", "-i", src_path, "-ar", "16000", "-ac", "1", wav_path],
            capture_output=True,
            check=False,
        )
    except FileNotFoundError:
        os.remove(wav_path)
        raise RuntimeError("ffmpeg is not installed. On macOS run: brew install ffmpeg") from None

    if result.returncode != 0:
        os.remove(wav_path)
        tail = result.stderr.decode(errors="ignore")[-300:]
        raise RuntimeError(f"ffmpeg could not read the audio: {tail}")
    return wav_path


def _transcribe_gemini(wav_path, config, language_hint):
    with open(wav_path, "rb") as f:
        audio_b64 = base64.b64encode(f.read()).decode()

    hint = f" The speaker is most likely speaking {language_hint}." if language_hint else ""
    prompt = (
        "Transcribe this audio exactly as spoken. The speaker may use Nepali or English."
        f"{hint} Write Nepali in Devanagari script. Do not translate, summarize, or answer. "
        "Output ONLY the transcript. If there is no speech, output an empty string."
    )
    message = HumanMessage(content=[
        {"type": "text", "text": prompt},
        {"type": "media", "mime_type": "audio/wav", "data": audio_b64},
    ])
    return get_response_text(config.llm.invoke([message])).strip()

def _transcribe_whisper(wav_path, language_code):
    global _whisper_model
    import whisper  # type: ignore  # lazy import: only needed for the whisper backend

    if _whisper_model is None:
        _whisper_model = whisper.load_model(WHISPER_MODEL_SIZE)
    result = _whisper_model.transcribe(wav_path, language=language_code)
    return str(result["text"]).strip()


def transcribe(audio_path, config=None, language_code=None, language_hint=None):
    """
    audio_path:    path to the recorded file (webm, mp4, wav, mp3, ...)
    config:        EngineConfig (needed for the gemini backend, uses config.llm)
    language_code: e.g. "ne" or "en" for whisper; None = auto-detect
    language_hint: e.g. "Nepali" for gemini; None = no hint
    Returns the transcript as a string ("" if no speech was found).
    """
    wav_path = _to_wav(audio_path)
    try:
        if ASR_BACKEND == "whisper":
            return _transcribe_whisper(wav_path, language_code)
        if config is None:
            raise ValueError("config is required for the gemini ASR backend")
        return _transcribe_gemini(wav_path, config, language_hint)
    finally:
        os.remove(wav_path)