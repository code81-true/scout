"""Context window engine — full transcript on every API call."""

from __future__ import annotations

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
        system=SYSTEM_PROMPT,
        messages=transcript,
    )
    # Extract text from the first content block
    return response.content[0].text


def generate_portrait(
    client: anthropic.Anthropic,
    transcript: list[dict[str, str]],
    model: str | None = None,
) -> str:
    """Make a separate API call using the Chronicler prompt to write the portrait.

    Sends the full transcript as a single user message. Returns the
    complete portrait prose.
    """
    from scout.chronicler import CHRONICLER_PROMPT

    # Flatten the transcript into a readable block
    lines: list[str] = []
    for turn in transcript:
        role = "Scout" if turn["role"] == "assistant" else "Person"
        lines.append(f"{role}: {turn['content']}")
    transcript_text = "\n\n".join(lines)

    response = client.messages.create(
        model=model or OPUS_MODEL,
        max_tokens=10000,
        temperature=TEMPERATURE,
        system=CHRONICLER_PROMPT,
        messages=[
            {
                "role": "user",
                "content": (
                    "Here is the complete Scout session transcript. "
                    "Write the portrait.\n\n" + transcript_text
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
            "Generate only the meta, purpose, and hats sections of the "
            "spine.yaml from this transcript. Use the exact schema "
            "defined in your instructions."
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
            system=SYSTEM_PROMPT,
            messages=messages,
        )
        yaml_parts.append(response.content[0].text)

    # Stitch sections into a single valid spine.yaml
    assembled = _stitch_yaml_sections(yaml_parts)

    # Validate with PyYAML — return raw if parsing fails
    import logging
    try:
        import yaml
        yaml.safe_load(assembled)
    except Exception as exc:
        logging.error("spine.yaml failed PyYAML validation: %s", exc)

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
        system=system_prompt or SYSTEM_PROMPT,
        messages=transcript,
    ) as stream:
        for text in stream.text_stream:
            yield text
