from __future__ import annotations

import unittest

from src.data_processing import MySqlRepository


class DataProcessingTests(unittest.TestCase):
    def test_completed_season_summary_shows_for_completed_current_year(self) -> None:
        self.assertTrue(
            MySqlRepository._should_show_completed_season_summary(
                export_year=2026,
                completed_season_year=2026,
                current_team_games={"Detroit Tigers": 162, "Toledo Mud Hens": 150},
            )
        )

    def test_completed_season_summary_persists_through_next_offseason(self) -> None:
        self.assertTrue(
            MySqlRepository._should_show_completed_season_summary(
                export_year=2027,
                completed_season_year=2026,
                current_team_games={"Detroit Tigers": 0, "Toledo Mud Hens": 0},
            )
        )

    def test_completed_season_summary_hides_once_new_season_starts(self) -> None:
        self.assertFalse(
            MySqlRepository._should_show_completed_season_summary(
                export_year=2027,
                completed_season_year=2026,
                current_team_games={"Detroit Tigers": 4, "Toledo Mud Hens": 3},
            )
        )


if __name__ == "__main__":
    unittest.main()
