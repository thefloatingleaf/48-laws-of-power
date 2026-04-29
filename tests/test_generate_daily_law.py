from __future__ import annotations

import json
import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch

import generate_daily_law as app


class DailyLawGenerationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.base_dir = Path(self.temp_dir.name)
        self.laws_file = self.base_dir / "laws.json"
        self.state_file = self.base_dir / "learning_state.json"
        self.output_file = self.base_dir / "daily_learning.txt"
        self.history_file = self.base_dir / "history.json"
        self.laws_file.write_text(json.dumps([f"Law {i}" for i in range(1, 49)]), encoding="utf-8")

        self.patches = [
            patch.object(app, "BASE_DIR", self.base_dir),
            patch.object(app, "LAWS_FILE", self.laws_file),
            patch.object(app, "STATE_FILE", self.state_file),
            patch.object(app, "OUTPUT_FILE", self.output_file),
            patch.object(app, "HISTORY_FILE", self.history_file),
        ]
        for item in self.patches:
            item.start()

    def tearDown(self) -> None:
        for item in reversed(self.patches):
            item.stop()
        self.temp_dir.cleanup()

    def write_history(self, entries: list[dict[str, object]]) -> None:
        self.history_file.write_text(json.dumps(entries), encoding="utf-8")

    def test_first_generation_creates_expected_message(self) -> None:
        with patch("generate_daily_law.random.choice", return_value="Law 7"):
            state = app.update_state_for_today(date(2026, 4, 29))

        self.assertEqual(state["current_law"], "Law 7")
        self.assertEqual(state["current_law_total_appearances"], 1)
        self.assertEqual(
            self.output_file.read_text(encoding="utf-8"),
            "Today's Learning from 48 Laws of Power:\n\nLaw 7\n",
        )
        history = json.loads(self.history_file.read_text(encoding="utf-8"))
        self.assertEqual(history[-1]["law"], "Law 7")
        self.assertEqual(history[-1]["law_total_appearances"], 1)

    def test_same_day_regeneration_is_idempotent(self) -> None:
        with patch("generate_daily_law.random.choice", return_value="Law 9"):
            first = app.update_state_for_today(date(2026, 4, 29))
        second = app.update_state_for_today(date(2026, 4, 29))

        self.assertEqual(first, second)
        history = json.loads(self.history_file.read_text(encoding="utf-8"))
        self.assertEqual(len(history), 1)

    def test_law_is_not_eligible_before_ten_other_laws_have_two_appearances(self) -> None:
        entries: list[dict[str, object]] = [{"date": "2026-04-01", "law": "Law 1", "law_total_appearances": 1}]
        for law_number in range(2, 11):
            entries.append({"date": f"2026-04-{law_number:02d}", "law": f"Law {law_number}", "law_total_appearances": 1})
            entries.append({"date": f"2026-05-{law_number:02d}", "law": f"Law {law_number}", "law_total_appearances": 2})
        self.write_history(entries)

        seen_available: list[str] = []

        def choose_first(available: list[str]) -> str:
            seen_available.extend(available)
            return available[0]

        with patch("generate_daily_law.random.choice", side_effect=choose_first):
            result = app.update_state_for_today(date(2026, 4, 29))

        self.assertNotIn("Law 1", seen_available)
        self.assertNotEqual(result["current_law"], "Law 1")

    def test_law_becomes_eligible_after_ten_other_laws_have_two_appearances(self) -> None:
        entries: list[dict[str, object]] = [{"date": "2026-04-01", "law": "Law 1", "law_total_appearances": 1}]
        for law_number in range(2, 12):
            entries.append({"date": f"2026-04-{law_number:02d}", "law": f"Law {law_number}", "law_total_appearances": 1})
            entries.append({"date": f"2026-05-{law_number:02d}", "law": f"Law {law_number}", "law_total_appearances": 2})
        self.write_history(entries)

        seen_available: list[str] = []

        def choose_law_one(available: list[str]) -> str:
            seen_available.extend(available)
            return "Law 1"

        with patch("generate_daily_law.random.choice", side_effect=choose_law_one):
            result = app.update_state_for_today(date(2026, 4, 29))

        self.assertIn("Law 1", seen_available)
        self.assertEqual(result["current_law"], "Law 1")
        self.assertEqual(result["current_law_total_appearances"], 2)

    def test_yesterdays_law_is_skipped_if_other_eligible_choices_exist(self) -> None:
        entries = [
            {"date": "2026-04-27", "law": "Law 3", "law_total_appearances": 1},
            {"date": "2026-04-28", "law": "Law 4", "law_total_appearances": 1},
        ]
        self.write_history(entries)

        seen_available: list[str] = []

        def choose_first(available: list[str]) -> str:
            seen_available.extend(available)
            return available[0]

        with patch("generate_daily_law.random.choice", side_effect=choose_first):
            result = app.update_state_for_today(date(2026, 4, 29))

        self.assertNotIn("Law 4", seen_available)
        self.assertNotEqual(result["current_law"], "Law 4")


if __name__ == "__main__":
    unittest.main()
