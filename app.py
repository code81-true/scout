"""Flask web interface for Scout."""

from __future__ import annotations

import json

from dotenv import load_dotenv

load_dotenv()

from flask import Flask, render_template, request, Response, session as flask_session

from scout.engine import (
    create_client,
    generate_portrait,
    generate_yaml_sections,
    send_message_stream,
)
from scout.session import Session

app = Flask(__name__)
app.secret_key = "scout-session-key"

# Single active session — in-memory, server-side
client = create_client()
session = Session()
_started = False


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/chat", methods=["POST"])
def chat():
    global _started

    data = request.get_json()
    message = data.get("message", "").strip()

    if not message:
        return {"error": "empty message"}, 400

    # First call: inject the synthetic "Begin." to get Scout's opening
    if not _started:
        _started = True
        session.add_user("Begin.")
        opening_chunks: list[str] = []

        def generate_opening():
            for chunk in send_message_stream(client, session.transcript):
                opening_chunks.append(chunk)
                yield f"data: {json.dumps({'text': chunk})}\n\n"
            full_opening = "".join(opening_chunks)
            session.add_assistant(full_opening)
            yield f"data: {json.dumps({'done': True})}\n\n"

        return Response(generate_opening(), mimetype="text/event-stream")

    # Normal turn
    session.add_user(message)
    collected: list[str] = []

    def generate():
        for chunk in send_message_stream(client, session.transcript):
            collected.append(chunk)
            yield f"data: {json.dumps({'text': chunk})}\n\n"
        full_reply = "".join(collected)
        session.add_assistant(full_reply)
        complete = (
            "Give me a moment" in full_reply
            and len(session.transcript) >= 40
        )
        yield f"data: {json.dumps({'done': True, 'session_complete': complete})}\n\n"

    return Response(generate(), mimetype="text/event-stream")


@app.route("/generate", methods=["POST"])
def generate_spine():
    """Generate the spine.yaml and portrait after the interview ends."""
    import os
    from datetime import datetime

    yaml_doc = generate_yaml_sections(client, session.transcript)
    portrait = generate_portrait(client, session.transcript)

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
