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
            active_page="toledo_mud_hens_team",
        )

        self.assertIn("Detroit Team", html)
        self.assertIn("dashboard.html", html)
        self.assertIn("detroit_tigers_team.html", html)
        self.assertIn("toledo_mud_hens_team.html", html)
        self.assertIn("scoring_info.html", html)
        self.assertIn('class="is-active" href="toledo_mud_hens_team.html"', html)
        self.assertIn("OOTP Date: Unknown", html)
        self.assertIn("const tables = document.querySelectorAll('table.data-table')", html)
        self.assertIn("applyColumnMode", html)


if __name__ == "__main__":
    unittest.main()
