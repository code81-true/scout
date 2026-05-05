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
        CREATE TABLE IF NOT EXISTS deliveries (
            token TEXT PRIMARY KEY,
            key TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            expires_at DATETIME NOT NULL,
            portrait_downloaded INTEGER DEFAULT 0,
            meridian_downloaded INTEGER DEFAULT 0,
            downloaded INTEGER DEFAULT 0,
            downloaded_at DATETIME DEFAULT NULL
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
    try:
        conn.execute("SELECT bridged FROM sessions LIMIT 1")
    except sqlite3.OperationalError:
        conn.execute("ALTER TABLE sessions ADD COLUMN bridged INTEGER DEFAULT 0")
        logger.info("Migration: added bridged column to sessions")
    try:
        conn.execute("SELECT archived FROM sessions LIMIT 1")
    except sqlite3.OperationalError:
        conn.execute("ALTER TABLE sessions ADD COLUMN archived INTEGER DEFAULT 0")
        logger.info("Migration: added archived column to sessions")
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
    """Insert a new session in interviewing state. Promotes 'pending' rows created by admin annotations.

    On promotion, created_at is reset to 'now' so it reflects the first /auth call, not the prior
    admin-annotation timestamp.
    """
    conn = _connect()
    now = datetime.now(timezone.utc).isoformat()
    conn.execute(
        "INSERT INTO sessions (key, state, created_at, state_changed_at) "
        "VALUES (?, 'interviewing', ?, ?) "
        "ON CONFLICT(key) DO UPDATE SET state = 'interviewing', created_at = ?, state_changed_at = ? "
        "WHERE sessions.state = 'pending'",
        (key, now, now, now, now),
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
    """Set the outcome for a session. Creates a 'pending' row if the key has no session yet."""
    valid_outcomes = {
        "completed", "sufficient", "user_terminated",
        "safety_exit", "abandoned", "technical_failure",
    }
    if outcome not in valid_outcomes:
        logger.warning("Invalid outcome %s for key %s", outcome, key)
        return
    conn = _connect()
    now = datetime.now(timezone.utc).isoformat()
    conn.execute(
        "INSERT INTO sessions (key, state, outcome, created_at, state_changed_at) "
        "VALUES (?, 'pending', ?, ?, ?) "
        "ON CONFLICT(key) DO UPDATE SET outcome = excluded.outcome",
        (key, outcome, now, now),
    )
    conn.commit()
    conn.close()


def set_recipient(key: str, recipient: str) -> None:
    """Set the recipient name/email for a key. Creates a 'pending' row if missing."""
    conn = _connect()
    now = datetime.now(timezone.utc).isoformat()
    conn.execute(
        "INSERT INTO sessions (key, state, recipient, created_at, state_changed_at) "
        "VALUES (?, 'pending', ?, ?, ?) "
        "ON CONFLICT(key) DO UPDATE SET recipient = excluded.recipient",
        (key, recipient, now, now),
    )
    conn.commit()
    conn.close()


def set_note(key: str, note: str) -> None:
    """Set a note for a session. Creates a 'pending' row if the key has no session yet."""
    conn = _connect()
    now = datetime.now(timezone.utc).isoformat()
    conn.execute(
        "INSERT INTO sessions (key, state, notes, created_at, state_changed_at) "
        "VALUES (?, 'pending', ?, ?, ?) "
        "ON CONFLICT(key) DO UPDATE SET notes = excluded.notes",
        (key, note, now, now),
    )
    conn.commit()
    conn.close()


def has_transcript(key: str) -> bool:
    """Check whether a transcript row exists for this key."""
    conn = _connect()
    row = conn.execute("SELECT 1 FROM transcripts WHERE key = ?", (key,)).fetchone()
    conn.close()
    return row is not None


def get_all_sessions() -> list[dict]:
    """Return all sessions ordered by creation date descending.

    Includes archived sessions; admin callers filter them in the view layer
    so that keys.txt entries with no surviving session row are still listed.
    """
    conn = _connect()
    rows = conn.execute(
        "SELECT key, state, outcome, recipient, notes, created_at, pseudonym, "
        "bridged, archived "
        "FROM sessions ORDER BY created_at DESC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def set_bridged(key: str, bridged: bool) -> None:
    """Mark a session as bridged (spine sent to MTN) or unmark it."""
    conn = _connect()
    now = datetime.now(timezone.utc).isoformat()
    conn.execute(
        "INSERT INTO sessions (key, state, bridged, created_at, state_changed_at) "
        "VALUES (?, 'pending', ?, ?, ?) "
        "ON CONFLICT(key) DO UPDATE SET bridged = excluded.bridged",
        (key, 1 if bridged else 0, now, now),
    )
    conn.commit()
    conn.close()


def archive_session(key: str) -> None:
    """Soft-delete a session — hides it from the admin table.

    The row stays in the database. Files are moved out of the spine
    directory by the calling route. Re-running has no additional effect.
    """
    conn = _connect()
    now = datetime.now(timezone.utc).isoformat()
    conn.execute(
        "INSERT INTO sessions (key, state, archived, created_at, state_changed_at) "
        "VALUES (?, 'pending', 1, ?, ?) "
        "ON CONFLICT(key) DO UPDATE SET archived = 1",
        (key, now, now),
    )
    conn.commit()
    conn.close()


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
    """Historically deleted the transcript row on session burn. Now a no-op.

    Transcripts retained during beta phase for quality review and regression diagnosis.
    DEC-SCOUT-017: transcripts deleted only after commercial launch and explicit operator instruction.
    """
    # Intentionally does nothing. The sessions row is kept permanently per
    # DEC-SCOUT-014; the transcripts row is now also kept per DEC-SCOUT-017.
    return


def create_delivery(key: str, token: str, expires_at: str) -> None:
    """Record a new delivery token bound to a key."""
    conn = _connect()
    conn.execute(
        "INSERT INTO deliveries (token, key, expires_at) VALUES (?, ?, ?)",
        (token, key, expires_at),
    )
    conn.commit()
    conn.close()


def get_delivery(token: str) -> dict | None:
    """Return delivery row as dict, or None if not found."""
    conn = _connect()
    row = conn.execute("SELECT * FROM deliveries WHERE token = ?", (token,)).fetchone()
    conn.close()
    return dict(row) if row else None


def mark_downloaded(token: str, kind: str) -> None:
    """Mark portrait or meridian as downloaded for this token. Sets combined flag if both done."""
    if kind not in ("portrait", "meridian"):
        return
    column = f"{kind}_downloaded"
    conn = _connect()
    conn.execute(f"UPDATE deliveries SET {column} = 1 WHERE token = ?", (token,))
    row = conn.execute(
        "SELECT portrait_downloaded, meridian_downloaded FROM deliveries WHERE token = ?",
        (token,),
    ).fetchone()
    if row and row["portrait_downloaded"] and row["meridian_downloaded"]:
        now = datetime.now(timezone.utc).isoformat()
        conn.execute(
            "UPDATE deliveries SET downloaded = 1, downloaded_at = ? WHERE token = ?",
            (now, token),
        )
    conn.commit()
    conn.close()


def is_delivery_valid(token: str) -> bool:
    """True if the token exists, both files are not yet downloaded, and expiry is in the future."""
    delivery = get_delivery(token)
    if delivery is None or delivery["downloaded"]:
        return False
    try:
        expires = datetime.fromisoformat(delivery["expires_at"])
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)
        return datetime.now(timezone.utc) < expires
    except (ValueError, TypeError):
        return False


def get_session_stats() -> dict:
    """Return summary statistics for the admin dashboard. Excludes 'pending' (admin-annotated, unauthenticated)."""
    conn = _connect()
    total = conn.execute("SELECT COUNT(*) FROM sessions WHERE state != 'pending'").fetchone()[0]
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
