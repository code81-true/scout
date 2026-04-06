"""Entry point — python run_session.py"""

from __future__ import annotations

import sys

from scout.engine import create_client, send_message
from scout.session import Session


def main() -> None:
    client = create_client()
    session = Session()

    # Scout opens the conversation (no user message needed — first turn)
    opening = send_message(client, [{"role": "user", "content": "Begin."}])
    session.add_user("Begin.")
    session.add_assistant(opening)
    print(f"\nScout: {opening}\n")

    # Conversation loop
    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\nSession ended by user.")
            sys.exit(0)

        if not user_input:
            continue

        if user_input.lower() in ("quit", "exit"):
            print("\nSession ended.")
            break

        session.add_user(user_input)

        reply = send_message(client, session.transcript)
        session.add_assistant(reply)

        print(f"\nScout: {reply}\n")

        # If Scout produced the YAML, the interview is done
        if "```yaml" in reply and "spine:" in reply:
            print("--- Your spine.yaml has been delivered above. ---")
            break


if __name__ == "__main__":
    main()
