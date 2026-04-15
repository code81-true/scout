"""Flask web interface for Scout."""

from __future__ import annotations

import json
import logging
import os

from dotenv import load_dotenv

load_dotenv()

from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask, render_template, request, Response, session as flask_session
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_session import Session as FlaskSessionExt

from scout.database import (
    cleanup_session,
    create_session,
    delete_transcript,
    get_closing_duration,
    get_pseudonym,
    get_session_state,
    get_stale_closing_sessions,
    init_db,
    is_started,
    load_transcript,
    mark_started,
    save_transcript,
    set_pseudonym,
    transition_state,
)
from scout.engine import (
    TEST_MODEL,
    create_client,
    generate_constitution,
    generate_portrait,
    generate_yaml_sections,
    send_message_stream,
)
from scout.session import Session

logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "scout-session-key-dev")

TRANSCRIPT_DIR = os.getenv("TRANSCRIPT_DIR", "sessions/transcripts")
FLASK_SESSION_DIR = os.getenv("FLASK_SESSION_DIR", "sessions/flask_sessions")
SPINE_DIR = os.getenv("SPINE_DIR", "spines")
os.makedirs(TRANSCRIPT_DIR, exist_ok=True)
os.makedirs(FLASK_SESSION_DIR, exist_ok=True)
os.makedirs(SPINE_DIR, exist_ok=True)

app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_FILE_DIR"] = FLASK_SESSION_DIR
app.config["SESSION_PERMANENT"] = False
FlaskSessionExt(app)
limiter = Limiter(get_remote_address, app=app, default_limits=[])

# Initialise database
init_db()

# Anthropic client
client = create_client()

KEYS_PATH = os.path.join(os.path.dirname(__file__), "access", "keys.txt")


@app.errorhandler(429)
def ratelimit_handler(e):
    return {"error": "too many attempts, please wait"}, 429


# --- Background scheduler: closing timeout ---

def _check_closing_timeouts():
    """Transition stale closing sessions to generating."""
    stale = get_stale_closing_sessions(timeout_seconds=90.0)
    for key in stale:
        logger.info("Closing timeout: %s has been closing for >90s, transitioning to generating", key)
        transition_state(key, "generating")


scheduler = BackgroundScheduler(daemon=True)
scheduler.add_job(_check_closing_timeouts, "interval", seconds=30)
try:
    if not scheduler.running:
        scheduler.start()
except Exception:
    pass


# --- Key file helpers ---

def _read_keys() -> list[str]:
    with open(KEYS_PATH, encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]


def _write_keys(lines: list[str]) -> None:
    with open(KEYS_PATH, "w", encoding="utf-8") as f:
        for line in lines:
            f.write(line + "\n")


def _is_test_key(key: str) -> bool:
    return str(key).upper().startswith("TEST")


def _require_auth():
    if not flask_session.get("scout_key"):
        return {"error": "unauthorised"}, 401
    return None


# --- Routes ---

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/health", methods=["GET"])
def health():
    return {"status": "ok", "service": "scout"}, 200


@app.route("/robots.txt")
def robots():
    return app.send_static_file("robots.txt")


@app.route("/status", methods=["GET"])
def status():
    maintenance = os.getenv("MAINTENANCE_MODE", "false").lower() == "true"
    result = {"maintenance": maintenance}
    if maintenance:
        result["message"] = os.getenv("MAINTENANCE_MESSAGE", "Scout is briefly offline. Back shortly.")
        try:
            mins = int(os.getenv("MAINTENANCE_RETURN_MINUTES", "0"))
        except ValueError:
            mins = 0
        if mins > 0:
            result["return_minutes"] = mins
    return result, 200


