from __future__ import annotations

import numpy as np
import pandas as pd

from src.data_processing import PlayerDataTransformer


class MetricsCalculator:
    def __init__(self, transformer: PlayerDataTransformer | None = None) -> None:
        self.transformer = transformer or PlayerDataTransformer()

    @staticmethod
    def age_projection_bonus(series: pd.Series) -> pd.Series:
        a = pd.to_numeric(series, errors="coerce").fillna(0)
        bonus = pd.Series(0.0, index=a.index)
        bonus = bonus.mask(a <= 22, 0.18)
        bonus = bonus.mask((a > 22) & (a <= 24), 0.12)
        bonus = bonus.mask((a > 24) & (a <= 27), 0.05)
        bonus = bonus.mask(a > 31, -0.08)
        return bonus

    def add_hitting_metrics(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()

        df["pa_val"] = self.transformer.num_alias(df, ["pa", "plate_appearances"])
        df["ab_val"] = self.transformer.num_alias(df, ["ab", "at_bats"])
        df["obp_val"] = self.transformer.num_alias(df, ["obp"])
        df["slg_val"] = self.transformer.num_alias(df, ["slg"])
        df["ops_val"] = self.transformer.num_alias(df, ["ops"])
        df["war_val"] = self.transformer.num_alias(df, ["war"])
        df["bb_val"] = self.transformer.num_alias(df, ["bb", "walks"])
        df["k_val"] = self.transformer.num_alias(df, ["k", "so", "strikeouts"])
        df["sb_val"] = self.transformer.num_alias(df, ["sb", "stolen_bases"])
        df["cs_val"] = self.transformer.num_alias(df, ["cs", "caught_stealing"])
        df["avg_val"] = self.transformer.num_alias(df, ["avg", "ba"])

        if (df["ops_val"] == 0).all():
            df["ops_val"] = df["obp_val"] + df["slg_val"]

        df["bbpct_val"] = np.where(df["pa_val"] > 0, df["bb_val"] / df["pa_val"], 0)
        df["kpct_val"] = np.where(df["pa_val"] > 0, df["k_val"] / df["pa_val"], 0)
        df["sb_rate_val"] = np.where(df["pa_val"] > 0, df["sb_val"] / df["pa_val"], 0)

        df["offense_score"] = (
            df["obp_val"] * 3.3
            + df["slg_val"] * 2.5
            + df["ops_val"] * 1.8
            + df["war_val"] * 0.8
            + df["bbpct_val"] * 0.8
            - df["kpct_val"] * 0.9
        )

        df["ratings_hitter_now"] = (
            df["contact_now"] * 0.30
            + df["power_now"] * 0.28
            + df["eye_now"] * 0.18
            + df["avoid_k_now"] * 0.14
            + df["gap_now"] * 0.10
        )

        df["ratings_hitter_future"] = (
            df["contact_pot"] * 0.30
            + df["power_pot"] * 0.28
            + df["eye_pot"] * 0.18
            + df["avoid_k_pot"] * 0.14
            + df["gap_pot"] * 0.10
        )

        df["speed_score"] = df["sb_val"] * 0.35 - df["cs_val"] * 0.20 + df["sb_rate_val"] * 5.0

        df["scarcity_bonus"] = 0.0
        df.loc[df["is_c"], "scarcity_bonus"] += 0.45
        df.loc[df["is_ss"], "scarcity_bonus"] += 0.35
        df.loc[df["is_2b"], "scarcity_bonus"] += 0.18
        df.loc[df["is_cf"], "scarcity_bonus"] += 0.20
        df.loc[df["is_3b"], "scarcity_bonus"] += 0.10

        age_source = df["age_val"] if "age_val" in df.columns else pd.Series(0, index=df.index)
        if "age_rating_val" in df.columns:
            age_source = age_source.where(age_source != 0, df["age_rating_val"])
        df["age_bonus"] = self.age_projection_bonus(age_source)

        df["overall_hitter_score"] = (
            df["offense_score"] * 0.65 + df["ratings_hitter_now"] * 0.25 + df["scarcity_bonus"] * 0.45
        )

        df["projection_hitter_score"] = (
            df["offense_score"] * 0.35
            + df["ratings_hitter_now"] * 0.30
            + df["ratings_hitter_future"] * 0.35
            + df["age_bonus"] * 0.5
        )

        bats = df["bats"].fillna("").astype(str).str.upper().str.strip()
        is_left = bats.isin(["L", "LEFT"])
        is_right = bats.isin(["R", "RIGHT"])
        is_switch = bats.isin(["S", "SWITCH"])

        df["split_bonus_rhp"] = np.where(is_left, 0.60, np.where(is_switch, 0.26, -0.16))
        df["split_bonus_lhp"] = np.where(is_right, 0.60, np.where(is_switch, 0.26, -0.16))

        df["vs_rhp_score"] = df["overall_hitter_score"] + df["split_bonus_rhp"]
        df["vs_lhp_score"] = df["overall_hitter_score"] + df["split_bonus_lhp"]

        df["selection_platoon_weight"] = np.where(
            df["pos_bucket"].isin(["1B", "COF", "DH"]),
            5.4,
            np.where(
                df["pos_bucket"].isin(["3B"]),
                2.4,
                np.where(
                    df["pos_bucket"].isin(["2B"]),
                    1.0,
                    np.where(df["pos_bucket"].isin(["C", "SS", "CF"]), 0.15, 0.8),
                ),
            ),
        )

        df["position_stability_bonus"] = np.where(
            df["pos_bucket"].isin(["C", "SS", "CF"]),
            1.00,
            np.where(df["pos_bucket"].isin(["2B", "3B"]), 0.20, 0.0),
        )

        df["select_score_rhp"] = (
            df["overall_hitter_score"]
            + df["split_bonus_rhp"] * df["selection_platoon_weight"]
            + df["position_stability_bonus"]
        )

        df["select_score_lhp"] = (
            df["overall_hitter_score"]
            + df["split_bonus_lhp"] * df["selection_platoon_weight"]
            + df["position_stability_bonus"]
        )

        df["dh_fit_score"] = (
            df["offense_score"]
            - df["scarcity_bonus"] * 2.0
            - np.where(df["is_c"] | df["is_ss"] | df["is_2b"] | df["is_cf"], 2.0, 0.0)
            + np.where(df["is_1b"] | df["is_lf"] | df["is_rf"], 0.90, 0.0)
            + np.where(df["is_3b"], 0.35, 0.0)
        )

        df["leadoff_score"] = (
            df["obp_val"] * 4.8
            + df["bbpct_val"] * 1.3
            + df["speed_score"] * 1.5
            - df["kpct_val"] * 0.8
            - df["power_now"] * 0.02
        )

        df["two_hole_score"] = df["obp_val"] * 4.2 + df["ops_val"] * 1.6 + df["bbpct_val"] * 1.0 - df["kpct_val"] * 0.5
        df["three_hole_score"] = df["overall_hitter_score"] * 1.3 + df["ops_val"] * 2.0 + df["obp_val"] * 1.2
        df["cleanup_score"] = df["slg_val"] * 4.4 + df["ops_val"] * 2.0 + df["power_now"] * 0.08 - df["speed_score"] * 0.10

        df["leadoff_eligible"] = (df["obp_val"] >= df["obp_val"].quantile(0.45)) & (
            df["power_now"] <= df["power_now"].quantile(0.80)
        )
        df["cleanup_eligible"] = (df["slg_val"] >= df["slg_val"].quantile(0.55)) | (
            df["power_now"] >= df["power_now"].quantile(0.70)
        )
        df["three_hole_eligible"] = df["overall_hitter_score"] >= df["overall_hitter_score"].quantile(0.55)

        return df

    def add_pitching_metrics(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df["ip_val"] = self.transformer.num_alias(df, ["ip", "innings_pitched"])
        df["era_val"] = self.transformer.num_alias(df, ["era"])
        df["fip_val"] = self.transformer.num_alias(df, ["fip"])
        df["whip_val"] = self.transformer.num_alias(df, ["whip"])
        df["gs_val"] = self.transformer.num_alias(df, ["gs", "games_started"])
        df["g_val"] = self.transformer.num_alias(df, ["g", "games"])
        df["sv_val"] = self.transformer.num_alias(df, ["sv", "saves"])
        df["hld_val"] = self.transformer.num_alias(df, ["hld", "holds"])
        df["k_val"] = self.transformer.num_alias(df, ["k", "so", "strikeouts"])
        df["bb_val"] = self.transformer.num_alias(df, ["bb", "walks"])
        df["hr_val"] = self.transformer.num_alias(df, ["hr", "home_runs_allowed"])

        df["k_9_val"] = np.where(df["ip_val"] > 0, df["k_val"] * 9 / df["ip_val"], 0)
        df["bb_9_val"] = np.where(df["ip_val"] > 0, df["bb_val"] * 9 / df["ip_val"], 0)
        df["hr_9_val"] = np.where(df["ip_val"] > 0, df["hr_val"] * 9 / df["ip_val"], 0)

        df["results_pitcher_score"] = (
            -df["era_val"] * 2.0
            + -df["fip_val"] * 2.2
            + -df["whip_val"] * 1.0
            + df["k_9_val"] * 0.80
            + -df["bb_9_val"] * 0.55
            + -df["hr_9_val"] * 0.40
        )

        df["ratings_pitcher_now"] = df["stuff_now"] * 0.45 + df["movement_now"] * 0.25 + df["control_now"] * 0.30
        df["ratings_pitcher_future"] = (
            df["stuff_pot"] * 0.45 + df["movement_pot"] * 0.25 + df["control_pot"] * 0.30
        )

        age_source = df["age_val"] if "age_val" in df.columns else pd.Series(0, index=df.index)
        if "age_rating_val" in df.columns:
            age_source = age_source.where(age_source != 0, df["age_rating_val"])
        df["age_bonus"] = self.age_projection_bonus(age_source)

        df["score"] = df["results_pitcher_score"] * 0.65 + df["ratings_pitcher_now"] * 0.35
        df["projection_pitcher_score"] = (
            df["results_pitcher_score"] * 0.30
            + df["ratings_pitcher_now"] * 0.30
            + df["ratings_pitcher_future"] * 0.40
            + df["age_bonus"] * 0.5
        )

        df["role_score_sp"] = (
            np.where(df["is_starter_role"], 2.0, 0.0)
            + np.where(df["gs_val"] >= 8, 3.0, 0.0)
            + np.where((df["gs_val"] >= 4) & (df["gs_val"] < 8), 1.8, 0.0)
            + np.where(df["stamina_now"] >= 55, 1.6, 0.0)
            + np.where(df["ip_val"] >= 40, 1.0, 0.0)
        )
        df["role_score_swing"] = (
            np.where(df["gs_val"].between(2, 5), 1.6, 0.0)
            + np.where(df["stamina_now"] >= 50, 1.2, 0.0)
            + np.where(df["ip_val"] >= 25, 0.8, 0.0)
        )
        df["role_score_rp"] = (
            np.where(df["is_reliever_role"], 2.0, 0.0)
            + np.where(df["gs_val"] == 0, 1.5, 0.0)
            + np.where((df["sv_val"] + df["hld_val"]) > 0, 1.2, 0.0)
            + np.where(df["stamina_now"] < 50, 0.6, 0.0)
        )

        df["pitch_role"] = "swingman"
        df.loc[df["role_score_sp"] >= df[["role_score_swing", "role_score_rp"]].max(axis=1), "pitch_role"] = "starter"
        df.loc[df["role_score_rp"] > df[["role_score_sp", "role_score_swing"]].max(axis=1), "pitch_role"] = "reliever"

        df["true_starter_flag"] = (df["pitch_role"] == "starter") & (
            ((df["gs_val"] >= 4) & df["is_starter_role"])
            | (df["gs_val"] >= 8)
            | ((df["stamina_now"] >= 55) & (df["gs_val"] >= 3))
        )
        df["swingman_flag"] = (df["pitch_role"] == "swingman") | (
            ~df["true_starter_flag"]
            & (
                ((df["gs_val"] >= 2) & (df["gs_val"] <= 5))
                | ((df["stamina_now"] >= 50) & (df["ip_val"] >= 25) & (df["gs_val"] >= 1))
            )
        )
        df["true_reliever_flag"] = ~df["true_starter_flag"] & ~df["swingman_flag"]

        df["rotation_score"] = (
            df["score"]
            + df["ip_val"] * 0.05
            + df["gs_val"] * 0.35
            + np.where(df["true_starter_flag"], 1.2, 0.0)
            + np.where(df["swingman_flag"], 0.3, 0.0)
        )
        df["bullpen_score"] = (
            df["score"]
            + df["sv_val"] * 0.25
            + df["hld_val"] * 0.20
            + np.where(df["true_reliever_flag"], 0.8, 0.0)
        )
        return df
