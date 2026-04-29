#!/usr/bin/env python3

from __future__ import annotations

import json
import os
import random
from collections import Counter
from datetime import date
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
LAWS_FILE = BASE_DIR / "laws.json"
STATE_FILE = BASE_DIR / "learning_state.json"
OUTPUT_FILE = BASE_DIR / "daily_learning.txt"
HISTORY_FILE = BASE_DIR / "history.json"
DATE_OVERRIDE_ENV = "LAWS48_NOW_DATE"
MIN_DOUBLE_SHOWN_OTHERS_BEFORE_REPEAT = 10


def resolve_today() -> date:
    override = os.environ.get(DATE_OVERRIDE_ENV)
    if override:
        return date.fromisoformat(override)
    return date.today()


def load_laws() -> list[str]:
    laws = json.loads(LAWS_FILE.read_text(encoding="utf-8"))
    if len(laws) != 48:
        raise ValueError(f"Expected 48 laws, found {len(laws)}")
    return laws


def load_state() -> dict[str, object]:
    if not STATE_FILE.exists():
        return {}
    return json.loads(STATE_FILE.read_text(encoding="utf-8"))


def save_state(state: dict[str, object]) -> None:
    STATE_FILE.write_text(json.dumps(state, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def load_history() -> list[dict[str, object]]:
    if not HISTORY_FILE.exists():
        return []
    raw_history = json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
    normalized_history: list[dict[str, object]] = []
    appearance_counts: Counter[str] = Counter()

    for entry in raw_history:
        law = str(entry["law"])
        appearance_counts[law] += 1
        normalized_history.append(
            {
                "date": entry["date"],
                "law": law,
                "law_total_appearances": entry.get("law_total_appearances", appearance_counts[law]),
            }
        )

    return normalized_history


def save_history(history: list[dict[str, object]]) -> None:
    HISTORY_FILE.write_text(json.dumps(history, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def build_appearance_counts(history: list[dict[str, object]]) -> Counter[str]:
    return Counter(entry["law"] for entry in history)


def can_repeat_law(law: str, appearance_counts: Counter[str]) -> bool:
    qualifying_other_laws = sum(
        1 for other_law, count in appearance_counts.items() if other_law != law and count >= 2
    )
    return qualifying_other_laws >= MIN_DOUBLE_SHOWN_OTHERS_BEFORE_REPEAT


def choose_random_law(laws: list[str], history: list[dict[str, object]], previous_law: str | None) -> str:
    appearance_counts = build_appearance_counts(history)
    available = [
        law
        for law in laws
        if appearance_counts[law] == 0 or can_repeat_law(law, appearance_counts)
    ]

    if previous_law and len(available) > 1 and previous_law in available:
        available = [law for law in available if law != previous_law]

    if not available:
        raise RuntimeError("No eligible laws available to schedule")

    return random.choice(available)


def render_message(law: str) -> str:
    return f"Today's Learning from 48 Laws of Power:\n\n{law}\n"


def update_state_for_today(today: date) -> dict[str, object]:
    laws = load_laws()
    state = load_state()
    history = load_history()
    save_history(history)
    today_iso = today.isoformat()

    if state.get("last_generated_date") == today_iso:
        return state

    previous_law = history[-1]["law"] if history else None
    selected_law = choose_random_law(laws, history, previous_law)
    appearance_counts = build_appearance_counts(history)
    total_appearances = appearance_counts[selected_law] + 1

    history.append(
        {
            "date": today_iso,
            "law": selected_law,
            "law_total_appearances": total_appearances,
        }
    )

    result_state = {
        "last_generated_date": today_iso,
        "current_law": selected_law,
        "current_law_total_appearances": total_appearances,
        "repeat_rule": (
            "No law becomes eligible again until ten other distinct laws "
            "have each been shown at least twice."
        ),
    }
    OUTPUT_FILE.write_text(render_message(selected_law), encoding="utf-8")
    save_history(history)
    save_state(result_state)
    return result_state


def main() -> None:
    today = resolve_today()
    state = update_state_for_today(today)
    if not OUTPUT_FILE.exists():
        OUTPUT_FILE.write_text(render_message(str(state["current_law"])), encoding="utf-8")


if __name__ == "__main__":
    main()
