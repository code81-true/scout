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
    """Create tables if they do not exist, run migrations."""
    conn = _connect()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS sessions (
            key TEXT PRIMARY KEY,
            state TEXT NOT NULL DEFAULT 'interviewing',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            state_changed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            pseudonym TEXT DEFAULT 'Anonymous',
            started INTEGER DEFAULT 0,
            outcome TEXT DEFAULT NULL,
            recipient TEXT DEFAULT NULL,
            notes TEXT DEFAULT NULL
        );
        CREATE TABLE IF NOT EXISTS transcripts (
            key TEXT PRIMARY KEY,
            transcript TEXT NOT NULL DEFAULT '[]',
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    """)
    # Migration: add outcome and recipient columns if missing
    try:
        conn.execute("SELECT outcome FROM sessions LIMIT 1")
    except sqlite3.OperationalError:
        conn.execute("ALTER TABLE sessions ADD COLUMN outcome TEXT DEFAULT NULL")
        logger.info("Migration: added outcome column to sessions")
    try:
        conn.execute("SELECT recipient FROM sessions LIMIT 1")
    except sqlite3.OperationalError:
        conn.execute("ALTER TABLE sessions ADD COLUMN recipient TEXT DEFAULT NULL")
        logger.info("Migration: added recipient column to sessions")
    try:
        conn.execute("SELECT notes FROM sessions LIMIT 1")
    except sqlite3.OperationalError:
        conn.execute("ALTER TABLE sessions ADD COLUMN notes TEXT DEFAULT NULL")
        logger.info("Migration: added notes column to sessions")
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


def set_outcome(key: str, outcome: str) -> None:
    """Set the outcome for a session."""
    valid_outcomes = {
        "completed", "sufficient", "user_terminated",
        "safety_exit", "abandoned", "technical_failure",
    }
    if outcome not in valid_outcomes:
        logger.warning("Invalid outcome %s for key %s", outcome, key)
        return
    conn = _connect()
    conn.execute("UPDATE sessions SET outcome = ? WHERE key = ?", (outcome, key))
    conn.commit()
    conn.close()


def set_recipient(key: str, recipient: str) -> None:
    """Set the recipient name/email for a key."""
    conn = _connect()
    conn.execute("UPDATE sessions SET recipient = ? WHERE key = ?", (recipient, key))
    conn.commit()
    conn.close()


def set_note(key: str, note: str) -> None:
    """Set a note for a session."""
    conn = _connect()
    conn.execute("UPDATE sessions SET notes = ? WHERE key = ?", (note, key))
    conn.commit()
    conn.close()


def get_all_sessions() -> list[dict]:
    """Return all sessions ordered by creation date descending."""
    conn = _connect()
    rows = conn.execute(
        "SELECT key, state, outcome, recipient, notes, created_at, pseudonym FROM sessions ORDER BY created_at DESC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


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
    """Delete transcript only. Sessions row is permanent history."""
    conn = _connect()
    conn.execute("DELETE FROM transcripts WHERE key = ?", (key,))
    conn.commit()
    conn.close()


def get_session_stats() -> dict:
    """Return summary statistics for the admin dashboard."""
    conn = _connect()
    total = conn.execute("SELECT COUNT(*) FROM sessions").fetchone()[0]
    active = conn.execute(
        "SELECT COUNT(*) FROM sessions WHERE state IN ('interviewing', 'closing')"
    ).fetchone()[0]
    completed = conn.execute(
        "SELECT COUNT(*) FROM sessions WHERE outcome = 'completed'"
    ).fetchone()[0]
    sufficient = conn.execute(
        "SELECT COUNT(*) FROM sessions WHERE outcome = 'sufficient'"
    ).fetchone()[0]
    abandoned = conn.execute(
        "SELECT COUNT(*) FROM sessions WHERE outcome = 'abandoned'"
    ).fetchone()[0]
    technical = conn.execute(
        "SELECT COUNT(*) FROM sessions WHERE outcome = 'technical_failure'"
    ).fetchone()[0]
    conn.close()
    return {
        "total": total,
        "active": active,
        "completed": completed,
        "sufficient": sufficient,
        "abandoned": abandoned,
        "technical_failure": technical,
    }
