"""Session state — in-memory transcript only."""

from __future__ import annotations


class Session:
    """Holds the conversation transcript for a single Scout interview."""

    def __init__(self) -> None:
        self.transcript: list[dict[str, str]] = []

    def add_user(self, text: str) -> None:
        """Record a user message."""
        self.transcript.append({"role": "user", "content": text})

    def add_assistant(self, text: str) -> None:
        """Record Scout's response."""
        self.transcript.append({"role": "assistant", "content": text})
