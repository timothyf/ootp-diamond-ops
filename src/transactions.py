from __future__ import annotations

import numpy as np
import pandas as pd


class TransactionEngine:
    POSITION_FALLBACKS = {
        "C": ["C"],
        "SS": ["SS", "2B"],
        "2B": ["2B", "SS", "3B"],
        "3B": ["3B", "1B", "2B"],
        "1B": ["1B", "3B", "DH"],
        "CF": ["CF", "COF"],
        "COF": ["COF", "CF", "DH"],
        "DH": ["DH", "1B", "COF"],
    }

    @staticmethod
    def aaa_hit_recommendation(row: pd.Series, hi: float, mid: float) -> str:
        if row["injured_flag"]:
            return "DO NOT PROMOTE - INJURED"
        if row["projection_hitter_score"] >= hi and row.get("pa_val", 0) >= 30:
            return "PROMOTE NOW"
        if row["projection_hitter_score"] >= mid:
            return "MONITOR"
        return "HOLD"

    @staticmethod
    def aaa_pitch_recommendation(row: pd.Series, hi: float, mid: float) -> str:
        if row["injured_flag"]:
            return "DO NOT PROMOTE - INJURED"
        if row["projection_pitcher_score"] >= hi and row.get("ip_val", 0) >= 10:
            return "PROMOTE NOW"
        if row["projection_pitcher_score"] >= mid:
            return "MONITOR"
        return "HOLD"

    @staticmethod
    def _num(row: pd.Series | None, column: str) -> float:
        if row is None:
            return 0.0
        return float(pd.to_numeric(pd.Series([row.get(column)]), errors="coerce").fillna(0.0).iloc[0])

    @staticmethod
    def _pos(row: pd.Series | None) -> str:
        return str(row.get("pos_bucket", "")).strip() if row is not None else ""

    def _recommended_hitter_exit_type(self, row: pd.Series | None) -> str | None:
        if row is None:
            return None
        age = self._num(row, "age_val")
        bucket = self._pos(row)
        score = self._num(row, "overall_hitter_score")
        pa_val = self._num(row, "pa_val")
        if age >= 30 and score >= 10.0:
            return None
        if age >= 31 and bucket in {"1B", "COF", "DH"}:
            return "DFA / BENCH HITTER"
        if age <= 28 or pa_val < 120:
            return "SEND DOWN HITTER"
        return None

    def _recommended_pitcher_exit_type(self, row: pd.Series | None) -> str | None:
        if row is None:
            return None
        age = self._num(row, "age_val")
        score = self._num(row, "score")
        ip_val = self._num(row, "ip_val")
        is_starter = bool(row.get("true_starter_flag", False))
        if age >= 30 and score >= 9.5:
            return None
        if age >= 32 and not is_starter:
            return "DFA / BENCH PITCHER"
        if age <= 29 or ip_val < 40:
            return "SEND DOWN PITCHER"
        return None

    def _acquire_hitter_profile(self, row: pd.Series | None) -> str:
        bucket = self._pos(row)
        if bucket in {"C", "SS", "CF"}:
            return "Up-the-middle regular"
        if bucket in {"2B", "3B"}:
            return "Everyday infield bat"
        return "Corner bat / DH"

    def _acquire_pitcher_profile(self, row: pd.Series | None) -> str:
        if row is None:
            return "Pitching upgrade"
        is_starter = bool(row.get("true_starter_flag", False)) or self._num(row, "gs_val") >= 5 or self._num(row, "stamina_now") >= 55
        return "Back-end starter" if is_starter else "Leverage reliever"

    def compute_replacement_penalty(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        top_cut = df["overall_hitter_score"].quantile(0.80) if not df.empty else 0
        median_cut = df["overall_hitter_score"].quantile(0.50) if not df.empty else 0
        top_pa_cut = df["pa_val"].quantile(0.75) if "pa_val" in df.columns and not df.empty else 0

        df["replace_penalty"] = 0.0
        df.loc[df["overall_hitter_score"] >= top_cut, "replace_penalty"] += 4.0
        df.loc[(df["overall_hitter_score"] >= median_cut) & (df["overall_hitter_score"] < top_cut), "replace_penalty"] += 1.2

        if "pa_val" in df.columns:
            df.loc[df["pa_val"] >= top_pa_cut, "replace_penalty"] += 2.0
            df.loc[df["pa_val"] < 120, "replace_penalty"] -= 0.8
            df.loc[df["pa_val"] < 60, "replace_penalty"] -= 0.8

        if "age_val" in df.columns:
            df.loc[(df["age_val"] > 0) & (df["age_val"] <= 28), "replace_penalty"] += 2.0
            df.loc[df["age_val"] >= 33, "replace_penalty"] -= 1.0

        df.loc[df["pos_bucket"].isin(["C", "SS", "CF"]), "replace_penalty"] += 2.0
        df.loc[df["pos_bucket"].isin(["2B", "3B"]), "replace_penalty"] += 0.7
        df.loc[df["pos_bucket"].isin(["1B", "COF", "DH"]), "replace_penalty"] -= 0.6

        if "ratings_hitter_now" in df.columns:
            rating_cut = df["ratings_hitter_now"].quantile(0.75) if not df.empty else 0
            df.loc[df["ratings_hitter_now"] >= rating_cut, "replace_penalty"] += 1.5

        df["bench_bonus"] = 0.0
        df.loc[df["pos_bucket"].isin(["1B", "COF", "DH"]), "bench_bonus"] -= 0.8
        df.loc[(df["overall_hitter_score"] < median_cut) & (df["pos_bucket"].isin(["1B", "COF", "DH"])), "bench_bonus"] -= 0.8
        df.loc[(df["age_val"] >= 31) & (df["pos_bucket"].isin(["1B", "COF", "DH"])), "bench_bonus"] -= 0.5

        df["replacement_target_score"] = df["overall_hitter_score"] + df["replace_penalty"] + df["bench_bonus"]
        df["roster_casualty_score"] = (
            df["replacement_target_score"]
            - np.where(df["pos_bucket"].isin(["1B", "COF", "DH"]), 1.0, 0.0)
            - np.where(df["age_val"] >= 31, 0.6, 0.0)
            - np.where(df["pa_val"] < 120, 0.8, 0.0)
        )
        return df

    def find_replacement_target(self, mlb_weak_hitters: pd.DataFrame, bucket: str) -> pd.Series | None:
        search_buckets = self.POSITION_FALLBACKS.get(bucket, [bucket])
        for search_bucket in search_buckets:
            pool = mlb_weak_hitters.loc[mlb_weak_hitters["pos_bucket"] == search_bucket].sort_values(
                "replacement_target_score", ascending=True
            )
            if not pool.empty:
                return pool.iloc[0]
        if not mlb_weak_hitters.empty:
            return mlb_weak_hitters.sort_values("replacement_target_score", ascending=True).iloc[0]
        return None

    def find_roster_casualty(self, mlb_weak_hitters: pd.DataFrame, primary_bucket: str) -> pd.Series | None:
        search_buckets = self.POSITION_FALLBACKS.get(primary_bucket, [primary_bucket])
        for search_bucket in search_buckets:
            pool = mlb_weak_hitters.loc[mlb_weak_hitters["pos_bucket"] == search_bucket].sort_values(
                "roster_casualty_score", ascending=True
            )
            if not pool.empty:
                return pool.iloc[0]
        pool = mlb_weak_hitters.loc[mlb_weak_hitters["pos_bucket"].isin(["1B", "COF", "DH"])].sort_values(
            "roster_casualty_score", ascending=True
        )
        if not pool.empty:
            return pool.iloc[0]
        if not mlb_weak_hitters.empty:
            return mlb_weak_hitters.sort_values("roster_casualty_score", ascending=True).iloc[0]
        return None

    @staticmethod
    def build_roster_note(prospect_row: pd.Series, target_row: pd.Series | None, casualty_row: pd.Series | None) -> str:
        if target_row is None and casualty_row is None:
            return "No clear one-for-one target; consider roster shuffle."
        prospect_bucket = prospect_row.get("pos_bucket", "")
        replace_name = target_row.get("player_name", "") if target_row is not None else ""
        replace_bucket = target_row.get("pos_bucket", "") if target_row is not None else ""
        casualty_name = casualty_row.get("player_name", "") if casualty_row is not None else ""

        if prospect_bucket in ["SS", "2B", "CF", "C"] and target_row is not None:
            return f"Direct positional pressure on {replace_name} at {replace_bucket}; roster casualty may still be elsewhere."
        if casualty_row is not None and casualty_name and casualty_name != replace_name:
            return f"Likely roster shuffle: positional pressure on {replace_name}, but the more expendable roster casualty may be {casualty_name}."
        if prospect_bucket in ["3B", "1B", "COF", "DH"]:
            return f"Could force a corner/DH/bench reshuffle; weakest same-bucket fit is {replace_name}."
        return f"Most likely pressure point is {replace_name}."

    def build_recommended_transactions(
        self,
        aaa_hitters: pd.DataFrame,
        aaa_pitchers: pd.DataFrame,
        mlb_hitters: pd.DataFrame,
        mlb_pitchers: pd.DataFrame,
    ) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        hit_hi = aaa_hitters.loc[aaa_hitters["is_hitter"], "projection_hitter_score"].quantile(0.85)
        hit_mid = aaa_hitters.loc[aaa_hitters["is_hitter"], "projection_hitter_score"].quantile(0.65)
        pit_hi = aaa_pitchers.loc[aaa_pitchers["is_pitcher"], "projection_pitcher_score"].quantile(0.85)
        pit_mid = aaa_pitchers.loc[aaa_pitchers["is_pitcher"], "projection_pitcher_score"].quantile(0.65)

        aaa_hitters = aaa_hitters.copy()
        aaa_pitchers = aaa_pitchers.copy()
        aaa_hitters["recommendation"] = aaa_hitters.apply(lambda r: self.aaa_hit_recommendation(r, hit_hi, hit_mid), axis=1)
        aaa_pitchers["recommendation"] = aaa_pitchers.apply(lambda r: self.aaa_pitch_recommendation(r, pit_hi, pit_mid), axis=1)

        mlb_weak_hitters = mlb_hitters.loc[
            mlb_hitters["is_hitter"] & (mlb_hitters["pa_val"] > 0) & (~mlb_hitters["injured_flag"])
        ].copy()
        mlb_weak_hitters = self.compute_replacement_penalty(mlb_weak_hitters)
        mlb_weak_pitchers = mlb_pitchers.loc[mlb_pitchers["is_pitcher"] & (mlb_pitchers["ip_val"] > 0)].sort_values(
            "score", ascending=True
        ).copy()

        moves = []
        hitter_exit_names: set[str] = set()
        pitcher_exit_names: set[str] = set()
        used_pitcher_replacements: set[str] = set()

        promote_hitters = aaa_hitters.loc[
            (aaa_hitters["is_hitter"]) & (aaa_hitters["recommendation"] == "PROMOTE NOW")
        ].sort_values("projection_hitter_score", ascending=False).head(8)
        for _, row in promote_hitters.iterrows():
            bucket = row["pos_bucket"]
            target = self.find_replacement_target(mlb_weak_hitters, bucket)
            casualty = self.find_roster_casualty(mlb_weak_hitters, bucket)

            replace_name = target["player_name"] if target is not None else ""
            replace_bucket = target["pos_bucket"] if target is not None else ""
            target_score = target["overall_hitter_score"] if target is not None else 0
            target_replace_score = target["replacement_target_score"] if target is not None else 0
            casualty_name = casualty["player_name"] if casualty is not None else ""
            casualty_score = casualty["roster_casualty_score"] if casualty is not None else 0
            score_gap = row["projection_hitter_score"] - target_score
            roster_note = self.build_roster_note(row, target, casualty)

            moves.append(
                {
                    "move_type": "CALL UP HITTER",
                    "player_name": row["player_name"],
                    "reason": row["recommendation"],
                    "score": row["projection_hitter_score"],
                    "possible_replace": replace_name,
                    "pos_bucket": bucket,
                    "replace_bucket": replace_bucket,
                    "score_gap": score_gap,
                    "replace_score": target_replace_score,
                    "likely_casualty": casualty_name,
                    "casualty_score": casualty_score,
                    "roster_note": roster_note,
                    "priority_value": 4.0 + max(score_gap, 0.0),
                }
            )

            exit_type = self._recommended_hitter_exit_type(casualty)
            if casualty is not None and casualty_name and casualty_name not in hitter_exit_names and exit_type:
                hitter_exit_names.add(casualty_name)
                casualty_actual_score = self._num(casualty, "overall_hitter_score")
                moves.append(
                    {
                        "move_type": exit_type,
                        "player_name": casualty_name,
                        "reason": f"Make room for {row['player_name']}",
                        "score": casualty_actual_score,
                        "possible_replace": row["player_name"],
                        "pos_bucket": self._pos(casualty),
                        "replace_bucket": bucket,
                        "score_gap": row["projection_hitter_score"] - casualty_actual_score,
                        "replace_score": row["projection_hitter_score"],
                        "likely_casualty": casualty_name,
                        "casualty_score": casualty_actual_score,
                        "roster_note": roster_note,
                        "priority_value": 3.0 + max(row["projection_hitter_score"] - casualty_actual_score, 0.0),
                    }
                )

        promote_pitchers = aaa_pitchers.loc[
            (aaa_pitchers["is_pitcher"]) & (aaa_pitchers["recommendation"] == "PROMOTE NOW")
        ].sort_values("projection_pitcher_score", ascending=False).head(5)
        for _, row in promote_pitchers.iterrows():
            available_pitchers = mlb_weak_pitchers.loc[~mlb_weak_pitchers["player_name"].isin(used_pitcher_replacements)]
            replace_row = available_pitchers.iloc[0] if not available_pitchers.empty else (mlb_weak_pitchers.iloc[0] if not mlb_weak_pitchers.empty else None)
            replace_name = replace_row["player_name"] if replace_row is not None else ""
            replace_score = self._num(replace_row, "score")
            if replace_name:
                used_pitcher_replacements.add(replace_name)

            moves.append(
                {
                    "move_type": "CALL UP PITCHER",
                    "player_name": row["player_name"],
                    "reason": row["recommendation"],
                    "score": row["projection_pitcher_score"],
                    "possible_replace": replace_name,
                    "pos_bucket": "P",
                    "replace_bucket": "P",
                    "score_gap": row["projection_pitcher_score"] - replace_score,
                    "replace_score": replace_score,
                    "likely_casualty": replace_name,
                    "casualty_score": replace_score,
                    "roster_note": (
                        f"Most likely pressure point is {replace_name} in the MLB staff."
                        if replace_name
                        else "No clear one-for-one target; consider staff shuffle."
                    ),
                    "priority_value": 4.0 + max(row["projection_pitcher_score"] - replace_score, 0.0),
                }
            )

            exit_type = self._recommended_pitcher_exit_type(replace_row)
            if replace_row is not None and replace_name and replace_name not in pitcher_exit_names and exit_type:
                pitcher_exit_names.add(replace_name)
                moves.append(
                    {
                        "move_type": exit_type,
                        "player_name": replace_name,
                        "reason": f"Make room for {row['player_name']}",
                        "score": replace_score,
                        "possible_replace": row["player_name"],
                        "pos_bucket": "P",
                        "replace_bucket": "P",
                        "score_gap": row["projection_pitcher_score"] - replace_score,
                        "replace_score": row["projection_pitcher_score"],
                        "likely_casualty": replace_name,
                        "casualty_score": replace_score,
                        "roster_note": (
                            f"{replace_name} is the clearest current staff casualty if {row['player_name']} is promoted."
                        ),
                        "priority_value": 3.0 + max(row["projection_pitcher_score"] - replace_score, 0.0),
                    }
                )

        if not aaa_hitters.empty:
            top_aaa_hitter_score = float(
                pd.to_numeric(
                    aaa_hitters.loc[
                        aaa_hitters["is_hitter"] & ~aaa_hitters["injured_flag"] & (aaa_hitters["pa_val"] >= 30),
                        "projection_hitter_score",
                    ],
                    errors="coerce",
                ).max()
            )
            if pd.isna(top_aaa_hitter_score):
                top_aaa_hitter_score = 0.0
        else:
            top_aaa_hitter_score = 0.0
        if promote_hitters.empty and not mlb_weak_hitters.empty:
            weakest_hitter = mlb_weak_hitters.sort_values("replacement_target_score", ascending=True).iloc[0]
            weakest_hitter_score = self._num(weakest_hitter, "overall_hitter_score")
            if top_aaa_hitter_score <= weakest_hitter_score + 0.35:
                moves.append(
                    {
                        "move_type": "ACQUIRE HITTER",
                        "player_name": self._acquire_hitter_profile(weakest_hitter),
                        "reason": "Internal promotion options are not strong enough",
                        "score": weakest_hitter_score + 0.75,
                        "possible_replace": weakest_hitter["player_name"],
                        "pos_bucket": self._pos(weakest_hitter),
                        "replace_bucket": self._pos(weakest_hitter),
                        "score_gap": (weakest_hitter_score + 0.75) - weakest_hitter_score,
                        "replace_score": weakest_hitter_score,
                        "likely_casualty": weakest_hitter["player_name"],
                        "casualty_score": weakest_hitter_score,
                        "roster_note": (
                            f"The club's weakest current hitter spot is {weakest_hitter['player_name']}, "
                            "and the best AAA alternative does not project as a clear upgrade."
                        ),
                        "priority_value": 2.25,
                    }
                )

        if not aaa_pitchers.empty:
            top_aaa_pitcher_score = float(
                pd.to_numeric(
                    aaa_pitchers.loc[
                        aaa_pitchers["is_pitcher"] & ~aaa_pitchers["injured_flag"] & (aaa_pitchers["ip_val"] >= 10),
                        "projection_pitcher_score",
                    ],
                    errors="coerce",
                ).max()
            )
            if pd.isna(top_aaa_pitcher_score):
                top_aaa_pitcher_score = 0.0
        else:
            top_aaa_pitcher_score = 0.0
        if promote_pitchers.empty and not mlb_weak_pitchers.empty:
            weakest_pitcher = mlb_weak_pitchers.iloc[0]
            weakest_pitcher_score = self._num(weakest_pitcher, "score")
            if top_aaa_pitcher_score <= weakest_pitcher_score + 0.35:
                moves.append(
                    {
                        "move_type": "ACQUIRE PITCHER",
                        "player_name": self._acquire_pitcher_profile(weakest_pitcher),
                        "reason": "Internal promotion options are not strong enough",
                        "score": weakest_pitcher_score + 0.75,
                        "possible_replace": weakest_pitcher["player_name"],
                        "pos_bucket": "P",
                        "replace_bucket": "P",
                        "score_gap": (weakest_pitcher_score + 0.75) - weakest_pitcher_score,
                        "replace_score": weakest_pitcher_score,
                        "likely_casualty": weakest_pitcher["player_name"],
                        "casualty_score": weakest_pitcher_score,
                        "roster_note": (
                            f"The club's weakest current pitcher is {weakest_pitcher['player_name']}, "
                            "and the best AAA arm does not project as a clear upgrade."
                        ),
                        "priority_value": 2.2,
                    }
                )

        moves_df = pd.DataFrame(moves)
        if not moves_df.empty:
            moves_df = moves_df.sort_values(["priority_value", "score_gap"], ascending=[False, False]).reset_index(drop=True)
            moves_df = moves_df.drop(columns=["priority_value"], errors="ignore")
        return aaa_hitters, aaa_pitchers, moves_df
