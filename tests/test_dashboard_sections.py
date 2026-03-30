from __future__ import annotations

import unittest

import pandas as pd

from src.dashboard_sections import (
    build_active_depth_chart,
    build_hitter_dashboard,
    build_hitter_toggle_dashboard,
    build_pitcher_toggle_dashboard,
)
from src.dashboard_utils import format_ip_columns


class DashboardSectionsTests(unittest.TestCase):
    def test_build_hitter_toggle_dashboard_formats_counting_stats_as_integers(self) -> None:
        df = pd.DataFrame(
            [
                {
                    "player_name": "Slugger",
                    "primary_position": "1B",
                    "is_hitter": True,
                    "pa_val": 18.0,
                    "obp_val": 0.402,
                    "slg_val": 0.611,
                    "ops_val": 1.013,
                    "contact_now": 60,
                    "power_now": 70,
                    "eye_now": 55,
                    "overall_hitter_score": 8.8,
                    "projection_hitter_score": 9.2,
                    "g": 12.0,
                    "pa": 48.0,
                    "ab": 41.0,
                    "h": 15.0,
                    "2b": 4.0,
                    "3b": 1.0,
                    "hr": 3.0,
                    "rbi": 11.0,
                    "r": 9.0,
                    "bb": 6.0,
                    "k": 8.0,
                    "sb": 2.0,
                    "cs": 1.0,
                    "avg": 0.366,
                    "obp": 0.438,
                    "slg": 0.707,
                    "ops": 1.145,
                    "war": 0.9,
                    "injury_text": "",
                }
            ]
        )

        result, _, _ = build_hitter_toggle_dashboard(df, "overall_hitter_score")

        self.assertEqual(result.loc[0, "g"], 12)
        self.assertEqual(result.loc[0, "ab"], 41)
        self.assertEqual(result.loc[0, "h"], 15)
        self.assertEqual(result.loc[0, "2b"], 4)
        self.assertEqual(result.loc[0, "3b"], 1)
        self.assertEqual(result.loc[0, "hr"], 3)
        self.assertEqual(result.loc[0, "rbi"], 11)
        self.assertEqual(result.loc[0, "r"], 9)
        self.assertEqual(result.loc[0, "bb"], 6)
        self.assertEqual(result.loc[0, "k"], 8)
        self.assertEqual(result.loc[0, "sb"], 2)
        self.assertEqual(result.loc[0, "cs"], 1)

    def test_build_pitcher_toggle_dashboard_formats_counting_stats_as_integers(self) -> None:
        df = pd.DataFrame(
            [
                {
                    "player_name": "Starter",
                    "primary_position": "SP",
                    "is_pitcher": True,
                    "ip_val": 12.0,
                    "era_val": 3.4,
                    "fip_val": 3.6,
                    "whip_val": 1.2,
                    "stuff_now": 60,
                    "movement_now": 55,
                    "control_now": 50,
                    "score": 7.5,
                    "projection_pitcher_score": 8.1,
                    "g": 5.0,
                    "gs": 4.0,
                    "w": 3.0,
                    "l": 1.0,
                    "sv": 0.0,
                    "hld": 0.0,
                    "ip": 11.1,
                    "ha": 9.0,
                    "hr": 1.0,
                    "er": 4.0,
                    "bb": 2.0,
                    "k": 14.0,
                    "era": 3.27,
                    "fip": 3.61,
                    "whip": 1.09,
                    "k_9": 11.4,
                    "bb_9": 1.6,
                    "hr_9": 0.8,
                    "war": 0.6,
                    "injury_text": "",
                }
            ]
        )

        result, _, _ = build_pitcher_toggle_dashboard(df, "score")

        self.assertEqual(result.loc[0, "g"], 5)
        self.assertEqual(result.loc[0, "gs"], 4)
        self.assertEqual(result.loc[0, "w"], 3)
        self.assertEqual(result.loc[0, "l"], 1)
        self.assertEqual(result.loc[0, "sv"], 0)
        self.assertEqual(result.loc[0, "hld"], 0)
        self.assertEqual(result.loc[0, "ha"], 9)
        self.assertEqual(result.loc[0, "hr"], 1)
        self.assertEqual(result.loc[0, "er"], 4)
        self.assertEqual(result.loc[0, "bb"], 2)
        self.assertEqual(result.loc[0, "k"], 14)

    def test_format_ip_columns_converts_toggle_table_ip_columns_to_mlb_notation(self) -> None:
        df = pd.DataFrame(
            [
                {"cv_ip": 5 + (1 / 3), "stats_ip": 7 + (2 / 3)},
                {"cv_ip": 6.2, "stats_ip": 4.1},
            ]
        )

        result = format_ip_columns(df)

        self.assertEqual(result["cv_ip"].tolist(), [5.1, 6.2])
        self.assertEqual(result["stats_ip"].tolist(), [7.2, 4.1])

    def test_build_hitter_dashboard_filters_sorts_and_rounds_pa(self) -> None:
        df = pd.DataFrame(
            [
                {
                    "player_name": "Top Bat",
                    "primary_position": "1B",
                    "is_hitter": True,
                    "pa_val": 101.6,
                    "obp_val": 0.400,
                    "slg_val": 0.550,
                    "ops_val": 0.950,
                    "contact_now": 60,
                    "power_now": 65,
                    "eye_now": 55,
                    "overall_hitter_score": 9.2,
                    "injury_text": "Healthy",
                },
                {
                    "player_name": "Bench Bat",
                    "primary_position": "LF",
                    "is_hitter": True,
                    "pa_val": 55.2,
                    "obp_val": 0.320,
                    "slg_val": 0.420,
                    "ops_val": 0.740,
                    "contact_now": 50,
                    "power_now": 45,
                    "eye_now": 40,
                    "overall_hitter_score": 4.1,
                    "injury_text": "Healthy",
                },
                {
                    "player_name": "No Sample",
                    "primary_position": "RF",
                    "is_hitter": True,
                    "pa_val": 0,
                    "obp_val": 0.0,
                    "slg_val": 0.0,
                    "ops_val": 0.0,
                    "contact_now": 50,
                    "power_now": 50,
                    "eye_now": 50,
                    "overall_hitter_score": 8.0,
                    "injury_text": "Healthy",
                },
                {
                    "player_name": "Pitcher",
                    "primary_position": "SP",
                    "is_hitter": False,
                    "pa_val": 20,
                    "obp_val": 0.100,
                    "slg_val": 0.100,
                    "ops_val": 0.200,
                    "contact_now": 20,
                    "power_now": 20,
                    "eye_now": 20,
                    "overall_hitter_score": 1.0,
                    "injury_text": "Healthy",
                },
            ]
        )

        result = build_hitter_dashboard(df, "overall_hitter_score")

        self.assertEqual(result["player_name"].tolist(), ["Top Bat", "Bench Bat"])
        self.assertEqual(result["pa"].tolist(), [102, 55])
        self.assertIn("score", result.columns)
        self.assertNotIn("pa_val", result.columns)

    def test_build_active_depth_chart_keeps_starters_unique_and_out_of_primary_backup_slots(self) -> None:
        rows = [
            {
                "player_name": "Starter Catcher",
                "primary_position": "C",
                "is_hitter": True,
                "status": "Active",
                "injured_flag": False,
                "is_c": True,
                "is_1b": False,
                "is_2b": False,
                "is_3b": False,
                "is_ss": False,
                "is_lf": False,
                "is_cf": False,
                "is_rf": False,
                "overall_hitter_score": 9.0,
                "dh_fit_score": 0.0,
                "ops_val": 0.800,
                "pa_val": 150,
                "bats": "R",
                "throws": "R",
            },
            {
                "player_name": "Starter First",
                "primary_position": "1B",
                "is_hitter": True,
                "status": "Active",
                "injured_flag": False,
                "is_c": False,
                "is_1b": True,
                "is_2b": False,
                "is_3b": False,
                "is_ss": False,
                "is_lf": False,
                "is_cf": False,
                "is_rf": False,
                "overall_hitter_score": 8.8,
                "dh_fit_score": 0.4,
                "ops_val": 0.820,
                "pa_val": 160,
                "bats": "L",
                "throws": "R",
            },
            {
                "player_name": "Second Base Starter",
                "primary_position": "2B",
                "is_hitter": True,
                "status": "Active",
                "injured_flag": False,
                "is_c": False,
                "is_1b": False,
                "is_2b": True,
                "is_3b": False,
                "is_ss": False,
                "is_lf": False,
                "is_cf": False,
                "is_rf": False,
                "overall_hitter_score": 8.4,
                "dh_fit_score": 0.0,
                "ops_val": 0.760,
                "pa_val": 140,
                "bats": "S",
                "throws": "R",
            },
            {
                "player_name": "Third Base Starter",
                "primary_position": "3B",
                "is_hitter": True,
                "status": "Active",
                "injured_flag": False,
                "is_c": False,
                "is_1b": False,
                "is_2b": False,
                "is_3b": True,
                "is_ss": False,
                "is_lf": False,
                "is_cf": False,
                "is_rf": False,
                "overall_hitter_score": 8.3,
                "dh_fit_score": 0.0,
                "ops_val": 0.750,
                "pa_val": 130,
                "bats": "R",
                "throws": "R",
            },
            {
                "player_name": "Utility Star",
                "primary_position": "SS",
                "is_hitter": True,
                "status": "Active",
                "injured_flag": False,
                "is_c": False,
                "is_1b": False,
                "is_2b": True,
                "is_3b": False,
                "is_ss": True,
                "is_lf": False,
                "is_cf": False,
                "is_rf": False,
                "overall_hitter_score": 9.5,
                "dh_fit_score": 0.0,
                "ops_val": 0.870,
                "pa_val": 180,
                "bats": "R",
                "throws": "R",
            },
            {
                "player_name": "Starter Left",
                "primary_position": "LF",
                "is_hitter": True,
                "status": "Active",
                "injured_flag": False,
                "is_c": False,
                "is_1b": False,
                "is_2b": False,
                "is_3b": False,
                "is_ss": False,
                "is_lf": True,
                "is_cf": False,
                "is_rf": False,
                "overall_hitter_score": 8.1,
                "dh_fit_score": 0.1,
                "ops_val": 0.740,
                "pa_val": 120,
                "bats": "L",
                "throws": "L",
            },
            {
                "player_name": "Starter Center",
                "primary_position": "CF",
                "is_hitter": True,
                "status": "Active",
                "injured_flag": False,
                "is_c": False,
                "is_1b": False,
                "is_2b": False,
                "is_3b": False,
                "is_ss": False,
                "is_lf": False,
                "is_cf": True,
                "is_rf": False,
                "overall_hitter_score": 8.0,
                "dh_fit_score": 0.1,
                "ops_val": 0.730,
                "pa_val": 110,
                "bats": "R",
                "throws": "R",
            },
            {
                "player_name": "Starter Right",
                "primary_position": "RF",
                "is_hitter": True,
                "status": "Active",
                "injured_flag": False,
                "is_c": False,
                "is_1b": False,
                "is_2b": False,
                "is_3b": False,
                "is_ss": False,
                "is_lf": False,
                "is_cf": False,
                "is_rf": True,
                "overall_hitter_score": 7.9,
                "dh_fit_score": 0.1,
                "ops_val": 0.720,
                "pa_val": 115,
                "bats": "R",
                "throws": "R",
            },
            {
                "player_name": "DH Starter",
                "primary_position": "LF",
                "is_hitter": True,
                "status": "Active",
                "injured_flag": False,
                "is_c": False,
                "is_1b": False,
                "is_2b": False,
                "is_3b": False,
                "is_ss": False,
                "is_lf": True,
                "is_cf": False,
                "is_rf": False,
                "overall_hitter_score": 7.5,
                "dh_fit_score": 2.0,
                "ops_val": 0.700,
                "pa_val": 90,
                "bats": "L",
                "throws": "L",
            },
            {
                "player_name": "Backup Catcher",
                "primary_position": "C",
                "is_hitter": True,
                "status": "Active",
                "injured_flag": False,
                "is_c": True,
                "is_1b": False,
                "is_2b": False,
                "is_3b": False,
                "is_ss": False,
                "is_lf": False,
                "is_cf": False,
                "is_rf": False,
                "overall_hitter_score": 6.0,
                "dh_fit_score": 0.0,
                "ops_val": 0.650,
                "pa_val": 60,
                "bats": "R",
                "throws": "R",
            },
            {
                "player_name": "Bench Infield",
                "primary_position": "2B",
                "is_hitter": True,
                "status": "Active",
                "injured_flag": False,
                "is_c": False,
                "is_1b": False,
                "is_2b": True,
                "is_3b": False,
                "is_ss": True,
                "is_lf": False,
                "is_cf": False,
                "is_rf": False,
                "overall_hitter_score": 6.8,
                "dh_fit_score": 0.0,
                "ops_val": 0.680,
                "pa_val": 70,
                "bats": "R",
                "throws": "R",
            },
            {
                "player_name": "Bench Outfield",
                "primary_position": "CF",
                "is_hitter": True,
                "status": "Active",
                "injured_flag": False,
                "is_c": False,
                "is_1b": False,
                "is_2b": False,
                "is_3b": False,
                "is_ss": False,
                "is_lf": True,
                "is_cf": True,
                "is_rf": True,
                "overall_hitter_score": 6.7,
                "dh_fit_score": 0.2,
                "ops_val": 0.675,
                "pa_val": 75,
                "bats": "L",
                "throws": "L",
            },
        ]
        df = pd.DataFrame(rows)

        result = build_active_depth_chart(df, depth_per_position=2)

        starters = result.loc[result["rank"] == 1, ["position", "player_name"]]
        starter_names = set(starters["player_name"])
        primary_backups = result.loc[result["rank"] == 2, "player_name"]

        self.assertEqual(len(starter_names), len(starters))
        self.assertEqual(
            starters.loc[starters["position"] == "SS", "player_name"].iloc[0],
            "Utility Star",
        )
        self.assertEqual(
            starters.loc[starters["position"] == "2B", "player_name"].iloc[0],
            "Second Base Starter",
        )
        self.assertTrue(primary_backups[~primary_backups.isin(starter_names)].shape[0] == len(primary_backups))


if __name__ == "__main__":
    unittest.main()
