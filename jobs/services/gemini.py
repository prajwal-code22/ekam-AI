"""Turns a spoken (or typed) Nepali job request into structured data with Gemini."""
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Literal

from pydantic import BaseModel

from jobs.models import TRADES

# gemini-2.5-flash deprecated Dec 1 2026 -> routes to gemini-3.5-flash-lite.
# Using gemini-3.5-flash-lite as the default for new deployments.
DEFAULT_MODEL = "gemini-3.5-flash-lite"

PROMPT = """You help a labour marketplace in Nepal. The user asks for a worker, in
Nepali, English, or a mix of both. Understand the request and fill every field.

- transcript: what the user said, written exactly as spoken (Devanagari for Nepali).
- trade: the single best match from the allowed list.
- description_ne: one clear sentence for the worker, in Nepali.
- description_en: the same sentence in English.
- urgency: "now" (right away), "today", or "scheduled" (a later day).
- price_min_npr / price_max_npr: a fair price range in Nepali rupees for this job in
  the Kathmandu valley. Whole numbers only.
- follow_up_question: if an important detail is missing (what is broken, how many
  rooms, what time), ask ONE short question in Nepali. Otherwise leave it empty.
"""


class GeminiError(Exception):
    """Raised for any problem turning the request into structured data."""


class JobExtract(BaseModel):
    transcript: str
    trade: Literal[tuple(TRADES)]  # type: ignore[valid-type]
    description_ne: str
    description_en: str
    urgency: Literal["now", "today", "scheduled"]
    price_min_npr: int
    price_max_npr: int
    follow_up_question: str = ""


def _to_wav(audio_bytes: bytes) -> bytes:
    """Browsers record WebM or MP4. Gemini accepts WAV, so convert with ffmpeg."""
    with tempfile.TemporaryDirectory() as tmp:
        src, dst = Path(tmp, "in.audio"), Path(tmp, "out.wav")
        src.write_bytes(audio_bytes)
        try:
            subprocess.run(
                ["ffmpeg", "-y", "-i", str(src), "-ar", "16000", "-ac", "1", str(dst)],
                check=True,
                capture_output=True,
                timeout=30,
            )
        except FileNotFoundError as exc:
            raise GeminiError("ffmpeg is not installed on the server.") from exc
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
            raise GeminiError("Could not read the audio. Please record again.") from exc
        return dst.read_bytes()


def _mock(text: str) -> dict:
    """Offline stand-in so the app can be tested without an API key (MOCK_GEMINI=1)."""
    t = (text or "").lower()
    if any(k in t for k in ("ट्यांकी", "धारा", "नल", "पाइप", "plumb", "tap", "pipe")):
        trade, ne, en = "plumber", "ट्यांकीको मर्मत गर्नुपर्नेछ।", "Water tank needs repair."
        price = (800, 1500)
    elif any(k in t for k in ("बिजुली", "वायर", "electric", "wire", "light")):
        trade, ne, en = "electrician", "बिजुलीको काम गर्नुपर्नेछ।", "Electrical work needed."
        price = (700, 1400)
    else:
        trade, ne, en = "helper", "सहयोगी चाहियो।", "A helper is needed."
        price = (600, 1200)
    return {
        "transcript": text or "(mock) audio request",
        "trade": trade,
        "description_ne": ne,
        "description_en": en,
        "urgency": "today",
        "price_min_npr": price[0],
        "price_max_npr": price[1],
        "follow_up_question": "",
    }


def extract_job(audio_bytes: bytes | None = None, text: str = "") -> dict:
    if os.environ.get("MOCK_GEMINI") == "1":
        return _mock(text)

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise GeminiError("GEMINI_API_KEY is not set on the server.")

    from google import genai
    from google.genai import types

    parts = [PROMPT + "\nAllowed trades: " + ", ".join(TRADES) + "."]
    if audio_bytes:
        parts.insert(0, types.Part.from_bytes(data=_to_wav(audio_bytes), mime_type="audio/wav"))
    else:
        parts.append("User request (text): " + text)

    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=os.environ.get("GEMINI_MODEL", DEFAULT_MODEL),
            contents=parts,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=JobExtract,
                temperature=0.2,
            ),
        )
        parsed = response.parsed
        if parsed is None:
            parsed = JobExtract.model_validate_json(response.text)
        return parsed.model_dump()
    except GeminiError:
        raise
    except Exception as exc:  # network, quota, bad JSON, safety block
        raise GeminiError(f"Gemini request failed: {exc}") from exc
