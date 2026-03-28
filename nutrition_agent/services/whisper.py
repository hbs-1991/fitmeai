from __future__ import annotations

import asyncio
import logging
import os

from openai import OpenAI

logger = logging.getLogger(__name__)

_client: OpenAI | None = None


def _get_client() -> OpenAI | None:
    global _client
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return None
    if _client is None:
        _client = OpenAI(api_key=api_key)
    return _client


def _transcribe_sync(client: OpenAI, file_path: str) -> str:
    """Synchronous transcription — runs in a thread to avoid blocking the event loop."""
    with open(file_path, "rb") as audio_file:
        response = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            language="ru",
        )
    return response.text


async def transcribe_voice(file_path: str) -> str | None:
    """Transcribe an audio file using OpenAI Whisper API. Returns text or None."""
    client = _get_client()
    if client is None:
        logger.warning("OPENAI_API_KEY not set, cannot transcribe voice")
        return None

    try:
        return await asyncio.to_thread(_transcribe_sync, client, file_path)
    except Exception:
        logger.exception("Failed to transcribe %s", file_path)
        return None
