"""Context window engine — full transcript on every API call."""

from __future__ import annotations

import datetime

import anthropic

from scout.prompt import SYSTEM_PROMPT

MODEL = "claude-sonnet-4-5"
OPUS_MODEL = "claude-opus-4-6"
TEST_MODEL = "claude-haiku-4-5-20251001"
MAX_TOKENS = 5000
TEMPERATURE = 1.0


def create_client() -> anthropic.Anthropic:
    """Create an Anthropic client. Reads ANTHROPIC_API_KEY from env."""
    return anthropic.Anthropic()


def send_message(
    client: anthropic.Anthropic,
    transcript: list[dict[str, str]],
) -> str:
    """Send the full transcript to Claude and return Scout's response.

    Every call includes the complete conversation history — no
    summarisation, no truncation. The system prompt is sent fresh
    each time.
    """
    response = client.messages.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        temperature=TEMPERATURE,
        system=[{"type": "text", "text": SYSTEM_PROMPT, "cache_control": {"type": "ephemeral"}}],
        messages=transcript,
    )
    # Extract text from the first content block
    return response.content[0].text


def generate_portrait(
    client: anthropic.Anthropic,
    transcript: list[dict[str, str]],
    model: str | None = None,
    pseudonym: str = "Anonymous",
) -> str:
    """Make a separate API call using the Chronicler prompt to write the portrait.

    Sends the full transcript as a single user message with the
    pseudonym explicitly stated. Returns the complete portrait prose.
    """
    from scout.chronicler import CHRONICLER_PROMPT

    # Flatten the transcript into a readable block — strip any YAML blocks
    lines: list[str] = []
    for turn in transcript:
        content = turn["content"]
        # Strip YAML blocks from assistant messages
        if turn["role"] == "assistant" and "```yaml" in content:
            import re
            content = re.sub(r"```yaml[\s\S]*?```", "", content).strip()
            if not content:
                continue
        role = "Scout" if turn["role"] == "assistant" else "Person"
        lines.append(f"{role}: {content}")
    transcript_text = "\n\n".join(lines)

    response = client.messages.create(
        model=model or OPUS_MODEL,
        max_tokens=16000,
        temperature=TEMPERATURE,
        system=CHRONICLER_PROMPT,
        messages=[
            {
                "role": "user",
                "content": (
                    f"The person's pseudonym for this session is: {pseudonym}. "
                    f"This is the exact name to use in the final sentence — "
                    f"do not invent or substitute any other name.\n\n"
                    f"Here is the complete Scout session transcript. "
                    f"Write the portrait.\n\n{transcript_text}"
                ),
            }
        ],
    )
    return response.content[0].text


def generate_constitution(
    client: anthropic.Anthropic,
    transcript: list[dict[str, str]],
    spine_yaml: str,
    pseudonym: str = "Anonymous",
    model: str | None = None,
) -> str:
    """Generate a personal constitution from the session transcript and spine.

    Uses Opus by default. Returns the constitution text.
    """
    from scout.constitution import CONSTITUTION_PROMPT

    lines: list[str] = []
    for turn in transcript:
        role = "Scout" if turn["role"] == "assistant" else "Person"
        lines.append(f"{role}: {turn['content']}")
    transcript_text = "\n\n".join(lines)

    response = client.messages.create(
        model=model or OPUS_MODEL,
        max_tokens=2000,
        temperature=TEMPERATURE,
        system=CONSTITUTION_PROMPT,
        messages=[
            {
                "role": "user",
                "content": (
                    f"The person's pseudonym is: {pseudonym}.\n\n"
                    f"SPINE YAML:\n{spine_yaml}\n\n"
                    f"FULL TRANSCRIPT:\n{transcript_text}"
                ),
            }
        ],
    )
    return response.content[0].text


