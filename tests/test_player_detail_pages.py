from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.player_detail_pages import PlayerDetailPageWriter


class PlayerDetailPageWriterTests(unittest.TestCase):
    def test_component_rows_formats_scores_and_includes_weight(self) -> None:
        row = pd.Series(
            {
                "overall_hitter_score": 9.2345,
                "contact_now": 55.6789,
                "missing": None,
            }
        )
        fields = [
            ("Overall Score", "overall_hitter_score", "computed"),
            ("Contact", "contact_now", "input"),
            ("Missing", "missing", "ignored"),
            ("No Column", "does_not_exist", "ignored"),
        ]

        result = PlayerDetailPageWriter.component_rows(row, fields, include_weight=True)

        self.assertEqual(result["component"].tolist(), ["Overall Score", "Contact"])
        self.assertEqual(result["value"].tolist(), ["9.23", 55.6789])
        self.assertEqual(result["weight"].tolist(), ["computed", "input"])

    def test_write_player_detail_pages_writes_file_and_returns_links(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            out_dir = Path(temp_dir)

            writer = PlayerDetailPageWriter(
                out_dir=out_dir,
                html_table=lambda df: f"<table rows='{len(df)}'></table>",
                html_shell=lambda title, body: f"<html><title>{title}</title>{body}</html>",
                player_detail_filename=lambda group, name: f"{group}_{name.lower().replace(' ', '_')}.html",
                normalize_key=lambda series: series.str.lower().str.strip(),
            )

            frame = pd.DataFrame(
                [
                    {
                        "player_name": "Alice <Slugger>",
                        "primary_position": "1B",
                        "age_val": 24,
                        "bats": "L",
                        "throws": "R",
                        "injury_text": "Healthy",
                        "overall_hitter_score": 9.5,
                        "projection_hitter_score": 8.8,
                        "offense_score": 9.1,
                        "offense_score_regressed": 8.7,
                        "ratings_hitter_now": 60,
                        "ratings_hitter_future": 62,
                        "discipline_component": 0.45,
                        "platoon_skill_component": 0.2,
                        "defensive_component": 0.1,
                        "running_component": 0.0,
                        "scarcity_bonus": 0.2,
                        "age_bonus": 0.3,
                        "select_score_rhp": 7.5,
                        "select_score_lhp": 7.1,
                        "pa_val": 120,
                        "ops_val": 0.92,
                        "obp_val": 0.39,
                        "slg_val": 0.53,
                        "bbpct_val": 0.12,
                        "kpct_val": 0.16,
                        "platoon_skill_rhp": 9.0,
                        "platoon_skill_lhp": 1.0,
                        "hitting_reliability": 0.8,
                    }
                ]
            )

            links = writer.write_player_detail_pages({"mlb_hitters": frame})

            expected_filename = "mlb_hitters_alice_<slugger>.html"
            detail_file = out_dir / expected_filename
            self.assertTrue(detail_file.exists())
            self.assertEqual(links["mlb_hitters"], {"alice <slugger>": expected_filename})

            html = detail_file.read_text(encoding="utf-8")
            self.assertIn("Alice &lt;Slugger&gt; - Score Components", html)
            self.assertIn("Score Summary", html)
            self.assertIn("<table rows='", html)


if __name__ == "__main__":
    unittest.main()