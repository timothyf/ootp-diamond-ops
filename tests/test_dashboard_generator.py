from __future__ import annotations

import unittest
from unittest.mock import patch

from src.dashboard import DashboardGenerator


class _RepoWithPrefixes:
    mlb_file_prefix = "detroit"
    aaa_file_prefix = "toledo"
    mlb_team_name = "Detroit Tigers"
    aaa_team_name = "Toledo Mud Hens"

    @staticmethod
    def get_export_date() -> str | None:
        return None


class _RepoWithoutPrefixes:
    @staticmethod
    def get_export_date() -> str | None:
        return None


class DashboardGeneratorInitTests(unittest.TestCase):
    def test_db_mode_prefixes_skip_csv_discovery(self) -> None:
        with patch.object(
            DashboardGenerator,
            "_discover_team_file_prefixes",
            side_effect=AssertionError("CSV discovery should not run when repository provides team prefixes"),
        ):
            generator = DashboardGenerator(
                data_dir="src/data",
                out_dir="output",
                repository=_RepoWithPrefixes(),
            )

        self.assertEqual(generator.mlb_batting_filename, "detroit_batting.csv")
        self.assertEqual(generator.aaa_batting_filename, "toledo_batting.csv")
        self.assertEqual(generator.mlb_team_name, "Detroit")
        self.assertEqual(generator.aaa_team_name, "Toledo")

    def test_csv_mode_uses_discovered_prefixes(self) -> None:
        with patch.object(
            DashboardGenerator,
            "_discover_team_file_prefixes",
            return_value=("alpha", "beta"),
        ) as discover_mock:
            generator = DashboardGenerator(
                data_dir="src/data",
                out_dir="output",
                repository=_RepoWithoutPrefixes(),
            )

        discover_mock.assert_called_once()
        self.assertEqual(generator.mlb_batting_filename, "alpha_batting.csv")
        self.assertEqual(generator.aaa_batting_filename, "beta_batting.csv")


if __name__ == "__main__":
    unittest.main()