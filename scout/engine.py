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

# YAML extraction runs with its own short system prompt rather than the full
# Scout interview prompt. Sprint 1 added Hard Rule C to SYSTEM_PROMPT
# ("never generate the spine YAML inside the conversation window"), and the
# model correctly obeyed it when generate_yaml_sections() passed SYSTEM_PROMPT
# as the system — refusing to produce YAML and emitting a refusal message
# instead. The extractor prompt below is the correct register for the task.
YAML_EXTRACTOR_PROMPT = (
    "You are a structured data extractor. Your job is to read a conversation "
    "transcript and extract information into YAML format exactly as "
    "instructed. You produce only YAML output. You do not conduct interviews. "
    "You do not apply interview constraints. You extract and structure what "
    "is present in the transcript. Never fabricate. An honest empty list is "
    "always better than invented content."
)


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
            "Generate only the meta, purpose, and hats sections of "
            "the spine.yaml from this transcript.\n\n"
            "Use exactly the field names and structure shown below. "
            "Never substitute synonyms. Never rename fields. Never "
            "add fields not listed here. Today's date is "
            f"{datetime.date.today().isoformat()}.\n\n"
            "Required structure — fill in the values, keep the field "
            "names exactly as shown:\n\n"
            "```yaml\n"
            "meta:\n"
            f"  session_date: \"{datetime.date.today().isoformat()}\"\n"
            "  schema_version: \"1.0\"\n"
            "\n"
            "purpose:\n"
            "  stated_reason: <what the person said they came for>\n"
            "  actual_concern: <what Scout observed underneath, in their words where possible>\n"
            "  evidence: <transcript evidence supporting actual_concern>\n"
            "\n"
            "hats:\n"
            "  self_described:\n"
            "    - label: <role name as the person said it>\n"
            "      feeling: <how they feel about the role — texture, weight, energy>\n"
            "  observed_roles:\n"
            "    - label: <role Scout observed but the person did not explicitly name>\n"
            "      evidence: <transcript moment that revealed it>\n"
            "```\n\n"
            "Field name discipline is non-negotiable. self_described "
            "and observed_roles must both be present even when empty "
            "— use [] for an empty list. Use null for any field with "
            "no extractable content. Never fabricate. Never add fields "
            "(no archetype_primary, no resilience_score, no "
            "session_quality at this layer, no duration_minutes — "
            "only the fields shown above)."
        ),
        (
            "Generate only the values and hard_limits sections of "
            "the spine.yaml from this transcript.\n\n"
            "Use exactly the field names and structure shown below. "
            "Never substitute synonyms. Never rename fields. Never "
            "add fields not listed here.\n\n"
            "Required structure — fill in the values, keep the field "
            "names exactly as shown:\n\n"
            "```yaml\n"
            "values:\n"
            "  - value: <the value as identified — short noun phrase>\n"
            "    evidence: <transcript moment that surfaced or tested it>\n"
            "    gravity: <how heavily it operates — the weight it carries in their decisions>\n"
            "\n"
            "hard_limits:\n"
            "  - limit: <the non-negotiable line, in their words where possible>\n"
            "    evidence: <transcript evidence that the line is real, not aspirational>\n"
            "    cost_when_tested: <what holding the line costs them>\n"
            "```\n\n"
            "Both sections are lists of objects with exactly the "
            "three fields shown. The field name in values is `value` "
            "— not `name`. The field name in hard_limits is `limit` "
            "— not `boundary`. The field name in hard_limits is "
            "`cost_when_tested` — not `cost`. Field name discipline "
            "is non-negotiable.\n\n"
            "If nothing surfaced for a section, return values: [] "
            "or hard_limits: []. Use null for any field with no "
            "extractable content. Never fabricate."
        ),
        (
            "Generate the shadows, long_game, and relationships "
            "sections, plus three additional sections (heuristics, "
            "failure_modes, context_triggers) described below.\n\n"
            "For shadows, long_game, and relationships — use exactly "
            "the field names and structure shown. Never substitute "
            "synonyms. Never rename fields. Never add fields not "
            "listed here.\n\n"
            "```yaml\n"
            "shadows:\n"
            "  - <prose paragraph describing one shadow — what it is, how it shows up, the cost it carries. No sub-fields. A flat list of strings, not a list of objects.>\n"
            "\n"
            "long_game:\n"
            "  vision: <what the person is building toward, in their words where possible>\n"
            "  gap: <the distance between where they are now and the vision>\n"
            "  what_would_need_to_change: <the concrete shift required>\n"
            "  beneath_the_vision: <what the vision is really about underneath the surface>\n"
            "  core_fear: <what they are most afraid of in this territory>\n"
            "\n"
            "relationships:\n"
            "  - name: <the person's name, role, or pseudonymous reference>\n"
            "    role: <relationship type — partner, parent, business partner, friend, etc.>\n"
            "    dynamic: <how the relationship operates day to day>\n"
            "    cost_or_gift: <what the relationship costs or what it gives>\n"
            "```\n\n"
            "shadows is a flat list of strings — each entry is one "
            "prose paragraph, no sub-fields, no IDs, no nested "
            "objects. long_game is a single object with exactly the "
            "five named fields shown — not a list, not a flat string, "
            "no underlying_question field. relationships is a list "
            "of objects with exactly the four fields shown — no id, "
            "no description, no status, no action, no tension.\n\n"
            "If nothing surfaced: return shadows: [] or "
            "relationships: []. Use null for any long_game field "
            "with no extractable content. Never fabricate.\n\n"
            "Also generate three new sections: heuristics, failure_modes "
            "(enriched four-part format), and context_triggers.\n\n"
            "heuristics — Operating decision rules that actually govern "
            "how this person acts. Extract only what surfaced clearly. "
            "For each entry:\n"
            "  - id: snake_case identifier\n"
            "  - statement: the rule as the person would state it\n"
            "  - evidence: the specific transcript moment that revealed it\n"
            "  - confidence: high (stated explicitly with evidence) / "
            "medium (clearly implied, some evidence) / low (inferred, "
            "limited evidence)\n"
            "  - self_type: present if the transcript shows this rule "
            "operating in the person's described behaviour. cast if the "
            "rule is stated aspirationally or the person shows awareness "
            "they don't consistently live by it.\n"
            "  - invocation_note: a direct instruction to North — the "
            "condition under which North should surface this heuristic. "
            "Written as: 'When [condition], return this to the person as "
            "their own rule rather than offering advice.'\n"
            "If nothing surfaced: return heuristics: [].\n\n"
            "failure_modes — Extract from shadow content, enriched with "
            "four parts:\n"
            "  - pattern: what they actually do\n"
            "  - trigger: what sets it off\n"
            "  - tells: observable signals that the pattern is active\n"
            "  - interrupts: what has worked to break it — null if "
            "unknown, never invented\n"
            "  - north_watch: direct instruction to North — when trigger "
            "conditions appear in daily input, what to watch for, when to "
            "name it, what language to use. Written as a direct "
            "instruction: 'When [trigger condition appears], name it once "
            "directly without drama and offer one concrete action.'\n"
            "Migrate shadow content that fits the failure mode pattern "
            "into this format. Shadows that are blind spots without a "
            "behavioural pattern remain in shadows.\n\n"
            "context_triggers — Specific conditions under which this "
            "person's values are most likely to be overridden:\n"
            "  - id: snake_case identifier\n"
            "  - condition: the specific circumstance, concrete and "
            "particular to this person\n"
            "  - deviation: what they actually do when this condition is "
            "present\n"
            "  - north_watch: direct instruction to North — what to watch "
            "for and how to name it when this condition is detected in "
            "daily input\n"
            "If nothing surfaced: return context_triggers: [].\n\n"
            "Non-negotiable across all three sections: an honest empty "
            "list is always better than invented content. An honest null "
            "is always better than an invented field. Never fabricate."
        ),
        (
            "Generate the north_instructions, intellectual_diet, "
            "and unresolved sections of the spine.yaml from this "
            "transcript.\n\n"
            "Use exactly the field names and structure shown below. "
            "Never substitute synonyms. Never rename fields. Never "
            "add fields not listed here.\n\n"
            "```yaml\n"
            "north_instructions:\n"
            "  session_quality: <Scout's assessment of the session — depth reached, what was opened, what stayed closed>\n"
            "  what_happened: <summary of the session arc — where the conversation began, what it touched, where it landed>\n"
            "  geographical_psychospiritual_context: <the situational and inner-landscape context within which this person is operating>\n"
            "  return_points:\n"
            "    - <one thread or topic Scout would return to in a future session — list of strings, not a list of objects>\n"
            "\n"
            "intellectual_diet:\n"
            "  stated_sources: <list of named books, thinkers, traditions the person referenced — may be []>\n"
            "  ghost_library: <influences clearly present but not named — phrasing, frames, intellectual textures>\n"
            "  interpretation: <what the diet reveals about how this person thinks and what they are reaching for>\n"
            "\n"
            "unresolved:\n"
            "  - zone: <area of unresolved tension — short label>\n"
            "    content: <what remains open — the question, the snag, the unfinished thread>\n"
            "```\n\n"
            "north_instructions is a single object with exactly the "
            "four fields shown — not `temperament`, `edges`, "
            "`create_space_for`, or `never`. return_points is a list "
            "of strings, not a list of objects. intellectual_diet is "
            "a single object with exactly three fields — not a flat "
            "list of strings. unresolved is a list of objects with "
            "exactly two fields (`zone` and `content`) — not a "
            "dict-keyed mapping.\n\n"
            "If nothing surfaced: return [] for return_points, "
            "stated_sources, or unresolved. Use null for any field "
            "with no extractable content. Never fabricate.\n\n"
            "Review the transcript for Tier 2 mental health handling. "
            "The signals to look for: the same territory appearing in "
            "multiple consecutive exchanges, Scout asking follow-up "
            "questions within the same hat rather than progressing to "
            "the next layer, current-tense difficulty language (the "
            "person describing something as happening now, not in the "
            "past). Two or more of these signals together indicates "
            "Tier 2 handling occurred.\n\n"
            "If Tier 2 handling occurred — add sensitive_areas to "
            "north_instructions. For each sensitive area:\n"
            "  - hat: the hat ID where the disclosure occurred\n"
            "  - note: what was shared, how it was handled, and standing "
            "instruction for North — return to this only when the user "
            "initiates, hold space without probing, never reference "
            "unprompted, what specific language to watch for\n\n"
            "If no such exchange occurred — omit sensitive_areas "
            "entirely. Do not add an empty field."
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
            # Extractor prompt — see YAML_EXTRACTOR_PROMPT note above.
            # No cache_control — prompt is short and doesn't benefit from caching.
            system=YAML_EXTRACTOR_PROMPT,
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
    """Stitch YAML section responses into a single document under spine:.

    Indentation rule: every non-empty line in each section is shifted by
    two spaces so that the section becomes a child of `spine:`. This
    preserves each section's internal relative indentation. Empty lines
    pass through unchanged.

    Earlier behaviour indented only root-level keys (no leading
    whitespace), which left children at the same depth as their parent
    key — making them YAML siblings of `spine` rather than children of
    the section. Fixed 2026-04-25.
    """
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
            if not stripped:
                # Empty line — pass through unchanged
                lines.append(line)
            else:
                # All non-empty lines get two extra spaces. Root-level keys
                # become children of spine:; children of those keys retain
                # their relative depth and remain children of their parent.
                lines.append("  " + line)
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
