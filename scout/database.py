"""SQLite session state database for Scout."""

from __future__ import annotations

import json
import logging
import os
import sqlite3
from datetime import datetime, timezone

DB_PATH = os.getenv("DB_PATH", "sessions/scout.db")

logger = logging.getLogger(__name__)


def _connect() -> sqlite3.Connection:
    """Create a new SQLite connection with WAL mode."""
    os.makedirs(os.path.dirname(DB_PATH) or ".", exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db() -> None:
    """Create tables if they do not exist."""
    conn = _connect()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS sessions (
            key TEXT PRIMARY KEY,
            state TEXT NOT NULL DEFAULT 'interviewing',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            state_changed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            pseudonym TEXT DEFAULT 'Anonymous',
            started INTEGER DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS transcripts (
            key TEXT PRIMARY KEY,
            transcript TEXT NOT NULL DEFAULT '[]',
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    """)
    conn.commit()
    conn.close()
    logger.info("Database initialised at %s", DB_PATH)


def get_session_state(key: str) -> dict | None:
    """Return session row as dict, or None if not found."""
    conn = _connect()
    row = conn.execute("SELECT * FROM sessions WHERE key = ?", (key,)).fetchone()
    conn.close()
    if row is None:
        return None
    return dict(row)


def create_session(key: str) -> None:
    """Insert a new session in interviewing state."""
    conn = _connect()
    now = datetime.now(timezone.utc).isoformat()
    conn.execute(
        "INSERT OR IGNORE INTO sessions (key, state, created_at, state_changed_at) VALUES (?, 'interviewing', ?, ?)",
        (key, now, now),
    )
    conn.commit()
    conn.close()


def mark_started(key: str) -> None:
    """Mark session as started (opening message delivered)."""
    conn = _connect()
    conn.execute("UPDATE sessions SET started = 1 WHERE key = ?", (key,))
    conn.commit()
    conn.close()


def is_started(key: str) -> bool:
    """Check if the session opening has been delivered."""
    conn = _connect()
    row = conn.execute("SELECT started FROM sessions WHERE key = ?", (key,)).fetchone()
    conn.close()
    return bool(row and row["started"])


def transition_state(key: str, new_state: str) -> None:
    """Transition session to a new state. Logs invalid transitions."""
    valid_transitions = {
        "interviewing": ["closing"],
        "closing": ["generating"],
        "generating": ["delivered"],
    }
    conn = _connect()
    row = conn.execute("SELECT state FROM sessions WHERE key = ?", (key,)).fetchone()
    if row is None:
        logger.error("transition_state: session %s not found", key)
        conn.close()
        return

    current = row["state"]
    if new_state not in valid_transitions.get(current, []):
        logger.warning("Invalid state transition %s → %s for key %s", current, new_state, key)
        conn.close()
        return

    now = datetime.now(timezone.utc).isoformat()
    conn.execute(
        "UPDATE sessions SET state = ?, state_changed_at = ? WHERE key = ?",
        (new_state, now, key),
    )
    conn.commit()
    conn.close()
    logger.info("Session %s: %s → %s", key, current, new_state)


def set_pseudonym(key: str, pseudonym: str) -> None:
    """Store the pseudonym for a session."""
    conn = _connect()
    conn.execute("UPDATE sessions SET pseudonym = ? WHERE key = ?", (pseudonym, key))
    conn.commit()
    conn.close()


def get_pseudonym(key: str) -> str:
    """Return the pseudonym for a session."""
    conn = _connect()
    row = conn.execute("SELECT pseudonym FROM sessions WHERE key = ?", (key,)).fetchone()
    conn.close()
    return row["pseudonym"] if row else "Anonymous"


def save_transcript(key: str, transcript: list[dict]) -> None:
    """Upsert transcript as JSON."""
    conn = _connect()
    now = datetime.now(timezone.utc).isoformat()
    conn.execute(
        "INSERT INTO transcripts (key, transcript, updated_at) VALUES (?, ?, ?) "
        "ON CONFLICT(key) DO UPDATE SET transcript = ?, updated_at = ?",
        (key, json.dumps(transcript, ensure_ascii=False), now,
         json.dumps(transcript, ensure_ascii=False), now),
    )
    conn.commit()
    conn.close()


def load_transcript(key: str) -> list[dict]:
    """Load transcript from database. Returns empty list if not found."""
    conn = _connect()
    row = conn.execute("SELECT transcript FROM transcripts WHERE key = ?", (key,)).fetchone()
    conn.close()
    if row is None:
        return []
    try:
        return json.loads(row["transcript"])
    except (json.JSONDecodeError, TypeError):
        return []


def delete_transcript(key: str) -> None:
    """Delete transcript for a key."""
    conn = _connect()
    conn.execute("DELETE FROM transcripts WHERE key = ?", (key,))
    conn.commit()
    conn.close()


def get_closing_duration(key: str) -> float:
    """Return seconds since state became 'closing'. Returns 0 if not in closing."""
    conn = _connect()
    row = conn.execute(
        "SELECT state, state_changed_at FROM sessions WHERE key = ?", (key,)
    ).fetchone()
    conn.close()
    if row is None or row["state"] != "closing":
        return 0.0
    try:
        changed = datetime.fromisoformat(row["state_changed_at"])
        if changed.tzinfo is None:
            changed = changed.replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        return (now - changed).total_seconds()
    except (ValueError, TypeError):
        return 0.0


def get_stale_closing_sessions(timeout_seconds: float = 90.0) -> list[str]:
    """Return keys of sessions stuck in closing state past the timeout."""
    conn = _connect()
    rows = conn.execute(
        "SELECT key, state_changed_at FROM sessions WHERE state = 'closing'"
    ).fetchall()
    conn.close()
    stale: list[str] = []
    now = datetime.now(timezone.utc)
    for row in rows:
        try:
            changed = datetime.fromisoformat(row["state_changed_at"])
            if changed.tzinfo is None:
                changed = changed.replace(tzinfo=timezone.utc)
            if (now - changed).total_seconds() > timeout_seconds:
                stale.append(row["key"])
        except (ValueError, TypeError):
            stale.append(row["key"])
    return stale


def cleanup_session(key: str) -> None:
    """Remove all database records for a key."""
    conn = _connect()
    conn.execute("DELETE FROM sessions WHERE key = ?", (key,))
    conn.execute("DELETE FROM transcripts WHERE key = ?", (key,))
    conn.commit()
    conn.close()
