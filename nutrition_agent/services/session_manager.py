from __future__ import annotations

import json
from pathlib import Path


class SessionManager:
    def __init__(self, storage_path: str) -> None:
        self._path = Path(storage_path)
        self._sessions: dict[str, str] = {}
        self._load()

    def _key(self, chat_id: int, thread_id: int | None = None) -> str:
        return f"{chat_id}:{thread_id or 0}"

    def get_session(self, chat_id: int, thread_id: int | None = None) -> str | None:
        return self._sessions.get(self._key(chat_id, thread_id))

    def set_session(
        self, chat_id: int, session_id: str, thread_id: int | None = None
    ) -> None:
        self._sessions[self._key(chat_id, thread_id)] = session_id
        self._save()

    def clear_session(self, chat_id: int, thread_id: int | None = None) -> None:
        key = self._key(chat_id, thread_id)
        self._sessions.pop(key, None)
        self._save()

    def _load(self) -> None:
        if self._path.exists():
            self._sessions = json.loads(self._path.read_text(encoding="utf-8"))

    def _save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(
            json.dumps(self._sessions, indent=2), encoding="utf-8"
        )
