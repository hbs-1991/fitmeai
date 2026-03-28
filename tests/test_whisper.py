import pytest
from unittest.mock import patch, MagicMock

from nutrition_agent.services.whisper import transcribe_voice


@pytest.mark.asyncio
async def test_transcribe_voice_returns_text(tmp_path):
    # Create a dummy audio file so open() succeeds
    dummy_file = tmp_path / "voice.ogg"
    dummy_file.write_bytes(b"fake audio data")

    mock_response = MagicMock()
    mock_response.text = "Я съел овсянку на завтрак"

    mock_client = MagicMock()
    mock_client.audio.transcriptions.create = MagicMock(return_value=mock_response)

    with patch("nutrition_agent.services.whisper._get_client", return_value=mock_client):
        result = await transcribe_voice(str(dummy_file))
        assert result == "Я съел овсянку на завтрак"


@pytest.mark.asyncio
async def test_transcribe_voice_returns_none_without_api_key():
    with patch("nutrition_agent.services.whisper._get_client", return_value=None):
        result = await transcribe_voice("/tmp/voice.ogg")
        assert result is None
