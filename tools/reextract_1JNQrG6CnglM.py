"""One-off script: re-extract spine for key 1JNQrG6CnglM.

Sprint 3 verification surfaced field-name drift in Calls 1 and 2 of
generate_yaml_sections(). After tightening the extraction prompts in
scout/engine.py, this script re-runs extraction against the existing
transcript and writes a corrected spine to spines/.

The script:
  1. Loads the transcript for key 1JNQrG6CnglM from the SQLite database.
  2. Runs generate_yaml_sections() with the production Sonnet model
     (engine.MODEL — never test/Haiku).
  3. Validates the resulting YAML with PyYAML.
  4. Validates field names against SCHEMA_CONTRACTS.md inline.
  5. On success, renames any existing 1JNQrG6CnglM_*.yaml to
     *.malformed.bak and writes the corrected spine.
  6. On failure, leaves all existing files untouched and writes the raw
     output to /tmp/ for inspection.

Usage on VPS:
    cd /home/scout
    source venv/bin/activate
    python3 tools/reextract_1JNQrG6CnglM.py

This is a one-off. Pope runs it manually. CC does not execute.
"""

from __future__ import annotations

import datetime
import logging
import os
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scout import database, engine

KEY = "1JNQrG6CnglM"
SPINE_DIR = Path(os.getenv("SPINE_DIR", "/home/scout/spines"))
RAW_DUMP_PATH = Path("/tmp/spine_raw.yaml")

EXPECTED_TOP_LEVEL = {
    "meta", "purpose", "hats", "values", "hard_limits",
    "shadows", "long_game", "relationships",
    "north_instructions", "intellectual_diet", "unresolved",
    "heuristics", "failure_modes", "context_triggers",
}

EXPECTED_OBJECT_FIELDS: dict[str, set[str]] = {
    "meta": {"session_date", "schema_version"},
    "purpose": {"stated_reason", "actual_concern", "evidence"},
    "hats": {"self_described", "observed_roles"},
    "long_game": {
        "vision", "gap", "what_would_need_to_change",
        "beneath_the_vision", "core_fear",
    },
    "north_instructions": {
        "session_quality", "what_happened",
        "geographical_psychospiritual_context", "return_points",
    },
    "intellectual_diet": {
        "stated_sources", "ghost_library", "interpretation",
    },
}

EXPECTED_LIST_ITEM_FIELDS: dict[str, set[str]] = {
    "values": {"value", "evidence", "gravity"},
    "hard_limits": {"limit", "evidence", "cost_when_tested"},
    "relationships": {"name", "role", "dynamic", "cost_or_gift"},
    "unresolved": {"zone", "content"},
    "heuristics": {
        "id", "statement", "evidence",
        "confidence", "self_type", "invocation_note",
    },
    "failure_modes": {
        "pattern", "trigger", "tells", "interrupts", "north_watch",
    },
    "context_triggers": {
        "id", "condition", "deviation", "north_watch",
    },
}

# sensitive_areas is conditional under north_instructions per
# DEC-SCOUT-016 — present only when Tier 2 mental health handling
# occurred. Treated as allowed-but-optional.
NORTH_INSTRUCTIONS_OPTIONAL = {"sensitive_areas"}


def validate_against_contract(spine: dict) -> tuple[bool, list[str]]:
    """Inline contract check against SCHEMA_CONTRACTS.md.

    Returns (ok, list of issues). The issues list is empty iff ok is True.
    Replaced by the permanent spine_validator.py in Step 3.
    """
    issues: list[str] = []

    if not isinstance(spine, dict) or "spine" not in spine:
        return False, ["Top-level `spine:` key missing or root is not a mapping"]

    body = spine["spine"]
    if not isinstance(body, dict):
        return False, ["spine: value is not a mapping"]

    actual_sections = set(body.keys())
    missing = EXPECTED_TOP_LEVEL - actual_sections
    extra = actual_sections - EXPECTED_TOP_LEVEL
    if missing:
        issues.append(f"Missing top-level sections: {sorted(missing)}")
    if extra:
        issues.append(f"Unexpected top-level sections: {sorted(extra)}")

    for section, expected in EXPECTED_OBJECT_FIELDS.items():
        section_body = body.get(section)
        if section_body is None:
            continue
        if not isinstance(section_body, dict):
            issues.append(
                f"{section}: expected a mapping, got "
                f"{type(section_body).__name__}"
            )
            continue
        actual_fields = set(section_body.keys())
        allowed = expected | (
            NORTH_INSTRUCTIONS_OPTIONAL if section == "north_instructions"
            else set()
        )
        missing_fields = expected - actual_fields
        extra_fields = actual_fields - allowed
        if missing_fields:
            issues.append(f"{section}: missing fields {sorted(missing_fields)}")
        if extra_fields:
            issues.append(f"{section}: unexpected fields {sorted(extra_fields)}")

    for section, expected_fields in EXPECTED_LIST_ITEM_FIELDS.items():
        items = body.get(section)
        if items is None:
            continue
        if not isinstance(items, list):
            issues.append(
                f"{section}: expected a list, got {type(items).__name__}"
            )
            continue
        for i, item in enumerate(items):
            if not isinstance(item, dict):
                issues.append(
                    f"{section}[{i}]: expected an object, got "
                    f"{type(item).__name__}"
                )
                continue
            actual_fields = set(item.keys())
            missing_fields = expected_fields - actual_fields
            extra_fields = actual_fields - expected_fields
            if missing_fields:
                issues.append(
                    f"{section}[{i}]: missing fields {sorted(missing_fields)}"
                )
            if extra_fields:
                issues.append(
                    f"{section}[{i}]: unexpected fields {sorted(extra_fields)}"
                )

    shadows = body.get("shadows")
    if shadows is not None:
        if not isinstance(shadows, list):
            issues.append(
                f"shadows: expected a list, got {type(shadows).__name__}"
            )
        else:
            for i, item in enumerate(shadows):
                if not isinstance(item, str):
                    issues.append(
                        f"shadows[{i}]: expected a string, got "
                        f"{type(item).__name__} (contract: flat list of "
                        f"strings, not list of objects)"
                    )

    return (not issues), issues


