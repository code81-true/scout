"""Generate single-use Scout access keys and append to keys.txt."""

from __future__ import annotations

import os
import random
import string
import sys

# New format: 12-char mixed case alphanumeric (A-Z, a-z, 0-9)
ALPHABET = string.ascii_letters + string.digits
KEY_LENGTH = 12

# Test keys still use uppercase-only for visual distinction
TEST_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"


def generate_key() -> str:
    """Generate a single 12-character mixed-case key."""
    return "".join(random.choices(ALPHABET, k=KEY_LENGTH))


def generate_test_key() -> str:
    """Generate a test key: TEST- followed by 6 uppercase characters."""
    return "TEST-" + "".join(random.choices(TEST_ALPHABET, k=6))


def main() -> None:
    test_mode = "--test" in sys.argv
    args = [a for a in sys.argv[1:] if a != "--test"]
    n = int(args[0]) if args else 1
    keys_path = os.path.join(os.path.dirname(__file__), "access", "keys.txt")

    new_keys: list[str] = []
    for _ in range(n):
        key = generate_test_key() if test_mode else generate_key()
        new_keys.append(f"{key}:unused")

    with open(keys_path, "a", encoding="utf-8") as f:
        for entry in new_keys:
            f.write(entry + "\n")

    for entry in new_keys:
        key = entry.split(":")[0]
        print(key)

    label = "test key" if test_mode else "key"
    print(f"\n{n} {label}(s) appended to {keys_path}")


if __name__ == "__main__":
    main()
