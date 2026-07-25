"""Which env var names count as the FatSecret application credentials.

The platform page at platform.fatsecret.com/api labels them "Consumer Key" and
"Consumer Secret" — the OAuth 1.0 naming — while this codebase historically called
them CLIENT_ID/CLIENT_SECRET. config.py accepts both. That aliasing was undocumented
folklore until it cost a real deploy: a claude-hermes catalog manifest declared the
CLIENT_* names, the operator had set the CONSUMER_* ones from the platform page, and
the install refused with a message naming only the spelling they had not used.

These tests pin the behaviour AND the wording of the failure, because the wording is
what turns that dead end into a one-line fix.
"""

import importlib
import sys

KEY = "abcdefghij1234567890"
SECRET = "zyxwvutsrq0987654321"
_NAMES = ("FATSECRET_CLIENT_ID", "FATSECRET_CLIENT_SECRET",
          "FATSECRET_CONSUMER_KEY", "FATSECRET_CONSUMER_SECRET")


def _config(monkeypatch, **env):
    """Re-import Config under a controlled environment.

    config.py calls load_dotenv() at import time, so without stubbing it a developer
    with a populated .env would get real credentials injected here and every one of
    these assertions would pass for the wrong reason. That is not hypothetical — it
    is exactly how this aliasing stayed unverified for so long.
    """
    for name in [m for m in list(sys.modules) if m.startswith("fatsecret_mcp")]:
        del sys.modules[name]
    import dotenv
    monkeypatch.setattr(dotenv, "load_dotenv", lambda *a, **k: False)
    for name in _NAMES:
        monkeypatch.delenv(name, raising=False)
    for name, value in env.items():
        monkeypatch.setenv(name, value)
    return importlib.import_module("fatsecret_mcp.config").Config


def test_consumer_names_alone_are_valid_credentials(monkeypatch):
    """The names the FatSecret platform page actually shows must work on their own."""
    cfg = _config(monkeypatch, FATSECRET_CONSUMER_KEY=KEY,
                  FATSECRET_CONSUMER_SECRET=SECRET)
    assert cfg.validate() == (True, None)
    assert (cfg.CLIENT_ID, cfg.CLIENT_SECRET) == (KEY, SECRET)


def test_client_names_alone_are_valid_credentials(monkeypatch):
    cfg = _config(monkeypatch, FATSECRET_CLIENT_ID=KEY, FATSECRET_CLIENT_SECRET=SECRET)
    assert cfg.validate() == (True, None)
    assert (cfg.CLIENT_ID, cfg.CLIENT_SECRET) == (KEY, SECRET)


def test_client_names_win_when_both_pairs_are_set(monkeypatch):
    """Documented precedence, so a stale CLIENT_ID cannot silently shadow a correct
    CONSUMER_KEY. Set one pair, not a mix."""
    cfg = _config(monkeypatch,
                  FATSECRET_CLIENT_ID="CLIENT" + KEY,
                  FATSECRET_CLIENT_SECRET="CLIENT" + SECRET,
                  FATSECRET_CONSUMER_KEY=KEY,
                  FATSECRET_CONSUMER_SECRET=SECRET)
    assert cfg.CLIENT_ID == "CLIENT" + KEY
    assert cfg.CLIENT_SECRET == "CLIENT" + SECRET


def test_a_half_set_pair_is_not_valid(monkeypatch):
    """CLIENT_ID without CLIENT_SECRET is the exact state that broke the deploy."""
    ok, msg = _config(monkeypatch, FATSECRET_CLIENT_ID=KEY).validate()
    assert not ok and "SECRET" in msg


def test_the_missing_credential_error_names_both_spellings(monkeypatch):
    """An operator who set CONSUMER_KEY and is told only that CLIENT_ID is missing
    cannot tell they set the right credential under a name the message never mentions.
    Both spellings appear, or the error is a dead end."""
    ok, msg = _config(monkeypatch).validate()
    assert not ok
    assert "FATSECRET_CONSUMER_KEY" in msg and "FATSECRET_CLIENT_ID" in msg
