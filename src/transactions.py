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
                }
            )

        promote_pitchers = aaa_pitchers.loc[
            (aaa_pitchers["is_pitcher"]) & (aaa_pitchers["recommendation"] == "PROMOTE NOW")
        ].sort_values("projection_pitcher_score", ascending=False).head(5)
        for _, row in promote_pitchers.iterrows():
            replace_name = mlb_weak_pitchers.iloc[0]["player_name"] if not mlb_weak_pitchers.empty else ""
            replace_score = mlb_weak_pitchers.iloc[0]["score"] if not mlb_weak_pitchers.empty else 0

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
                }
            )

        return aaa_hitters, aaa_pitchers, pd.DataFrame(moves)