def generate_yaml_sections(
    client: anthropic.Anthropic,
    transcript: list[dict[str, str]],
    model: str | None = None,
) -> str:
    """Run four sequential API calls to build the spine.yaml in sections.

    Each call receives the full transcript plus a directive to generate
    only specific sections. The four responses are assembled into one
    complete spine.yaml document.
    """
    section_directives = [
        (
            f"Generate only the meta, purpose, and hats sections of the "
            f"spine.yaml from this transcript. Use the exact schema "
            f"defined in your instructions. "
            f"Today's date is {datetime.date.today().isoformat()} — "
            f"use this as the session_date."
        ),
        (
            "Generate only the values and hard_limits sections of the "
            "spine.yaml from this transcript."
        ),
        (
            "Generate only the shadows, long_game, and relationships "
            "sections of the spine.yaml from this transcript."
        ),
        (
            "Generate only the north_instructions, intellectual_diet, "
            "and unresolved sections of the spine.yaml from this transcript."
        ),
    ]

    yaml_parts: list[str] = []
    for directive in section_directives:
        # Build messages: full transcript + the section directive
        messages = list(transcript) + [
            {"role": "user", "content": directive},
        ]
        response = client.messages.create(
            model=model or MODEL,
            max_tokens=4000,
            temperature=TEMPERATURE,
            system=[{"type": "text", "text": SYSTEM_PROMPT, "cache_control": {"type": "ephemeral"}}],
            messages=messages,
        )
        yaml_parts.append(response.content[0].text)

    # Stitch sections into a single valid spine.yaml
    assembled = _stitch_yaml_sections(yaml_parts)

    # Strip trailing prose — truncate at first non-YAML line
    import logging
    import yaml

    clean_lines: list[str] = []
    truncated_lines: list[str] = []
    hit_prose = False
    for line in assembled.splitlines():
        if hit_prose:
            truncated_lines.append(line)
            continue
        stripped = line.strip()
        # Empty lines and YAML content pass through
        if not stripped or stripped.startswith("-") or ":" in stripped or stripped.startswith("#"):
            clean_lines.append(line)
        # Indented continuation lines pass through
        elif line and line[0] == " ":
            clean_lines.append(line)
        else:
            # Prose detected — stop here
            hit_prose = True
            truncated_lines.append(line)
    assembled = "\n".join(clean_lines).rstrip() + "\n"

    if truncated_lines:
        logging.warning("YAML prose truncation — removed %d lines: %s",
                        len(truncated_lines), truncated_lines[:3])

    # Validate with PyYAML
    try:
        yaml.safe_load(assembled)
    except Exception as exc:
        logging.error("spine.yaml failed PyYAML validation after truncation: %s", exc)
        # Attempt recovery — extract from spine: to last parseable point
        try:
            recovery_lines: list[str] = []
            for line in assembled.splitlines():
                recovery_lines.append(line)
                test = "\n".join(recovery_lines) + "\n"
                try:
                    yaml.safe_load(test)
                except Exception:
                    recovery_lines.pop()
                    break
            if recovery_lines:
                assembled = "\n".join(recovery_lines).rstrip() + "\n"
                logging.warning("YAML recovery — truncated to %d valid lines", len(recovery_lines))
            else:
                logging.error("YAML recovery failed — no valid lines found. Saving raw output.")
        except Exception as recovery_exc:
            logging.error("YAML recovery exception: %s. Saving raw output.", recovery_exc)

    return assembled


def _stitch_yaml_sections(parts: list[str]) -> str:
    """Stitch YAML section responses into a single document under spine:."""
    import re

    cleaned: list[str] = []
    for part in parts:
        # Strip fenced code block markers
        text = re.sub(r"```(?:yaml)?\s*\n?", "", part.strip())
        text = re.sub(r"\n?```\s*", "", text)
        cleaned.append(text.strip())

    # Build the document: start with spine: root, then nest each section
    lines: list[str] = ["spine:"]
    for section in cleaned:
        for line in section.splitlines():
            # Strip duplicate spine: root keys
            stripped = line.strip()
            if stripped == "spine:" or stripped == "spine: {}":
                continue
            # If line is a root-level key (no leading whitespace),
            # indent it under spine:
            if line and not line[0].isspace():
                lines.append("  " + line)
            else:
                lines.append(line)
        lines.append("")  # blank line between sections

    return "\n".join(lines).rstrip() + "\n"


def send_message_stream(
    client: anthropic.Anthropic,
    transcript: list[dict[str, str]],
    system_prompt: str | None = None,
    model: str | None = None,
):
    """Stream the full transcript to Claude, yielding text chunks.

    Same as send_message but uses the streaming API. Yields
    strings as they arrive from the model.
    """
    with client.messages.stream(
        model=model or MODEL,
        max_tokens=MAX_TOKENS,
        temperature=TEMPERATURE,
        system=[{"type": "text", "text": system_prompt or SYSTEM_PROMPT, "cache_control": {"type": "ephemeral"}}],
        messages=transcript,
    ) as stream:
        for text in stream.text_stream:
            yield text
