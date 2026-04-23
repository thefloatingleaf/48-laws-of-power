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

    def test_first_generation_creates_expected_message(self) -> None:
        with patch("generate_daily_law.random.choice", return_value="Law 7"):
            state = app.update_state_for_today(date(2026, 4, 23))

        self.assertEqual(state["current_law"], "Law 7")
        self.assertEqual(state["current_cycle_shown_count"], 1)
        self.assertEqual(
            self.output_file.read_text(encoding="utf-8"),
            "Today's Learning from 48 Laws of Power:\n\nLaw 7\n",
        )
        history = json.loads(self.history_file.read_text(encoding="utf-8"))
        self.assertEqual(history[-1]["law"], "Law 7")
        self.assertEqual(history[-1]["cycle_shown_count"], 1)

    def test_law_repeats_on_alternate_days_exactly_three_times(self) -> None:
        with patch("generate_daily_law.random.choice", side_effect=["Law 1", "Law 2"]):
            app.update_state_for_today(date(2026, 4, 23))
            app.update_state_for_today(date(2026, 4, 24))
            third_day_state = app.update_state_for_today(date(2026, 4, 25))
            fourth_day_state = app.update_state_for_today(date(2026, 4, 26))
            fifth_day_state = app.update_state_for_today(date(2026, 4, 27))

        self.assertEqual(third_day_state["current_law"], "Law 1")
        self.assertEqual(third_day_state["current_cycle_shown_count"], 2)
        self.assertEqual(fourth_day_state["current_law"], "Law 2")
        self.assertEqual(fourth_day_state["current_cycle_shown_count"], 2)
        self.assertEqual(fifth_day_state["current_law"], "Law 1")
        self.assertEqual(fifth_day_state["current_cycle_shown_count"], 3)

        stored = json.loads(self.state_file.read_text(encoding="utf-8"))
        self.assertIn("Law 1", stored["completed_laws"])
        self.assertNotIn("Law 1", [item["law"] for item in stored["active_laws"]])
        self.assertEqual(stored["recently_completed_laws"][-1]["law"], "Law 1")

    def test_same_day_regeneration_is_idempotent(self) -> None:
        with patch("generate_daily_law.random.choice", return_value="Law 9"):
            first = app.update_state_for_today(date(2026, 4, 23))
        second = app.update_state_for_today(date(2026, 4, 23))

        self.assertEqual(first, second)
        self.assertEqual(
            self.output_file.read_text(encoding="utf-8"),
            "Today's Learning from 48 Laws of Power:\n\nLaw 9\n",
        )
        history = json.loads(self.history_file.read_text(encoding="utf-8"))
        self.assertEqual(len(history), 1)

    def test_recently_completed_law_respects_cooldown_after_reset(self) -> None:
        state = {
            "last_generated_date": "2026-04-29",
            "current_law": "Law 9",
            "current_cycle_shown_count": 1,
            "active_laws": [],
            "completed_laws": [f"Law {i}" for i in range(1, 49)],
            "recently_completed_laws": [
                {"law": f"Law {i}", "completed_on": f"2026-04-{i:02d}"}
                for i in range(41, 49)
            ],
        }
        self.state_file.write_text(json.dumps(state), encoding="utf-8")
        self.history_file.write_text("[]", encoding="utf-8")

        with patch("generate_daily_law.random.choice", side_effect=lambda available: available[0]):
            result = app.update_state_for_today(date(2026, 4, 30))

        self.assertEqual(result["current_law"], "Law 1")
        self.assertNotIn(result["current_law"], [item["law"] for item in result["recently_completed_laws"]])
        self.assertNotIn("Law 41", result["current_law"])


if __name__ == "__main__":
    unittest.main()
