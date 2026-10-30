"""
auth.py — API-key validation and session-state helpers.

The key is stored ONLY in st.session_state and is never written to disk,
logs, or environment variables.
"""

from __future__ import annotations

import streamlit as st
from openai import OpenAI, AuthenticationError, APIConnectionError, RateLimitError


# ---------------------------------------------------------------------------
# Session-state helpers
# ---------------------------------------------------------------------------

def is_authenticated() -> bool:
    """Return True if the user has a validated OpenAI key in this session."""
    return bool(st.session_state.get("authenticated", False))


def get_api_key() -> str | None:
    """Return the raw API key stored in session_state (None if not set)."""
    return st.session_state.get("openai_api_key")


def store_key(key: str) -> None:
    """Persist key and mark session as authenticated."""
    st.session_state["openai_api_key"] = key
    st.session_state["authenticated"] = True


def logout() -> None:
    """Clear all session data — key, auth flag, and form answers."""
    for k in list(st.session_state.keys()):
        del st.session_state[k]


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def validate_key(key: str) -> tuple[bool, str]:
    """
    Make a lightweight test call to the OpenAI API.

    Returns (True, "") on success or (False, error_message) on failure.
    We intentionally do NOT log or print the key.
    """
    if not key.startswith("sk-"):
        return False, "That doesn't look like an OpenAI API key (should start with 'sk-')."

    try:
        client = OpenAI(api_key=key)
        # Cheapest possible call: list available models
        client.models.list()
        return True, ""

    except AuthenticationError:
        return False, "Invalid API key — please double-check and try again."
    except RateLimitError:
        return False, "Rate limit reached on that key. Wait a moment and retry."
    except APIConnectionError:
        return False, "Couldn't reach OpenAI. Check your internet connection."
    except Exception as exc:  # noqa: BLE001
        return False, f"Unexpected error: {exc}"
