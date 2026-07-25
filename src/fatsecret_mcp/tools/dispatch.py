"""Shared plumbing for action-dispatch tools.

Four fat tools replace twenty thin ones: every tool schema lives in the model's
cached prompt prefix and is paid for on every request, whether or not the turn is
about food. Actions cost one enum value; tools cost a whole schema.
"""

from __future__ import annotations

import functools

from ..utils import get_logger, APIError, ActionError

logger = get_logger(__name__)

# ActionError is defined in ..utils, not here, so that report.py can raise it without
# importing this package — tools/__init__ pulls in diary.py, which imports report.py.
# Re-exported because this is where callers and tests reasonably look for it.
__all__ = ["ActionError", "require", "unknown", "guard"]


def require(params: dict, action: str, *names: str) -> tuple:
    """Return the named params, or raise naming EVERY missing one.

    All at once, not first-failure: a model that gets one name per round trip
    spends four turns discovering four required fields.
    """
    missing = [n for n in names if params.get(n) in (None, "")]
    if missing:
        raise ActionError(f"action={action!r} requires: {', '.join(missing)}")
    return tuple(params[n] for n in names)


def unknown(action: str, valid: tuple[str, ...]) -> dict:
    return {"error": f"unknown action {action!r}; expected one of: {', '.join(valid)}"}


def guard(fn):
    """Every tool returns a dict, always. An exception crossing the MCP boundary
    reads to the model as an infrastructure failure it cannot fix; an error string
    reads as something to correct and retry."""
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except ActionError as e:
            return {"error": str(e)}
        except APIError as e:
            logger.error("FatSecret API error in %s: %s", fn.__name__, e)
            return {"error": f"FatSecret API error: {e}"}
        except Exception as e:  # noqa: BLE001 — the boundary is the point
            logger.exception("unexpected error in %s", fn.__name__)
            return {"error": f"Unexpected error: {e}"}
    return wrapper
