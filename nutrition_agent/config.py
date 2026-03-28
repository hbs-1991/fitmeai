from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

PROJECT_DIR = Path(__file__).resolve().parent.parent


class Config:
    def __init__(self) -> None:
        self.telegram_bot_token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
        if not self.telegram_bot_token:
            raise ValueError("TELEGRAM_BOT_TOKEN environment variable is required")

        self.openai_api_key: str | None = os.environ.get("OPENAI_API_KEY")
        self.anthropic_auth_token: str | None = os.environ.get("ANTHROPIC_AUTH_TOKEN")
        self.anthropic_api_key: str | None = os.environ.get("ANTHROPIC_API_KEY")

        self.fatsecret_client_id = os.environ.get("FATSECRET_CLIENT_ID", "")
        self.fatsecret_client_secret = os.environ.get("FATSECRET_CLIENT_SECRET", "")
        if not self.fatsecret_client_id or not self.fatsecret_client_secret:
            raise ValueError(
                "FATSECRET_CLIENT_ID and FATSECRET_CLIENT_SECRET are required"
            )

        self.mcp_server_command = "python"
        self.mcp_server_args = ["main.py"]
        self.mcp_server_cwd = str(PROJECT_DIR)
