"""Flask web interface for Scout."""

from __future__ import annotations

import json
import os

from dotenv import load_dotenv

load_dotenv()

from flask import Flask, render_template, request, Response, session as flask_session
from flask_session import Session as FlaskSessionExt

from scout.engine import (
    TEST_MODEL,
    create_client,
    generate_portrait,
    generate_yaml_sections,
    send_message_stream,
)
from scout.session import Session

app = Flask(__name__)
app.secret_key = "scout-session-key"

TRANSCRIPT_DIR = os.getenv("TRANSCRIPT_DIR", "sessions/transcripts")
FLASK_SESSION_DIR = os.getenv("FLASK_SESSION_DIR", "sessions/flask_sessions")
os.makedirs(TRANSCRIPT_DIR, exist_ok=True)
os.makedirs(FLASK_SESSION_DIR, exist_ok=True)

app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_FILE_DIR"] = FLASK_SESSION_DIR
app.config["SESSION_PERMANENT"] = False
FlaskSessionExt(app)

# Per-key session isolation
client = create_client()
_sessions: dict[str, Session] = {}
_started_keys: set[str] = set()


def get_session(key: str) -> Session:
    """Get or create a Session for the given key."""
    if key not in _sessions:
        _sessions[key] = Session()
    return _sessions[key]

KEYS_PATH = os.path.join(os.path.dirname(__file__), "access", "keys.txt")


def _read_keys() -> list[str]:
    """Read keys.txt lines."""
    with open(KEYS_PATH, encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]


def _write_keys(lines: list[str]) -> None:
    """Write keys.txt lines."""
    with open(KEYS_PATH, "w", encoding="utf-8") as f:
        for line in lines:
            f.write(line + "\n")


def _is_test_key(key: str) -> bool:
    """Check if a key is a test key."""
    return str(key).upper().startswith("TEST")


def _require_auth():
    """Return error response if session is not authenticated, else None."""
    if not flask_session.get("scout_key"):
        return {"error": "unauthorised"}, 401
    return None


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/auth", methods=["POST"])
def auth():
    """Authenticate a single-use key."""
    data = request.get_json()
    key = data.get("key", "").strip().upper()

    if not key:
        return {"success": False, "reason": "invalid"}

    lines = _read_keys()
    for i, line in enumerate(lines):
        parts = line.split(":")
        if len(parts) != 2:
            continue
        k, status = parts[0], parts[1]
        if k == key:
            if status == "used":
                return {"success": False, "reason": "expired"}
            transcript_path = os.path.join(TRANSCRIPT_DIR, f"{key}_transcript.json")
            if status == "active":
                # Active key — only allow resume if transcript exists
                if not os.path.exists(transcript_path):
                    return {"success": False, "reason": "invalid"}
                # Resume: load transcript into per-key session
                flask_session["scout_key"] = key
                restored = Session()
                with open(transcript_path, "r", encoding="utf-8") as f:
                    restored.transcript = json.load(f)
                _sessions[key] = restored
                _started_keys.add(key)
                flask_session["resumed"] = True
                last_assistant = next(
                    (m["content"] for m in reversed(restored.transcript)
                     if m["role"] == "assistant"), ""
                )
                flask_session["last_topic"] = last_assistant[:120]
                return {"success": True}
            # Unused key — fresh session
            lines[i] = f"{k}:active"
            _write_keys(lines)
            flask_session["scout_key"] = key
            _sessions[key] = Session()
            flask_session["resumed"] = False
            flask_session["last_topic"] = ""
            return {"success": True}

    return {"success": False, "reason": "invalid"}


@app.route("/burn", methods=["POST"])
def burn():
    """Burn the active key after YAML delivery."""
    key = flask_session.get("scout_key")
    if not key:
        return {"error": "no active key"}, 400

    lines = _read_keys()
    for i, line in enumerate(lines):
        parts = line.split(":")
        if len(parts) == 2 and parts[0] == key:
            lines[i] = f"{key}:used"
            _write_keys(lines)
            break

    # Delete transcript file after burn
    transcript_path = os.path.join(TRANSCRIPT_DIR, f"{key}_transcript.json")
    try:
        os.remove(transcript_path)
    except FileNotFoundError:
        pass

    # Clean up per-key session state
    _sessions.pop(key, None)
    _started_keys.discard(key)

    return {"success": True}