@app.route("/auth", methods=["POST"])
@limiter.limit("5 per minute")
def auth():
    """Authenticate a single-use key."""
    if os.getenv("MAINTENANCE_MODE", "false").lower() == "true":
        return {"error": "maintenance", "message": "Scout is briefly offline. Back shortly."}, 503

    data = request.get_json()
    key = data.get("key", "").strip().upper()

    if not key:
        return {"success": False, "reason": "invalid"}

    lines = _read_keys()
    for i, line in enumerate(lines):
        parts = line.split(":")
        if len(parts) != 2:
            continue
        k, key_status = parts[0], parts[1]
        if k == key:
            if key_status == "used":
                return {"success": False, "reason": "expired"}

            if key_status == "active":
                # Active key — check for existing session in DB
                db_session = get_session_state(key)
                if db_session is None:
                    return {"success": False, "reason": "invalid"}

                # Resume: load transcript from DB
                flask_session["scout_key"] = key
                flask_session["pseudonym"] = get_pseudonym(key)

                transcript = load_transcript(key)
                if transcript:
                    flask_session["resumed"] = True
                    last_assistant = next(
                        (m["content"] for m in reversed(transcript)
                         if m["role"] == "assistant"), ""
                    )
                    flask_session["last_topic"] = last_assistant[:120]
                else:
                    flask_session["resumed"] = False
                    flask_session["last_topic"] = ""

                # Restore portrait/constitution files if they exist on disk
                import glob
                portrait_matches = sorted(
                    glob.glob(os.path.join(SPINE_DIR, f"{key}_*_portrait.txt"))
                )
                if portrait_matches:
                    portrait_filename = os.path.basename(portrait_matches[-1])
                    flask_session["portrait_file"] = portrait_filename
                    fname_parts = portrait_filename.replace("_portrait.txt", "").split("_", 1)
                    if len(fname_parts) == 2:
                        flask_session["date"] = fname_parts[1]
                    flask_session["user_id"] = key

                constitution_matches = sorted(
                    glob.glob(os.path.join(SPINE_DIR, f"{key}_*_constitution.txt"))
                )
                if constitution_matches:
                    flask_session["constitution_file"] = os.path.basename(constitution_matches[-1])

                return {"success": True, "session_state": db_session["state"]}

            # Unused key — fresh session
            lines[i] = f"{k}:active"
            _write_keys(lines)
            flask_session["scout_key"] = key
            flask_session["pseudonym"] = "Anonymous"
            flask_session["resumed"] = False
            flask_session["last_topic"] = ""
            create_session(key)
            return {"success": True, "session_state": "interviewing"}

    return {"success": False, "reason": "invalid"}


@app.route("/burn", methods=["POST"])
def burn():
    """Burn the active key after delivery."""
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

    # Transition to delivered and clean up
    transition_state(key, "delivered")
    delete_transcript(key)
    cleanup_session(key)

    # Delete flat-file transcript backup
    transcript_path = os.path.join(TRANSCRIPT_DIR, f"{key}_transcript.json")
    try:
        os.remove(transcript_path)
    except FileNotFoundError:
        pass

    return {"success": True}