def print_section_summary(spine: dict) -> None:
    """Print one-line summary per section for human inspection."""
    body = spine.get("spine", {})
    print("\n--- Section summary ---")
    for section in sorted(body.keys()):
        section_body = body[section]
        if isinstance(section_body, list):
            print(f"  {section}: list of {len(section_body)} entries")
        elif isinstance(section_body, dict):
            print(
                f"  {section}: object with keys "
                f"{sorted(section_body.keys())}"
            )
        else:
            print(f"  {section}: {type(section_body).__name__}")
    print()


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )
    log = logging.getLogger("reextract")

    transcript = database.load_transcript(KEY)
    if not transcript:
        log.error("No transcript found for key %s", KEY)
        return 1

    log.info("Loaded transcript for %s — %d turns", KEY, len(transcript))

    client = engine.create_client()
    log.info(
        "Running generate_yaml_sections with model=%s (production Sonnet)",
        engine.MODEL,
    )

    spine_yaml = engine.generate_yaml_sections(
        client,
        transcript,
        model=engine.MODEL,
    )

    log.info("Extraction complete. %d chars produced.", len(spine_yaml))

    try:
        loaded = yaml.safe_load(spine_yaml)
    except yaml.YAMLError as exc:
        log.error("PyYAML validation failed: %s", exc)
        RAW_DUMP_PATH.write_text(spine_yaml, encoding="utf-8")
        log.error("Raw output written to %s. Spine NOT saved.", RAW_DUMP_PATH)
        return 2

    log.info("PyYAML validation: pass")

    ok, issues = validate_against_contract(loaded)
    if not ok:
        log.error("Contract validation failed (%d issues):", len(issues))
        for issue in issues:
            log.error("  - %s", issue)
        RAW_DUMP_PATH.write_text(spine_yaml, encoding="utf-8")
        log.error("Raw output written to %s. Spine NOT saved.", RAW_DUMP_PATH)
        print_section_summary(loaded)
        return 3

    log.info(
        "Contract validation: pass — all sections and fields match "
        "SCHEMA_CONTRACTS.md"
    )

    today = datetime.date.today().isoformat()
    out_path = SPINE_DIR / f"{KEY}_{today}.yaml"

    existing = sorted(SPINE_DIR.glob(f"{KEY}_*.yaml"))
    for old in existing:
        if old == out_path:
            continue
        backup = old.with_suffix(".yaml.malformed.bak")
        if backup.exists():
            log.warning("Backup already exists, skipping rename: %s", backup)
            continue
        old.rename(backup)
        log.info("Renamed prior spine: %s → %s", old.name, backup.name)

    if out_path.exists():
        backup = out_path.with_suffix(".yaml.malformed.bak")
        if not backup.exists():
            out_path.rename(backup)
            log.info("Renamed prior spine: %s → %s", out_path.name, backup.name)
        else:
            log.error(
                "Both %s and %s exist — refusing to overwrite. "
                "Move one aside before re-running.",
                out_path.name, backup.name,
            )
            return 4

    out_path.write_text(spine_yaml, encoding="utf-8")
    log.info("Saved corrected spine: %s", out_path)

    print_section_summary(loaded)

    log.info(
        "Re-extraction complete. Pope reviews the corrected spine before "
        "any further action."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