@app.route("/chat", methods=["POST"])
def chat():
    auth_err = _require_auth()
    if auth_err:
        return auth_err

    active_key = flask_session.get("scout_key", "")
    sess = get_session(active_key)

    # Resume acknowledgement — inject system note into transcript
    if flask_session.get("resumed"):
        last_topic = flask_session.get("last_topic", "where we left off")
        resume_note = (
            f"[SYSTEM: This session was resumed after a disconnection. "
            f"Before your next question, acknowledge the return warmly "
            f"in one sentence using this message adapted naturally to "
            f"your voice: 'Welcome back. To protect your work from "
            f"interruptions, your session was held temporarily — like "
            f"a document that saves itself while you write. The moment "
            f"your spine is delivered, it is deleted completely. Nothing "
            f"is kept. We were talking about: {last_topic}. "
            f"Shall we continue?' Then continue the interview normally.]"
        )
        sess.transcript.append({
            "role": "user",
            "content": resume_note
        })
        flask_session["resumed"] = False

    data = request.get_json()
    message = data.get("message", "").strip()

    if not message:
        return {"error": "empty message"}, 400

    # Resolve prompt and model based on key type
    if _is_test_key(active_key):
        from scout.test_prompt import TEST_PROMPT
        stream_kwargs = {"system_prompt": TEST_PROMPT, "model": TEST_MODEL}
    else:
        stream_kwargs = {}

    # First call: inject the synthetic "Begin." to get Scout's opening
    if active_key not in _started_keys:
        _started_keys.add(active_key)
        sess.add_user("Begin.")
        opening_chunks: list[str] = []

        def generate_opening():
            for chunk in send_message_stream(client, sess.transcript, **stream_kwargs):
                opening_chunks.append(chunk)
                yield f"data: {json.dumps({'text': chunk})}\n\n"
            full_opening = "".join(opening_chunks)
            sess.add_assistant(full_opening)
            yield f"data: {json.dumps({'done': True})}\n\n"

        return Response(generate_opening(), mimetype="text/event-stream")

    # Normal turn
    sess.add_user(message)
    collected: list[str] = []

    def generate():
        for chunk in send_message_stream(client, sess.transcript, **stream_kwargs):
            collected.append(chunk)
            yield f"data: {json.dumps({'text': chunk})}\n\n"
        full_reply = "".join(collected)
        sess.add_assistant(full_reply)
        # Save transcript to disk after every exchange
        transcript_path = os.path.join(TRANSCRIPT_DIR, f"{active_key}_transcript.json")
        with open(transcript_path, "w", encoding="utf-8") as f:
            json.dump(sess.transcript, f, ensure_ascii=False, indent=2)
        complete = (
            "Give me a moment" in full_reply
            and len(sess.transcript) >= 40
        )
        # Test mode: YAML in response IS the completion signal
        if _is_test_key(active_key) and not complete:
            complete = (
                "```yaml" in full_reply
                and "spine:" in full_reply
            )
        yield f"data: {json.dumps({'done': True, 'session_complete': complete})}\n\n"

    return Response(generate(), mimetype="text/event-stream")


@app.route("/generate", methods=["POST"])
def generate_spine():
    """Generate the spine.yaml and portrait after the interview ends."""
    auth_err = _require_auth()
    if auth_err:
        return auth_err

    from datetime import datetime

    gen_key = flask_session.get("scout_key", "")
    gen_model = TEST_MODEL if _is_test_key(gen_key) else None
    sess = get_session(gen_key)
    yaml_doc = generate_yaml_sections(client, sess.transcript, model=gen_model)
    portrait = generate_portrait(client, sess.transcript, model=gen_model)

    # Save YAML to filesystem
    user_id = flask_session.get("user_id") or datetime.now().strftime("%Y%m%d_%H%M%S")
    date_str = datetime.now().strftime("%Y-%m-%d")
    spine_dir = "/home/scout/spines"
    os.makedirs(spine_dir, exist_ok=True)
    filepath = os.path.join(spine_dir, f"{user_id}_{date_str}.yaml")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(yaml_doc)

    return {"yaml": yaml_doc, "portrait": portrait}


@app.route("/portrait", methods=["POST"])
def portrait():
    """Serve the portrait display page."""
    auth_err = _require_auth()
    if auth_err:
        return auth_err

    data = request.get_json()
    flask_session["pseudonym"] = data.get("pseudonym", "Anonymous")
    flask_session["date"] = data.get("date", "")
    flask_session["user_id"] = data.get("user_id", "")
    return render_template(
        "portrait.html",
        pseudonym=flask_session["pseudonym"],
        date=flask_session["date"],
        user_id=flask_session["user_id"],
    )


@app.route("/test-generate", methods=["POST"])
def test_generate():
    """Dev-only route: run generation against a mock transcript."""
    import os

    mock_path = os.path.join(os.path.dirname(__file__), "tests", "mock_transcript.json")
    if not os.path.exists(mock_path):
        return {"error": "No mock transcript found. Create tests/mock_transcript.json first."}, 404

    with open(mock_path, encoding="utf-8") as f:
        transcript = json.load(f)

    yaml_doc = generate_yaml_sections(client, transcript)
    portrait = generate_portrait(client, transcript)
    return {"yaml": yaml_doc, "portrait": portrait}


if __name__ == "__main__":
    app.run(debug=True, port=5000)