@app.route("/chat", methods=["POST"])
def chat():
    auth_err = _require_auth()
    if auth_err:
        return auth_err

    active_key = flask_session.get("scout_key", "")

    # Check session state — refuse if generating or delivered
    db_state = get_session_state(active_key)
    if db_state and db_state["state"] in ("generating", "delivered"):
        return {"error": "session ended"}, 403

    # Load transcript from database
    transcript_data = load_transcript(active_key)
    sess = Session()
    sess.transcript = transcript_data

    # Resume acknowledgement
    if flask_session.get("resumed"):
        last_topic = flask_session.get("last_topic", "where we left off")
        resume_note = (
            f"[SYSTEM: This session was resumed after a disconnection. "
            f"Before your next question, acknowledge the return warmly "
            f"in one sentence using this message adapted naturally to "
            f"your voice: 'Welcome back. To protect your work from "
            f"interruptions, your session was held temporarily — like "
            f"a document that saves itself while you write. The moment "
            f"your Meridian is delivered, it is deleted completely. Nothing "
            f"is kept. We were talking about: {last_topic}. "
            f"Shall we continue?' Then continue the interview normally.]"
        )
        sess.transcript.append({"role": "user", "content": resume_note})
        flask_session["resumed"] = False

    data = request.get_json()
    message = data.get("message", "").strip()

    if not message:
        return {"error": "empty message"}, 400

    # Resolve prompt and model
    if _is_test_key(active_key):
        from scout.test_prompt import TEST_PROMPT
        stream_kwargs = {"system_prompt": TEST_PROMPT, "model": TEST_MODEL}
    else:
        stream_kwargs = {}

    # First call: inject synthetic "Begin."
    if not is_started(active_key):
        mark_started(active_key)
        sess.add_user("Begin.")
        opening_chunks: list[str] = []

        def generate_opening():
            for chunk in send_message_stream(client, sess.transcript, **stream_kwargs):
                opening_chunks.append(chunk)
                yield f"data: {json.dumps({'text': chunk})}\n\n"
            full_opening = "".join(opening_chunks)
            sess.add_assistant(full_opening)
            save_transcript(active_key, sess.transcript)
            # Also save flat-file backup
            _save_transcript_backup(active_key, sess.transcript)
            yield f"data: {json.dumps({'done': True, 'session_state': 'interviewing'})}\n\n"

        return Response(generate_opening(), mimetype="text/event-stream")

    # Normal turn
    sess.add_user(message)

    # Pseudonym detection — during arrival phase (skip for test keys)
    exchange_count = len(sess.transcript) // 2
    if (not _is_test_key(active_key)
            and flask_session.get("pseudonym", "Anonymous") == "Anonymous"
            and 2 <= exchange_count <= 7
            and len(message) < 80):
        candidate = message.strip()
        for prefix in ["you can call me ", "i'd like to be called ", "just call me ",
                        "let's go with ", "how about ", "call me ", "my name is ",
                        "use ", "i'll be ", "i am ", "im ", "i'm "]:
            if candidate.lower().startswith(prefix):
                candidate = candidate[len(prefix):].strip()
                break
        decline_signals = ["anonymous", "i don't mind", "doesn't matter",
                          "no preference", "don't care", "anything", "whatever"]
        if not any(s in candidate.lower() for s in decline_signals) and candidate:
            detected_pseudonym = candidate.strip(' "\'.,')
            flask_session["pseudonym"] = detected_pseudonym
            set_pseudonym(active_key, detected_pseudonym)

    collected: list[str] = []

    def generate():
        for chunk in send_message_stream(client, sess.transcript, **stream_kwargs):
            collected.append(chunk)
            yield f"data: {json.dumps({'text': chunk})}\n\n"
        full_reply = "".join(collected)
        sess.add_assistant(full_reply)

        # Save transcript to database and flat-file backup
        save_transcript(active_key, sess.transcript)
        _save_transcript_backup(active_key, sess.transcript)

        # State transition detection
        current = get_session_state(active_key)
        current_state = current["state"] if current else "interviewing"

        if current_state == "interviewing":
            # Check for interview completion
            complete = (
                "Give me a moment" in full_reply
                and len(sess.transcript) >= 40
            )
            if _is_test_key(active_key) and not complete:
                complete = (
                    "```yaml" in full_reply
                    and "spine:" in full_reply
                )
            if complete:
                transition_state(active_key, "closing")
                current_state = "closing"

        if current_state == "closing":
            # Check for settling completion
            settling = "I'll start now" in full_reply and "give me a few minutes" in full_reply
            if settling:
                transition_state(active_key, "generating")
                current_state = "generating"
            # 90-second timeout handled by background scheduler

        yield f"data: {json.dumps({'done': True, 'session_state': current_state})}\n\n"

    return Response(generate(), mimetype="text/event-stream")


