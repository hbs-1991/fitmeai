import pytest
from unittest.mock import patch, MagicMock

from nutrition_agent.services.whisper import transcribe_voice


@pytest.mark.asyncio
async def test_transcribe_voice_returns_text():
    with patch("nutrition_agent.services.whisper._get_client", return_value=MagicMock()), \
         patch("nutrition_agent.services.whisper._transcribe_sync", return_value="Я съел овсянку на завтрак"):
        result = await transcribe_voice("/tmp/voice.ogg")
        assert result == "Я съел овсянку на завтрак"


@pytest.mark.asyncio
async def test_transcribe_voice_returns_none_without_api_key():
    with patch("nutrition_agent.services.whisper._get_client", return_value=None):
        result = await transcribe_voice("/tmp/voice.ogg")
        assert result is None
