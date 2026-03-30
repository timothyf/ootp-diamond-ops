from __future__ import annotations

import unittest

import pandas as pd

from src.dashboard_html import build_html_shell, html_table


class DashboardHtmlTests(unittest.TestCase):
    def test_html_table_empty_and_flags(self) -> None:
        empty = html_table(pd.DataFrame())
        self.assertIn("No rows", empty)

        df = pd.DataFrame(
            [
                {
                    "primary_position": "C",
                    "rank": 1,
                    "player_name": "Starter",
                }
            ]
        )
        rendered = html_table(
            df,
            sortable=False,
            highlight_starters=True,
            column_modes={"current": ["rank"]},
            column_labels={"primary_position": "pos", "rank": "rank"},
            default_mode="current",
        )

        self.assertIn('data-sortable="false"', rendered)
        self.assertIn('data-highlight-starters="true"', rendered)
        self.assertIn(">pos</th>", rendered)
        self.assertIn('data-default-mode="current"', rendered)
        self.assertIn("table-toggle-group", rendered)

    def test_build_html_shell_includes_nav_date_and_active_page(self) -> None:
        html = build_html_shell(
            title="Detroit Team",
            body="<section>Body</section>",
            mlb_team_name="Detroit Tigers",
            aaa_team_name="Toledo Mud Hens",
            ootp_export_date=None,
            team_header_summaries={
                "mlb": {"team_name": "Detroit Tigers", "wins": 8, "losses": 4, "position": 1, "gb": 0},
                "aaa": {"team_name": "Toledo Mud Hens", "wins": 6, "losses": 5, "position": 2, "gb": 1.5},
            },
            active_page="toledo_mud_hens_team",
        )

        self.assertIn("Detroit Team", html)
        self.assertIn("dashboard.html", html)
        self.assertIn("detroit_tigers_team.html", html)
        self.assertIn("toledo_mud_hens_team.html", html)
        self.assertIn("team_needs.html", html)
        self.assertIn("scoring_info.html", html)
        self.assertIn('class="is-active" href="toledo_mud_hens_team.html"', html)
        self.assertIn("OOTP Date: Unknown", html)
        self.assertIn("../src/images/diamondops-logo.png", html)
        self.assertIn('alt="DiamondOps logo"', html)
        self.assertIn("Detroit Tigers", html)
        self.assertIn("8-4", html)
        self.assertIn("1st", html)
        self.assertIn("GB 0", html)
        self.assertIn("Toledo Mud Hens", html)
        self.assertIn("6-5", html)
        self.assertIn("2nd", html)
        self.assertIn("GB 1.5", html)
        self.assertIn("const tables = document.querySelectorAll('table.data-table')", html)
        self.assertIn("applyColumnMode", html)

    def test_build_html_shell_handles_missing_team_summaries(self) -> None:
        html = build_html_shell(
            title="Detroit Team",
            body="<section>Body</section>",
            mlb_team_name="Detroit Tigers",
            aaa_team_name="Toledo Mud Hens",
            ootp_export_date="2026-04-01",
            team_header_summaries={"mlb": None, "aaa": None},
        )

        self.assertIn("Record unavailable", html)
        self.assertIn("Position unavailable", html)
        self.assertIn("GB unavailable", html)


if __name__ == "__main__":
    unittest.main()