def _save_transcript_backup(key: str, transcript: list[dict]) -> None:
    """Save flat-file transcript backup alongside SQLite."""
    try:
        path = os.path.join(TRANSCRIPT_DIR, f"{key}_transcript.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(transcript, f, ensure_ascii=False, indent=2)
    except Exception as exc:
        logger.error("Failed to save transcript backup for %s: %s", key, exc)


@app.route("/generate", methods=["POST"])
def generate_spine():
    """Generate the spine.yaml, portrait, and constitution."""
    auth_err = _require_auth()
    if auth_err:
        return auth_err

    from datetime import datetime

    gen_key = flask_session.get("scout_key", "")

    # Check state — must be generating
    db_state = get_session_state(gen_key)
    if not db_state or db_state["state"] != "generating":
        return {"error": "not ready for generation"}, 403

    # Load transcript from database
    transcript = load_transcript(gen_key)
    if not transcript:
        return {"error": "no transcript found"}, 404

    gen_model = TEST_MODEL if _is_test_key(gen_key) else None
    yaml_doc = generate_yaml_sections(client, transcript, model=gen_model)
    pseudonym = flask_session.get("pseudonym", get_pseudonym(gen_key))
    portrait_text = generate_portrait(client, transcript, model=gen_model, pseudonym=pseudonym)

    # Save YAML
    date_str = datetime.now().strftime("%Y-%m-%d")
    yaml_path = os.path.join(SPINE_DIR, f"{gen_key}_{date_str}.yaml")
    with open(yaml_path, "w", encoding="utf-8") as f:
        f.write(yaml_doc)

    # Save portrait
    portrait_filename = f"{gen_key}_{date_str}_portrait.txt"
    portrait_path = os.path.join(SPINE_DIR, portrait_filename)
    with open(portrait_path, "w", encoding="utf-8") as f:
        clean_portrait = "\n".join(
            line for line in portrait_text.splitlines()
            if not line.startswith("#")
        ).strip()
        f.write(clean_portrait)

    # Generate and save constitution
    constitution_text = generate_constitution(
        client, transcript, yaml_doc,
        pseudonym=pseudonym, model=gen_model,
    )
    constitution_filename = f"{gen_key}_{date_str}_constitution.txt"
    constitution_path = os.path.join(SPINE_DIR, constitution_filename)
    with open(constitution_path, "w", encoding="utf-8") as f:
        f.write(constitution_text)

    # Store in flask session for download routes
    flask_session["portrait_file"] = portrait_filename
    flask_session["constitution_file"] = constitution_filename
    flask_session["pseudonym"] = pseudonym
    flask_session["date"] = date_str
    flask_session["user_id"] = gen_key

    return {"yaml": yaml_doc, "portrait_url": "/portrait"}


@app.route("/portrait")
def portrait():
    """Serve the portrait display page with text from disk."""
    portrait_filename = flask_session.get("portrait_file")
    if not portrait_filename:
        return render_template(
            "portrait.html",
            pseudonym="Anonymous", date="", user_id="", portrait_text="",
        )

    portrait_path = os.path.join(SPINE_DIR, portrait_filename)
    if not os.path.exists(portrait_path):
        return render_template(
            "portrait.html",
            pseudonym=flask_session.get("pseudonym", "Anonymous"),
            date=flask_session.get("date", ""),
            user_id=flask_session.get("user_id", ""),
            portrait_text="",
        )

    with open(portrait_path, "r", encoding="utf-8") as f:
        portrait_text = f.read()

    return render_template(
        "portrait.html",
        pseudonym=flask_session.get("pseudonym", "Anonymous"),
        date=flask_session.get("date", ""),
        user_id=flask_session.get("user_id", ""),
        portrait_text=portrait_text,
    )


@app.route("/download-portrait")
def download_portrait():
    """Generate PDF portrait and return as download."""
    import re
    from io import BytesIO

    portrait_filename = flask_session.get("portrait_file")
    if not portrait_filename:
        return {"error": "No portrait available."}, 404

    portrait_path = os.path.join(SPINE_DIR, portrait_filename)
    if not os.path.exists(portrait_path):
        return {"error": "Portrait file not found."}, 404

    with open(portrait_path, "r", encoding="utf-8") as f:
        raw_text = f.read()

    pseudonym = flask_session.get("pseudonym", "Anonymous")
    date_str = flask_session.get("date", "")

    portrait_html = _parse_portrait_markers(raw_text, pseudonym)

    html_string = render_template(
        "portrait_pdf.html",
        pseudonym=pseudonym,
        date=date_str,
        portrait_html=portrait_html,
    )

    from weasyprint import HTML
    pdf_buffer = BytesIO()
    HTML(string=html_string).write_pdf(pdf_buffer)
    pdf_buffer.seek(0)

    safe_name = re.sub(r"[^a-zA-Z0-9]", "_", pseudonym)
    filename = f"portrait_{safe_name}_{date_str}.pdf"

    return Response(
        pdf_buffer.read(),
        mimetype="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@app.route("/download-meridian")
def download_meridian():
    """Download the personal meridian as a text file."""
    import re

    constitution_filename = flask_session.get("constitution_file")
    if not constitution_filename:
        return {"error": "No constitution available."}, 404

    constitution_path = os.path.join(SPINE_DIR, constitution_filename)
    if not os.path.exists(constitution_path):
        return {"error": "Constitution file not found."}, 404

    with open(constitution_path, "r", encoding="utf-8") as f:
        constitution_text = f.read()

    pseudonym = flask_session.get("pseudonym", "Anonymous")
    date_str = flask_session.get("date", "")
    safe_name = re.sub(r"[^a-zA-Z0-9]", "_", pseudonym)
    filename = f"meridian_{safe_name}_{date_str}.txt"

    return Response(
        constitution_text,
        mimetype="text/plain; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def _parse_portrait_markers(raw_text: str, pseudonym: str) -> str:
    """Parse SHADOW/SURPRISE/EXTRACT markers and convert to HTML paragraphs."""
    import re

    # Strip any unrecognised [TAG]...[/TAG] markers, keeping content
    raw_text = re.sub(r"\[(?!SHADOW\]|/SHADOW\]|SURPRISE\]|/SURPRISE\]|EXTRACT\]|/EXTRACT\])([A-Z_]+)\]", "", raw_text)
    raw_text = re.sub(r"\[/(?!SHADOW\]|SURPRISE\]|EXTRACT\])([A-Z_]+)\]", "", raw_text)

    # Known markers and their types (EXTRACT treated as surprise)
    marker_defs = [
        ("[SHADOW]", "[/SHADOW]", "shadow"),
        ("[SURPRISE]", "[/SURPRISE]", "surprise"),
        ("[EXTRACT]", "[/EXTRACT]", "surprise"),
    ]

    blocks: list[dict] = []
    remaining = raw_text

    while remaining:
        # Find nearest known marker
        nearest = -1
        nearest_def = None

        for open_tag, close_tag, mtype in marker_defs:
            idx = remaining.find(open_tag)
            if idx != -1 and (nearest == -1 or idx < nearest):
                nearest = idx
                nearest_def = (open_tag, close_tag, mtype)

        if nearest == -1:
            if remaining.strip():
                blocks.append({"type": "normal", "text": remaining.strip()})
            break

        open_tag, close_tag, marker_type = nearest_def

        before = remaining[:nearest].strip()
        if before:
            blocks.append({"type": "normal", "text": before})

        after_open = remaining[nearest + len(open_tag):]
        close_idx = after_open.find(close_tag)
        if close_idx == -1:
            if after_open.strip():
                blocks.append({"type": "normal", "text": after_open.strip()})
            break

        marked = after_open[:close_idx].strip()
        if marked:
            blocks.append({"type": marker_type, "text": marked})

        remaining = after_open[close_idx + len(close_tag):]

    html_parts: list[str] = []
    for block in blocks:
        paragraphs = [p.strip() for p in block["text"].split("\n\n") if p.strip()]
        for para in paragraphs:
            safe = para.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            safe = safe.replace("\n", " ")

            if block["type"] == "shadow":
                html_parts.append(f'<div class="shadow-passage"><p>{safe}</p></div>')
            elif block["type"] == "surprise":
                html_parts.append(f'<div class="surprise-passage"><p>{safe}</p></div>')
            else:
                html_parts.append(f'<div class="para-wrap"><p>{safe}</p></div>')

    if html_parts:
        last = html_parts[-1]
        if pseudonym in last:
            last = last.replace(
                pseudonym,
                f'<span class="final-name">{pseudonym}</span>',
                1,
            )
            html_parts[-1] = last

    return "\n".join(html_parts)


@app.route("/test-generate", methods=["POST"])
def test_generate():
    """Dev-only route: run generation against a mock transcript."""
    mock_path = os.path.join(os.path.dirname(__file__), "tests", "mock_transcript.json")
    if not os.path.exists(mock_path):
        return {"error": "No mock transcript found."}, 404

    with open(mock_path, encoding="utf-8") as f:
        transcript = json.load(f)

    yaml_doc = generate_yaml_sections(client, transcript)
    portrait = generate_portrait(client, transcript)
    return {"yaml": yaml_doc, "portrait": portrait}


if __name__ == "__main__":
    app.run(debug=False, port=5000)
