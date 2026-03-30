from __future__ import annotations

import numpy as np
import pandas as pd

from src.data_processing import PlayerDataTransformer


class MetricsCalculator:
    SCORE_BASELINE_OFFSET = 10.0
    HITTER_SCORE_SPREAD_MULTIPLIER = 2.0

    def __init__(self, transformer: PlayerDataTransformer | None = None) -> None:
        self.transformer = transformer or PlayerDataTransformer()

    @staticmethod
    def reliability_weight(sample: pd.Series, k: float) -> pd.Series:
        s = pd.to_numeric(sample, errors="coerce").fillna(0)
        return s / (s + float(k))

    @staticmethod
    def regress_to_baseline(value: pd.Series, baseline: float, weight: pd.Series) -> pd.Series:
        return value * weight + baseline * (1.0 - weight)

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
        df["score_baseline_offset"] = self.SCORE_BASELINE_OFFSET

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
        df["discipline_score"] = df["bbpct_val"] * 1.2 - df["kpct_val"] * 1.0

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
        # Center ratings so 50-grade talent contributes near zero and only above/below-average
        # ratings materially shift score.
        df["ratings_hitter_now_component"] = (df["ratings_hitter_now"] - 50.0) / 5.0
        df["ratings_hitter_future_component"] = (df["ratings_hitter_future"] - 50.0) / 5.0

        df["vsr_contact_val"] = self.transformer.num_alias(df, ["vsr_contact"])
        df["vsr_power_val"] = self.transformer.num_alias(df, ["vsr_power"])
        df["vsr_eye_val"] = self.transformer.num_alias(df, ["vsr_eye"])
        df["vsl_contact_val"] = self.transformer.num_alias(df, ["vsl_contact"])
        df["vsl_power_val"] = self.transformer.num_alias(df, ["vsl_power"])
        df["vsl_eye_val"] = self.transformer.num_alias(df, ["vsl_eye"])

        df["platoon_skill_rhp"] = (
            (df["vsr_contact_val"] + df["vsr_power_val"] + df["vsr_eye_val"]) / 3.0 - 50.0
        ) / 25.0
        df["platoon_skill_lhp"] = (
            (df["vsl_contact_val"] + df["vsl_power_val"] + df["vsl_eye_val"]) / 3.0 - 50.0
        ) / 25.0
        df["platoon_skill_component"] = (df["platoon_skill_rhp"] + df["platoon_skill_lhp"]) / 2.0

        df["run_speed_val"] = self.transformer.num_alias(df, ["running_speed"])
        df["run_baserunning_val"] = self.transformer.num_alias(df, ["running_baserunning"])
        df["run_steal_rate_val"] = self.transformer.num_alias(df, ["running_stealing_rate"])
        df["running_component"] = (
            ((df["run_speed_val"] + df["run_baserunning_val"] + df["run_steal_rate_val"]) / 3.0 - 50.0) / 25.0
        )

        df["field_c_component"] = (
            (
                self.transformer.num_alias(df, ["field_c_ability"]) * 0.45
                + self.transformer.num_alias(df, ["field_c_framing"]) * 0.35
                + self.transformer.num_alias(df, ["field_c_arm"]) * 0.20
            )
            - 50.0
        ) / 20.0
        df["field_if_component"] = (
            (
                self.transformer.num_alias(df, ["field_if_range"]) * 0.45
                + self.transformer.num_alias(df, ["field_if_arm"]) * 0.25
                - self.transformer.num_alias(df, ["field_if_error"]) * 0.30
            )
            - 20.0
        ) / 20.0
        df["field_of_component"] = (
            (
                self.transformer.num_alias(df, ["field_of_range"]) * 0.45
                + self.transformer.num_alias(df, ["field_of_arm"]) * 0.25
                - self.transformer.num_alias(df, ["field_of_error"]) * 0.30
            )
            - 20.0
        ) / 20.0

        df["defensive_component"] = np.where(
            df["is_c"],
            df["field_c_component"],
            np.where(
                df["is_ss"] | df["is_2b"] | df["is_3b"] | df["is_1b"],
                df["field_if_component"],
                np.where(df["is_cf"] | df["is_lf"] | df["is_rf"], df["field_of_component"], 0.0),
            ),
        )

        # Quality of contact metrics derived from batted-ball data (exit velo, launch angle)
        # These are NA-safe defaults; only present when DB batting loader populated them.
        df["avg_exit_velo"] = self.transformer.num_alias(df, ["avg_exit_velo"])
        df["hard_hit_rate"] = self.transformer.num_alias(df, ["hard_hit_rate"])
        df["barrel_rate"] = self.transformer.num_alias(df, ["barrel_rate"])
        df["sweet_spot_rate"] = self.transformer.num_alias(df, ["sweet_spot_rate"])
        df["weak_contact_rate"] = self.transformer.num_alias(df, ["weak_contact_rate"])

        # Normalize exit velocity: scale from [70, 110] mph to [-1, 1] range; 90 mph = 0.
        ev_normalized = np.where(
            df["avg_exit_velo"] > 0,
            (df["avg_exit_velo"] - 90.0) / 20.0,
            0.0
        )
        # Combine contact signals: hard hit + barrel + sweet spot are positive; weak contact is negative.
        # Weight barrel_rate higher than individual components since it represents optimal EV+LA combination.
        contact_quality_raw = (
            ev_normalized * 0.25
            + df["hard_hit_rate"] * 3.0
            + df["barrel_rate"] * 4.0
            + df["sweet_spot_rate"] * 2.5
            - df["weak_contact_rate"] * 2.0
        )
        # Reliability-weight by tracked balls in play; use PA as proxy if ball data unavailable.
        contact_quality_weight = self.reliability_weight(df["avg_exit_velo"], k=80)
        df["contact_quality_component"] = contact_quality_raw * contact_quality_weight

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

        df["hitting_reliability"] = self.reliability_weight(df["pa_val"], k=180)
        offense_baseline = float(df["offense_score"].median()) if not df.empty else 0.0
        df["offense_score_regressed"] = self.regress_to_baseline(
            df["offense_score"],
            offense_baseline,
            df["hitting_reliability"],
        )
        df["discipline_component"] = df["discipline_score"] * self.reliability_weight(df["pa_val"], k=120) * 4.0

        overall_hitter_subtotal = (
            df["offense_score_regressed"] * 0.52
            + df["ratings_hitter_now_component"] * 0.22
            + df["scarcity_bonus"] * 0.40
            + df["discipline_component"] * 0.8
            + df["platoon_skill_component"] * 0.6
            + df["defensive_component"] * 0.5
            + df["contact_quality_component"] * 0.08
            + df["running_component"] * 0.25
        )
        df["overall_hitter_score"] = (
            overall_hitter_subtotal * self.HITTER_SCORE_SPREAD_MULTIPLIER
            + self.SCORE_BASELINE_OFFSET
        )

        projection_hitter_subtotal = (
            df["offense_score_regressed"] * 0.58
            + df["ratings_hitter_now_component"] * 0.27
            + df["ratings_hitter_future_component"] * 0.48
            + df["age_bonus"] * 0.5
            + df["discipline_component"] * 0.9
            + df["platoon_skill_component"] * 0.7
            + df["defensive_component"] * 0.35
            + df["contact_quality_component"] * 0.04
            + df["running_component"] * 0.2
            + df["scarcity_bonus"] * 0.35
        )
        df["projection_hitter_score"] = (
            projection_hitter_subtotal * self.HITTER_SCORE_SPREAD_MULTIPLIER
            + self.SCORE_BASELINE_OFFSET
        )

        bats = df["bats"].fillna("").astype(str).str.upper().str.strip()
        is_left = bats.isin(["L", "LEFT"])
        is_right = bats.isin(["R", "RIGHT"])
        is_switch = bats.isin(["S", "SWITCH"])

        handedness_split_rhp = np.where(is_left, 0.60, np.where(is_switch, 0.26, -0.16))
        handedness_split_lhp = np.where(is_right, 0.60, np.where(is_switch, 0.26, -0.16))
        df["split_bonus_rhp"] = handedness_split_rhp + df["platoon_skill_rhp"] * 0.22
        df["split_bonus_lhp"] = handedness_split_lhp + df["platoon_skill_lhp"] * 0.22

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
        df["score_baseline_offset"] = self.SCORE_BASELINE_OFFSET
        ip_raw = self.transformer.num_alias(df, ["ip", "innings_pitched"])
        df["ip_val"] = self.transformer.innings_notation_to_decimal(ip_raw)
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
        df["gb_val"] = self.transformer.num_alias(df, ["gb", "ground_balls"])
        df["fb_val"] = self.transformer.num_alias(df, ["fb", "fly_balls", "gf"])

        df["k_9_val"] = np.where(df["ip_val"] > 0, df["k_val"] * 9 / df["ip_val"], 0)
        df["bb_9_val"] = np.where(df["ip_val"] > 0, df["bb_val"] * 9 / df["ip_val"], 0)
        df["hr_9_val"] = np.where(df["ip_val"] > 0, df["hr_val"] * 9 / df["ip_val"], 0)
        df["k_bb_9_val"] = df["k_9_val"] - df["bb_9_val"]
        df["gb_share_val"] = np.where((df["gb_val"] + df["fb_val"]) > 0, df["gb_val"] / (df["gb_val"] + df["fb_val"]), 0)

        starter_profile = ((df["gs_val"] >= 3) | (df["stamina_now"] >= 55)).astype(float)
        starter_sample_scale = np.clip(df["ip_val"] / 60.0, 0.0, 1.0)
        starter_penalty_scale = 1.0 - starter_profile * (1.0 - starter_sample_scale) * 0.35

        df["results_pitcher_score"] = (
            -df["era_val"] * 1.8
            + -df["fip_val"] * 1.7 * starter_penalty_scale
            + -df["whip_val"] * 0.9
            + df["k_9_val"] * 0.85
            + -df["bb_9_val"] * 0.42 * starter_penalty_scale
            + -df["hr_9_val"] * 0.35
        )

        df["ratings_pitcher_now"] = df["stuff_now"] * 0.45 + df["movement_now"] * 0.25 + df["control_now"] * 0.30
        df["ratings_pitcher_future"] = (
            df["stuff_pot"] * 0.45 + df["movement_pot"] * 0.25 + df["control_pot"] * 0.30
        )
        df["ratings_pitcher_now_component"] = (df["ratings_pitcher_now"] - 50.0) / 5.0
        df["ratings_pitcher_future_component"] = (df["ratings_pitcher_future"] - 50.0) / 5.0

        vsl_mix = (
            self.transformer.num_alias(df, ["pitch_vsl_stuff"])
            + self.transformer.num_alias(df, ["pitch_vsl_movement"])
            + self.transformer.num_alias(df, ["pitch_vsl_control"])
        )
        vsr_mix = (
            self.transformer.num_alias(df, ["pitch_vsr_stuff"])
            + self.transformer.num_alias(df, ["pitch_vsr_movement"])
            + self.transformer.num_alias(df, ["pitch_vsr_control"])
        )
        df["pitcher_platoon_component"] = ((vsl_mix + vsr_mix) / 6.0 - 50.0) / 25.0

        df["command_dominance_component"] = (
            df["k_bb_9_val"] * 0.9
            + df["control_now"] * 0.06
            + df["stuff_now"] * 0.04
            + df["pitcher_platoon_component"] * 0.4
        )

        ground_fly_rating = self.transformer.num_alias(df, ["pitch_ground_fly"])
        df["contact_management_component"] = (
            df["gb_share_val"] * 2.0
            - df["hr_9_val"] * 0.25
            + df["movement_now"] * 0.03
            + (ground_fly_rating - 50.0) / 100.0
        )

        age_source = df["age_val"] if "age_val" in df.columns else pd.Series(0, index=df.index)
        if "age_rating_val" in df.columns:
            age_source = age_source.where(age_source != 0, df["age_rating_val"])
        df["age_bonus"] = self.age_projection_bonus(age_source)

        df["pitching_reliability"] = self.reliability_weight(df["ip_val"], k=45)
        pitcher_baseline = float(df["results_pitcher_score"].median()) if not df.empty else 0.0
        df["results_pitcher_score_regressed"] = self.regress_to_baseline(
            df["results_pitcher_score"],
            pitcher_baseline,
            df["pitching_reliability"],
        )

        stamina_source = np.where(self.transformer.num_alias(df, ["pitch_stamina"]) > 0, self.transformer.num_alias(df, ["pitch_stamina"]), df["stamina_now"])
        df["durability_component"] = (
            df["ip_val"] * 0.015
            + df["gs_val"] * 0.12
            + np.clip(stamina_source - 50.0, -30.0, 30.0) * 0.03
        )

        df["score"] = (
            df["results_pitcher_score_regressed"] * 0.58
            + df["ratings_pitcher_now_component"] * 0.30
            + df["command_dominance_component"] * 0.20
            + df["contact_management_component"] * 0.14
            + df["durability_component"] * 0.12
            + self.SCORE_BASELINE_OFFSET
        )
        df["projection_pitcher_score"] = (
            df["results_pitcher_score_regressed"] * 0.50
            + df["ratings_pitcher_now_component"] * 0.22
            + df["ratings_pitcher_future_component"] * 0.24
            + df["age_bonus"] * 0.30
            + df["command_dominance_component"] * 0.20
            + df["contact_management_component"] * 0.14
            + df["durability_component"] * 0.10
            + self.SCORE_BASELINE_OFFSET
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
