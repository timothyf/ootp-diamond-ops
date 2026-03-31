from __future__ import annotations

import unittest

import pandas as pd

from src.transactions import TransactionEngine


class TransactionEngineTests(unittest.TestCase):
    def test_build_recommended_transactions_adds_mlb_exit_moves_for_callups(self) -> None:
        engine = TransactionEngine()

        aaa_hitters = pd.DataFrame(
            [
                {
                    "player_name": "Prospect Bat",
                    "is_hitter": True,
                    "injured_flag": False,
                    "projection_hitter_score": 13.2,
                    "pa_val": 120,
                    "pos_bucket": "COF",
                }
            ]
        )
        aaa_pitchers = pd.DataFrame(
            [
                {
                    "player_name": "Prospect Arm",
                    "is_pitcher": True,
                    "injured_flag": False,
                    "projection_pitcher_score": 11.8,
                    "ip_val": 32,
                }
            ]
        )
        mlb_hitters = pd.DataFrame(
            [
                {
                    "player_name": "Veteran Corner",
                    "is_hitter": True,
                    "injured_flag": False,
                    "overall_hitter_score": 8.1,
                    "pa_val": 210,
                    "age_val": 34,
                    "pos_bucket": "COF",
                    "ratings_hitter_now": 42,
                }
            ]
        )
        mlb_pitchers = pd.DataFrame(
            [
                {
                    "player_name": "Veteran Reliever",
                    "is_pitcher": True,
                    "injured_flag": False,
                    "score": 7.4,
                    "ip_val": 24,
                    "age_val": 35,
                    "true_starter_flag": False,
                    "gs_val": 0,
                    "stamina_now": 35,
                }
            ]
        )

        _, _, moves = engine.build_recommended_transactions(aaa_hitters, aaa_pitchers, mlb_hitters, mlb_pitchers)
        move_types = set(moves["move_type"].tolist())

        self.assertIn("CALL UP HITTER", move_types)
        self.assertIn("DFA / BENCH HITTER", move_types)
        self.assertIn("CALL UP PITCHER", move_types)
        self.assertIn("DFA / BENCH PITCHER", move_types)
        self.assertIn("Prospect Bat", moves["player_name"].tolist())
        self.assertIn("Veteran Corner", moves["player_name"].tolist())

    def test_build_recommended_transactions_can_recommend_external_help(self) -> None:
        engine = TransactionEngine()

        aaa_hitters = pd.DataFrame(
            [
                {
                    "player_name": "Depth Bat",
                    "is_hitter": True,
                    "injured_flag": False,
                    "projection_hitter_score": 8.0,
                    "pa_val": 12,
                    "pos_bucket": "1B",
                }
            ]
        )
        aaa_pitchers = pd.DataFrame(
            [
                {
                    "player_name": "Depth Arm",
                    "is_pitcher": True,
                    "injured_flag": False,
                    "projection_pitcher_score": 7.2,
                    "ip_val": 4,
                }
            ]
        )
        mlb_hitters = pd.DataFrame(
            [
                {
                    "player_name": "Weak Corner",
                    "is_hitter": True,
                    "injured_flag": False,
                    "overall_hitter_score": 8.4,
                    "pa_val": 180,
                    "age_val": 32,
                    "pos_bucket": "1B",
                    "ratings_hitter_now": 40,
                }
            ]
        )
        mlb_pitchers = pd.DataFrame(
            [
                {
                    "player_name": "Weak Starter",
                    "is_pitcher": True,
                    "injured_flag": False,
                    "score": 8.0,
                    "ip_val": 48,
                    "age_val": 30,
                    "true_starter_flag": True,
                    "gs_val": 9,
                    "stamina_now": 58,
                }
            ]
        )

        _, _, moves = engine.build_recommended_transactions(aaa_hitters, aaa_pitchers, mlb_hitters, mlb_pitchers)
        move_types = set(moves["move_type"].tolist())

        self.assertIn("ACQUIRE HITTER", move_types)
        self.assertIn("ACQUIRE PITCHER", move_types)

    def test_high_value_veterans_do_not_get_explicit_send_downs(self) -> None:
        engine = TransactionEngine()

        aaa_hitters = pd.DataFrame(
            [
                {
                    "player_name": "Ready Bat",
                    "is_hitter": True,
                    "injured_flag": False,
                    "projection_hitter_score": 12.4,
                    "pa_val": 150,
                    "pos_bucket": "SS",
                }
            ]
        )
        aaa_pitchers = pd.DataFrame(
            [
                {
                    "player_name": "Ready Arm",
                    "is_pitcher": True,
                    "injured_flag": False,
                    "projection_pitcher_score": 11.3,
                    "ip_val": 40,
                }
            ]
        )
        mlb_hitters = pd.DataFrame(
            [
                {
                    "player_name": "Established Veteran",
                    "is_hitter": True,
                    "injured_flag": False,
                    "overall_hitter_score": 10.8,
                    "pa_val": 260,
                    "age_val": 33,
                    "pos_bucket": "SS",
                    "ratings_hitter_now": 58,
                }
            ]
        )
        mlb_pitchers = pd.DataFrame(
            [
                {
                    "player_name": "Established Starter",
                    "is_pitcher": True,
                    "injured_flag": False,
                    "score": 10.1,
                    "ip_val": 95,
                    "age_val": 34,
                    "true_starter_flag": True,
                    "gs_val": 16,
                    "stamina_now": 64,
                }
            ]
        )

        _, _, moves = engine.build_recommended_transactions(aaa_hitters, aaa_pitchers, mlb_hitters, mlb_pitchers)
        move_types = set(moves["move_type"].tolist())
        move_players = moves["player_name"].tolist()

        self.assertIn("CALL UP HITTER", move_types)
        self.assertIn("CALL UP PITCHER", move_types)
        self.assertNotIn("SEND DOWN HITTER", move_types)
        self.assertNotIn("SEND DOWN PITCHER", move_types)
        self.assertNotIn("Established Veteran", move_players)
        self.assertNotIn("Established Starter", move_players)


if __name__ == "__main__":
    unittest.main()
