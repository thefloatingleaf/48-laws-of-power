#!/usr/bin/env python3

from __future__ import annotations

import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_FILE = BASE_DIR / "daily_learning.txt"
STATE_FILE = BASE_DIR / "learning_state.json"


def main() -> None:
    if not OUTPUT_FILE.exists():
        raise SystemExit("daily_learning.txt was not generated")

    if not STATE_FILE.exists():
        raise SystemExit("learning_state.json was not generated")

    message = OUTPUT_FILE.read_text(encoding="utf-8")
    state = json.loads(STATE_FILE.read_text(encoding="utf-8"))
    current_law = state.get("current_law")
    shown_count = state.get("current_cycle_shown_count")

    if not current_law:
        raise SystemExit("current_law missing in learning_state.json")

    expected = f"Today's Learning from 48 Laws of Power:\n\n{current_law}\n"
    if message != expected:
        raise SystemExit("daily_learning.txt does not match learning_state.json")

    if shown_count not in (1, 2, 3):
        raise SystemExit("current_cycle_shown_count must be 1, 2, or 3")


if __name__ == "__main__":
    main()
