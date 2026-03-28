import json
import pytest
from pathlib import Path

from nutrition_agent.services.session_manager import SessionManager


@pytest.fixture
def storage_path(tmp_path):
    return str(tmp_path / "sessions.json")


def test_set_and_get_session(storage_path):
    mgr = SessionManager(storage_path)
    mgr.set_session(chat_id=123, session_id="sess-abc")
    assert mgr.get_session(chat_id=123) == "sess-abc"


def test_get_nonexistent_session(storage_path):
    mgr = SessionManager(storage_path)
    assert mgr.get_session(chat_id=999) is None


def test_thread_id_isolation(storage_path):
    mgr = SessionManager(storage_path)
    mgr.set_session(chat_id=123, session_id="sess-main", thread_id=None)
    mgr.set_session(chat_id=123, session_id="sess-diary", thread_id=42)

    assert mgr.get_session(chat_id=123) == "sess-main"
    assert mgr.get_session(chat_id=123, thread_id=42) == "sess-diary"


def test_persistence_across_instances(storage_path):
    mgr1 = SessionManager(storage_path)
    mgr1.set_session(chat_id=10, session_id="sess-persist")

    mgr2 = SessionManager(storage_path)
    assert mgr2.get_session(chat_id=10) == "sess-persist"


def test_clear_session(storage_path):
    mgr = SessionManager(storage_path)
    mgr.set_session(chat_id=123, session_id="sess-old")
    mgr.clear_session(chat_id=123)
    assert mgr.get_session(chat_id=123) is None
