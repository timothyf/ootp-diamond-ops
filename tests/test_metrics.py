from __future__ import annotations

import unittest

import pandas as pd

from src.metrics import MetricsCalculator


class MetricsCalculatorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.calculator = MetricsCalculator()

    @staticmethod
    def _base_hitter_row(**overrides: object) -> dict[str, object]:
        row: dict[str, object] = {
            "player_name": "Test Hitter",
            "is_hitter": True,
            "is_c": False,
            "is_1b": True,
            "is_2b": False,
            "is_3b": False,
            "is_ss": False,
            "is_lf": False,
            "is_cf": False,
            "is_rf": False,
            "pos_bucket": "1B",
            "pa": 200,
            "ab": 180,
            "obp": 0.360,
            "slg": 0.500,
            "ops": 0.860,
            "war": 1.5,
            "bb": 20,
            "k": 40,
            "sb": 5,
            "cs": 2,
            "avg": 0.280,
            "contact_now": 55,
            "power_now": 55,
            "eye_now": 50,
            "avoid_k_now": 50,
            "gap_now": 50,
            "contact_pot": 60,
            "power_pot": 60,
            "eye_pot": 55,
            "avoid_k_pot": 55,
            "gap_pot": 50,
            "vsr_contact": 55,
            "vsr_power": 55,
            "vsr_eye": 50,
            "vsl_contact": 55,
            "vsl_power": 55,
            "vsl_eye": 50,
            "running_speed": 50,
            "running_baserunning": 50,
            "running_stealing_rate": 50,
            "field_c_ability": 0,
            "field_c_framing": 0,
            "field_c_arm": 0,
            "field_if_range": 50,
            "field_if_arm": 50,
            "field_if_error": 50,
            "field_of_range": 0,
            "field_of_arm": 0,
            "field_of_error": 0,
            "avg_exit_velo": 95,
            "tracked_bip": 50,
            "hard_hit_rate": 0.45,
            "barrel_rate": 0.10,
            "sweet_spot_rate": 0.35,
            "weak_contact_rate": 0.10,
            "bats": "R",
            "age_val": 26,
            "injured_flag": False,
        }
        row.update(overrides)
        return row

    @staticmethod
    def _base_pitcher_row(**overrides: object) -> dict[str, object]:
        row: dict[str, object] = {
            "player_name": "Test Pitcher",
            "is_pitcher": True,
            "ip": 12.0,
            "era": 3.50,
            "fip": 3.60,
            "whip": 1.10,
            "gs": 0,
            "g": 8,
            "sv": 0,
            "hld": 0,
            "k": 16,
            "bb": 4,
            "hr": 1,
            "gb": 18,
            "fb": 10,
            "stuff_now": 50,
            "movement_now": 50,
            "control_now": 50,
            "stuff_pot": 60,
            "movement_pot": 55,
            "control_pot": 55,
            "pitch_vsl_stuff": 50,
            "pitch_vsl_movement": 50,
            "pitch_vsl_control": 50,
            "pitch_vsr_stuff": 50,
            "pitch_vsr_movement": 50,
            "pitch_vsr_control": 50,
            "pitch_ground_fly": 50,
            "pitch_stamina": 45,
            "stamina_now": 45,
            "age_val": 26,
            "is_starter_role": False,
            "is_reliever_role": True,
        }
        row.update(overrides)
        return row

    def test_hitter_contact_quality_uses_tracked_bip_as_reliability_sample(self) -> None:
        df = pd.DataFrame(
            [
                self._base_hitter_row(player_name="Small Sample", tracked_bip=10),
                self._base_hitter_row(player_name="Large Sample", tracked_bip=200),
            ]
        )

        result = self.calculator.add_hitting_metrics(df)
        small = result.loc[result["player_name"] == "Small Sample", "contact_quality_component"].iloc[0]
        large = result.loc[result["player_name"] == "Large Sample", "contact_quality_component"].iloc[0]

        self.assertLess(small, large)

    def test_hitter_offense_score_no_longer_changes_with_ops_duplicate_input(self) -> None:
        df = pd.DataFrame(
            [
                self._base_hitter_row(player_name="Normal OPS", ops=0.860),
                self._base_hitter_row(player_name="Inflated OPS", ops=1.260),
            ]
        )

        result = self.calculator.add_hitting_metrics(df)
        scores = result.set_index("player_name")["offense_score"]

        self.assertAlmostEqual(scores["Normal OPS"], scores["Inflated OPS"], places=6)

    def test_pitcher_results_score_does_not_get_starter_profile_discount(self) -> None:
        df = pd.DataFrame(
            [
                self._base_pitcher_row(player_name="Reliever Profile"),
                self._base_pitcher_row(
                    player_name="Starter Profile",
                    gs=3,
                    stamina_now=60,
                    pitch_stamina=60,
                    is_starter_role=True,
                    is_reliever_role=False,
                ),
            ]
        )

        result = self.calculator.add_pitching_metrics(df)
        scores = result.set_index("player_name")["results_pitcher_score"]

        self.assertAlmostEqual(scores["Reliever Profile"], scores["Starter Profile"], places=6)


if __name__ == "__main__":
    unittest.main()
