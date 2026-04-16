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
    get_session_state,
    get_stale_closing_sessions,
    init_db,
    is_started,
    load_transcript,
    mark_started,
    save_transcript,
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
                flask_session["pseudonym"] = "Anonymous"

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
        lock_input = False

        if current_state == "interviewing":
            # Interview completion: "Give me a moment" + 40 messages
            complete = (
                "Give me a moment" in full_reply
                and len(sess.transcript) >= 40
            )
            if complete:
                transition_state(active_key, "closing")
                current_state = "closing"
                lock_input = True

        if current_state == "closing" or current_state == "interviewing":
            # Settling phrase detection — works for both production and test mode
            settling = "I'll start now" in full_reply and "give me a few minutes" in full_reply
            if settling:
                lock_input = True
                if current_state == "interviewing":
                    # Direct close — skip closing state, go straight to generating
                    transition_state(active_key, "closing")
                transition_state(active_key, "generating")
                current_state = "generating"

        # 90-second timeout handled by background scheduler

        done_payload = {"done": True, "session_state": current_state}
        if lock_input:
            done_payload["lock_input"] = True
        yield f"data: {json.dumps(done_payload)}\n\n"

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
    pseudonym = flask_session.get("pseudonym", "Anonymous")
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
    """Generate Meridian PDF with ReportLab and return as download."""
    import math
    import re
    from io import BytesIO

    from reportlab.lib.colors import Color
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.pdfgen import canvas
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont

    constitution_filename = flask_session.get("constitution_file")
    if not constitution_filename:
        return {"error": "No Meridian available."}, 404

    constitution_path = os.path.join(SPINE_DIR, constitution_filename)
    if not os.path.exists(constitution_path):
        return {"error": "Meridian file not found."}, 404

    with open(constitution_path, "r", encoding="utf-8") as f:
        constitution_text = f.read()

    pseudonym = flask_session.get("pseudonym", "Anonymous")
    date_str = flask_session.get("date", "")

    # Parse five paragraphs
    paragraphs = [p.strip() for p in constitution_text.split("\n\n") if p.strip()]
    # Strip any markdown headers from paragraphs
    paragraphs = [p for p in paragraphs if not p.startswith("#")]
    while len(paragraphs) < 5:
        paragraphs.append("")
    paragraphs = paragraphs[:5]

    section_titles = [
        "WHAT YOU ARE",
        "WHAT DRIVES YOU",
        "WHAT YOU CANNOT ESCAPE",
        "WHAT YOU EXPECT OF YOURSELF",
        "WHAT REMAINS OPEN",
    ]

    # Colours
    gold = Color(184 / 255, 150 / 255, 90 / 255)
    dark = Color(42 / 255, 31 / 255, 20 / 255)
    ivory = Color(253 / 255, 250 / 255, 245 / 255)
    muted = Color(154 / 255, 138 / 255, 122 / 255)

    W, H = A4
    margin = 18 * mm

    # Register Lora-Italic if available
    lora_available = False
    lora_path = "/usr/share/fonts/truetype/google-fonts/Lora-Italic-Variable.ttf"
    try:
        if os.path.exists(lora_path):
            pdfmetrics.registerFont(TTFont("Lora-Italic", lora_path))
            lora_available = True
    except Exception:
        pass
    preamble_font = "Lora-Italic" if lora_available else "Times-Italic"

    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)

    # Ivory background
    c.setFillColor(ivory)
    c.rect(0, 0, W, H, fill=1, stroke=0)

    # --- Globe watermark ---
    cx, cy = W / 2, H / 2
    R = 100 * mm

    def ortho(lat, lon, clat=20, clon=15):
        """Orthographic projection. Returns (x, y, visible)."""
        rlat = math.radians(lat)
        rlon = math.radians(lon)
        rclat = math.radians(clat)
        rclon = math.radians(clon)
        x = R * math.cos(rlat) * math.sin(rlon - rclon)
        y = R * (math.cos(rclat) * math.sin(rlat) - math.sin(rclat) * math.cos(rlat) * math.cos(rlon - rclon))
        vis = math.sin(rclat) * math.sin(rlat) + math.cos(rclat) * math.cos(rlat) * math.cos(rlon - rclon)
        return (cx + x, cy + y, vis > 0)

    c.saveState()

    # Outer circle
    c.setStrokeColor(Color(184 / 255, 150 / 255, 90 / 255, alpha=0.13))
    c.setLineWidth(0.5)
    c.circle(cx, cy, R, fill=0, stroke=1)

    # Meridian ellipses
    c.setLineWidth(0.3)
    for lon in range(-60, 181, 30):
        pts = []
        for lat in range(-90, 91, 3):
            x, y, v = ortho(lat, lon)
            if v:
                pts.append((x, y))
        if len(pts) > 1:
            p = c.beginPath()
            p.moveTo(pts[0][0], pts[0][1])
            for px, py in pts[1:]:
                p.lineTo(px, py)
            c.drawPath(p, fill=0, stroke=1)

    # Parallel ellipses
    for lat in range(-60, 61, 30):
        pts = []
        for lon in range(-180, 181, 3):
            x, y, v = ortho(lat, lon)
            if v:
                pts.append((x, y))
        if len(pts) > 1:
            p = c.beginPath()
            p.moveTo(pts[0][0], pts[0][1])
            for px, py in pts[1:]:
                p.lineTo(px, py)
            c.drawPath(p, fill=0, stroke=1)

    # Prime meridian (bold)
    c.setLineWidth(2.0)
    pts = []
    for lat in range(-90, 91, 2):
        x, y, v = ortho(lat, 0)
        if v:
            pts.append((x, y))
    if len(pts) > 1:
        p = c.beginPath()
        p.moveTo(pts[0][0], pts[0][1])
        for px, py in pts[1:]:
            p.lineTo(px, py)
        c.drawPath(p, fill=0, stroke=1)

    # Equator (bold)
    c.setLineWidth(1.2)
    pts = []
    for lon in range(-180, 181, 2):
        x, y, v = ortho(0, lon)
        if v:
            pts.append((x, y))
    if len(pts) > 1:
        p = c.beginPath()
        p.moveTo(pts[0][0], pts[0][1])
        for px, py in pts[1:]:
            p.lineTo(px, py)
        c.drawPath(p, fill=0, stroke=1)

    # Simplified continent polygons
    continent_fill = Color(184 / 255, 150 / 255, 90 / 255, alpha=0.06)
    c.setFillColor(continent_fill)
    c.setStrokeColor(Color(184 / 255, 150 / 255, 90 / 255, alpha=0.10))
    c.setLineWidth(0.3)

    continents = {
        "europe": [(36, -9), (36, 0), (38, 3), (43, 5), (46, 3), (48, 7), (54, 10), (55, 14), (57, 10), (60, 5), (63, 10), (70, 20), (71, 28), (68, 35), (60, 30), (55, 28), (50, 30), (47, 35), (42, 28), (38, 24), (36, 22), (35, 12), (36, -9)],
        "africa": [(35, -6), (37, 10), (33, 12), (30, 32), (20, 40), (10, 42), (0, 42), (-5, 38), (-10, 40), (-15, 35), (-25, 33), (-34, 25), (-34, 18), (-28, 15), (-15, 12), (-5, 10), (0, 1), (5, -5), (5, -15), (10, -15), (15, -17), (25, -13), (30, -10), (35, -6)],
        "north_america": [(30, -85), (25, -100), (30, -115), (35, -120), (40, -125), (48, -125), (55, -130), (60, -140), (65, -165), (70, -160), (72, -130), (70, -90), (65, -65), (55, -60), (48, -55), (45, -65), (42, -70), (35, -75), (30, -85)],
        "south_america": [(12, -72), (5, -77), (0, -80), (-5, -80), (-10, -78), (-15, -75), (-20, -70), (-25, -65), (-30, -60), (-35, -57), (-40, -62), (-45, -65), (-50, -68), (-55, -70), (-50, -75), (-40, -73), (-30, -52), (-25, -47), (-20, -40), (-10, -37), (-5, -35), (0, -50), (5, -60), (10, -65), (12, -72)],
        "greenland": [(60, -45), (65, -55), (70, -55), (75, -60), (80, -50), (83, -35), (80, -20), (75, -18), (70, -22), (65, -40), (60, -45)],
        "britain": [(50, -5), (52, 1), (55, -2), (58, -5), (58, -3), (56, -2), (53, 0), (51, 1), (50, -5)],
        "iceland": [(64, -24), (65, -18), (66, -14), (65, -14), (64, -18), (63, -22), (64, -24)],
        "madagascar": [(-12, 49), (-16, 50), (-20, 48), (-24, 47), (-25, 44), (-20, 44), (-16, 46), (-12, 49)],
        "scandinavia": [(56, 8), (58, 6), (60, 5), (63, 10), (66, 14), (69, 16), (70, 20), (71, 26), (70, 28), (68, 16), (64, 12), (60, 12), (58, 12), (56, 8)],
    }

    for name, coords in continents.items():
        visible_pts = []
        for lat, lon in coords:
            x, y, v = ortho(lat, lon)
            if v:
                visible_pts.append((x, y))
        if len(visible_pts) > 2:
            p = c.beginPath()
            p.moveTo(visible_pts[0][0], visible_pts[0][1])
            for px, py in visible_pts[1:]:
                p.lineTo(px, py)
            p.close()
            c.drawPath(p, fill=1, stroke=1)

    c.restoreState()

    # --- Top rule ---
    c.setStrokeColor(gold)
    c.setLineWidth(0.6)
    y_top = H - margin
    c.line(margin, y_top, W - margin, y_top)

    # --- Pseudonym ---
    c.setFillColor(gold)
    c.setFont("Times-BoldItalic", 38)
    y_pseudo = y_top - 18 * mm
    c.drawCentredString(W / 2, y_pseudo, pseudonym)

    # Thin gold rule under pseudonym
    c.setLineWidth(0.4)
    y_rule = y_pseudo - 4 * mm
    c.line(W / 2 - 20 * mm, y_rule, W / 2 + 20 * mm, y_rule)

    # --- Preamble at bottom ---
    preamble_y = margin + 25 * mm

    # "THIS IS MERIDIAN"
    c.setFillColor(gold)
    title_text = "THIS IS MERIDIAN"
    spaced = "  ".join(title_text)
    c.setFont("Helvetica-Bold", 6.5)
    c.drawCentredString(W / 2, preamble_y + 14 * mm, spaced)

    # Two preamble lines
    c.setFillColor(muted)
    c.setFont(preamble_font, 7.2)
    c.drawCentredString(W / 2, preamble_y + 8 * mm,
                        "This is not advice. It does not tell you what to think or how to live.")
    c.drawCentredString(W / 2, preamble_y + 3 * mm,
                        "It shows you what was visible in one serious, sincere hour with yourself.")

    # Colophon
    c.setStrokeColor(gold)
    c.setLineWidth(0.3)
    c.line(W / 2 - 11 * mm, preamble_y - 3 * mm, W / 2 + 11 * mm, preamble_y - 3 * mm)
    c.setFillColor(muted)
    c.setFont("Helvetica", 5.5)
    c.drawCentredString(W / 2, preamble_y - 8 * mm,
                        f"This Meridian was written for you alone. \u00b7 Scout \u00b7 {date_str}")

    # --- Sections ---
    content_top = y_rule - 8 * mm
    content_bottom = preamble_y + 22 * mm
    available = content_top - content_bottom
    section_height = available / 5

    def draw_spaced_text(c, x, y, text, font, size, spacing_mm):
        """Draw text with manual letter-spacing."""
        c.setFont(font, size)
        total_w = sum(c.stringWidth(ch, font, size) + spacing_mm for ch in text) - spacing_mm
        cx = x - total_w / 2
        for ch in text:
            c.drawString(cx, y, ch)
            cx += c.stringWidth(ch, font, size) + spacing_mm

    for i, (title, body) in enumerate(zip(section_titles, paragraphs)):
        sec_y = content_top - i * section_height

        # Title
        c.setFillColor(gold)
        draw_spaced_text(c, W / 2, sec_y, title, "Helvetica-Bold", 7.5, 0.8 * mm)

        # Body — wrap text
        if body:
            c.setFillColor(dark)
            c.setFont("Times-Roman", 9.5)
            text_width = W - 2 * margin - 10 * mm
            leading = 5 * mm
            ty = sec_y - 6 * mm

            # Simple word-wrap
            words = body.split()
            line = ""
            for word in words:
                test = f"{line} {word}".strip()
                if c.stringWidth(test, "Times-Roman", 9.5) < text_width:
                    line = test
                else:
                    if line:
                        # Check if this is the final section's last line with pseudonym
                        c.drawCentredString(W / 2, ty, line)
                        ty -= leading
                    line = word
            # Last line
            if line:
                # Final section — check for pseudonym in last line
                if i == 4 and pseudonym in line:
                    # Split at pseudonym
                    before = line[:line.rfind(pseudonym)]
                    c.setFont("Times-Roman", 9.5)
                    c.setFillColor(dark)
                    bw = c.stringWidth(before, "Times-Roman", 9.5)
                    pw = c.stringWidth(pseudonym, "Times-BoldItalic", 10.5)
                    total = bw + pw
                    start_x = W / 2 - total / 2
                    c.drawString(start_x, ty, before)
                    c.setFont("Times-BoldItalic", 10.5)
                    c.setFillColor(gold)
                    c.drawString(start_x + bw, ty, pseudonym)
                else:
                    c.drawCentredString(W / 2, ty, line)

    c.save()
    buf.seek(0)

    safe_name = re.sub(r"[^a-zA-Z0-9]", "_", pseudonym)
    filename = f"meridian_{safe_name}_{date_str}.pdf"

    return Response(
        buf.read(),
        mimetype="application/pdf",
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
