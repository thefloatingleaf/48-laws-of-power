#!/usr/bin/env python3

from __future__ import annotations

import json
import os
import random
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
LAWS_FILE = BASE_DIR / "laws.json"
STATE_FILE = BASE_DIR / "learning_state.json"
OUTPUT_FILE = BASE_DIR / "daily_learning.txt"
HISTORY_FILE = BASE_DIR / "history.json"
DATE_OVERRIDE_ENV = "LAWS48_NOW_DATE"
TOTAL_APPEARANCES_PER_LAW = 3
REPEAT_GAP_DAYS = 2
RECENT_COMPLETION_COOLDOWN = 8


@dataclass
class ActiveLaw:
    law: str
    shown_count: int
    next_due_date: str | None
    shown_dates: list[str]

    def to_dict(self) -> dict[str, object]:
        return {
            "law": self.law,
            "shown_count": self.shown_count,
            "next_due_date": self.next_due_date,
            "shown_dates": self.shown_dates,
        }


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
        return {"completed_laws": [], "active_laws": [], "recently_completed_laws": []}
    return json.loads(STATE_FILE.read_text(encoding="utf-8"))


def save_state(state: dict[str, object]) -> None:
    STATE_FILE.write_text(json.dumps(state, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def load_history() -> list[dict[str, object]]:
    if not HISTORY_FILE.exists():
        return []
    return json.loads(HISTORY_FILE.read_text(encoding="utf-8"))


def save_history(history: list[dict[str, object]]) -> None:
    HISTORY_FILE.write_text(json.dumps(history, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def choose_due_law(active_laws: list[ActiveLaw], today_iso: str) -> ActiveLaw | None:
    due = [law for law in active_laws if law.next_due_date == today_iso]
    if not due:
        return None
    due.sort(key=lambda item: item.shown_dates[0])
    return due[0]


def choose_new_law(laws: list[str], state: dict[str, object], active_laws: list[ActiveLaw]) -> ActiveLaw:
    completed = set(state.get("completed_laws", []))
    active_names = {item.law for item in active_laws}
    recent_completed = list(state.get("recently_completed_laws", []))
    recent_cooldown = {item["law"] for item in recent_completed[-RECENT_COMPLETION_COOLDOWN:]}
    available = [
        law
        for law in laws
        if law not in completed and law not in active_names and law not in recent_cooldown
    ]

    if not available:
        state["completed_laws"] = []
        completed = set()
        available = [law for law in laws if law not in active_names and law not in recent_cooldown]

    if not available:
        available = [law for law in laws if law not in active_names]

    if not available:
        raise RuntimeError("No laws available to schedule")

    selected_law = random.choice(available)
    return ActiveLaw(
        law=selected_law,
        shown_count=0,
        next_due_date=None,
        shown_dates=[],
    )


def bump_law(active_law: ActiveLaw, today: date) -> ActiveLaw:
    updated_dates = [*active_law.shown_dates, today.isoformat()]
    shown_count = active_law.shown_count + 1
    if shown_count < TOTAL_APPEARANCES_PER_LAW:
        next_due_date = (today + timedelta(days=REPEAT_GAP_DAYS)).isoformat()
    else:
        next_due_date = None
    return ActiveLaw(
        law=active_law.law,
        shown_count=shown_count,
        next_due_date=next_due_date,
        shown_dates=updated_dates,
    )


def render_message(law: str) -> str:
    return f"Today's Learning from 48 Laws of Power:\n\n{law}\n"


def update_state_for_today(today: date) -> dict[str, object]:
    laws = load_laws()
    state = load_state()
    history = load_history()
    today_iso = today.isoformat()

    if state.get("last_generated_date") == today_iso:
        return state

    active_laws = [ActiveLaw(**item) for item in state.get("active_laws", [])]
    selected = choose_due_law(active_laws, today_iso)
    selected_was_existing = selected is not None
    if selected is None:
        selected = choose_new_law(laws, state, active_laws)

    updated = bump_law(selected, today)
    next_active_laws: list[ActiveLaw] = []
    completed_laws = list(state.get("completed_laws", []))
    recently_completed_laws = list(state.get("recently_completed_laws", []))

    for item in active_laws:
        candidate = item
        if item.law == selected.law:
            candidate = updated
        if candidate.shown_count >= TOTAL_APPEARANCES_PER_LAW:
            if candidate.law not in completed_laws:
                completed_laws.append(candidate.law)
            recently_completed_laws.append(
                {
                    "law": candidate.law,
                    "completed_on": today_iso,
                }
            )
            continue
        next_active_laws.append(candidate)

    if not selected_was_existing:
        if updated.shown_count >= TOTAL_APPEARANCES_PER_LAW:
            if updated.law not in completed_laws:
                completed_laws.append(updated.law)
            recently_completed_laws.append(
                {
                    "law": updated.law,
                    "completed_on": today_iso,
                }
            )
        else:
            next_active_laws.append(updated)

    history.append(
        {
            "date": today_iso,
            "law": updated.law,
            "cycle_shown_count": updated.shown_count,
            "total_cycle_target": TOTAL_APPEARANCES_PER_LAW,
        }
    )

    result_state = {
        "last_generated_date": today_iso,
        "current_law": updated.law,
        "current_cycle_shown_count": updated.shown_count,
        "active_laws": [item.to_dict() for item in next_active_laws],
        "completed_laws": completed_laws,
        "recently_completed_laws": recently_completed_laws[-RECENT_COMPLETION_COOLDOWN:],
    }
    OUTPUT_FILE.write_text(render_message(updated.law), encoding="utf-8")
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
