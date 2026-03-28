import os
import pytest


def test_config_loads_telegram_token(monkeypatch):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test-token-123")
    monkeypatch.setenv("FATSECRET_CLIENT_ID", "cid")
    monkeypatch.setenv("FATSECRET_CLIENT_SECRET", "csec")

    from nutrition_agent.config import Config

    cfg = Config()
    assert cfg.telegram_bot_token == "test-token-123"


def test_config_raises_without_telegram_token(monkeypatch):
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)

    from nutrition_agent.config import Config

    with pytest.raises(ValueError, match="TELEGRAM_BOT_TOKEN"):
        Config()


def test_config_optional_openai_key(monkeypatch):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "t")
    monkeypatch.setenv("FATSECRET_CLIENT_ID", "cid")
    monkeypatch.setenv("FATSECRET_CLIENT_SECRET", "csec")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    from nutrition_agent.config import Config

    cfg = Config()
    assert cfg.openai_api_key is None


def test_config_project_dir():
    from nutrition_agent.config import PROJECT_DIR

    assert PROJECT_DIR.exists()
