from __future__ import annotations

from itertools import permutations

import numpy as np
import pandas as pd


class LineupPlanner:
    SIDE_EDGE_BONUS = 0.10

    @staticmethod
    def choose_best(pool: pd.DataFrame, flag_col: str, score_col: str, used_names: set[str]) -> pd.Series | None:
        subset = pool.loc[pool[flag_col] & ~pool["player_name"].isin(used_names)].sort_values(score_col, ascending=False)
        if subset.empty:
            return None
        return subset.iloc[0]

    def choose_best_with_fallback(
        self, pool: pd.DataFrame, flags: list[str], score_col: str, used_names: set[str]
    ) -> pd.Series | None:
        for flag in flags:
            row = self.choose_best(pool, flag, score_col, used_names)
            if row is not None:
                return row
        return None

    @staticmethod
    def choose_anchor(remaining: pd.DataFrame, eligibility_col: str, score_col: str):
        eligible = remaining.loc[remaining[eligibility_col]]
        if not eligible.empty:
            return eligible[score_col].idxmax()
        return remaining[score_col].idxmax()

    def choose_baseline_lineup(self, pool: pd.DataFrame) -> pd.DataFrame:
        used = set()
        chosen = []
        plan = [
            ("C", ["is_c"]),
            ("SS", ["is_ss"]),
            ("2B", ["is_2b", "is_ss"]),
            ("CF", ["is_cf", "is_lf", "is_rf"]),
            ("3B", ["is_3b", "is_1b", "is_2b"]),
            ("1B", ["is_1b", "is_3b"]),
            ("LF", ["is_lf", "is_rf", "is_cf"]),
            ("RF", ["is_rf", "is_lf", "is_cf"]),
        ]
        for label, flags in plan:
            row = self.choose_best_with_fallback(pool, flags, "overall_hitter_score", used)
            if row is not None:
                used.add(row["player_name"])
                chosen.append(self._lineup_row(label, row, row["overall_hitter_score"]))

        dh_pool = pool.loc[~pool["player_name"].isin(used)].copy()
        dh_priority = dh_pool.loc[dh_pool["is_1b"] | dh_pool["is_lf"] | dh_pool["is_rf"] | dh_pool["is_3b"]].copy()
        if dh_priority.empty:
            dh_priority = dh_pool.copy()
        if not dh_priority.empty:
            dh_priority["dh_base_score"] = dh_priority["dh_fit_score"] + dh_priority["overall_hitter_score"]
            row = dh_priority.sort_values("dh_base_score", ascending=False).iloc[0]
            chosen.append(self._lineup_row("DH", row, row["dh_base_score"]))
        return pd.DataFrame(chosen)

    @staticmethod
    def _lineup_row(position: str, row: pd.Series, select_score: float) -> dict:
        return {
            "position": position,
            "player_name": row["player_name"],
            "obp": row["obp_val"],
            "slg": row["slg_val"],
            "select_score": select_score,
            "leadoff_score": row["leadoff_score"],
            "two_hole_score": row["two_hole_score"],
            "three_hole_score": row["three_hole_score"],
            "cleanup_score": row["cleanup_score"],
            "overall_hitter_score": row["overall_hitter_score"],
            "leadoff_eligible": row["leadoff_eligible"],
            "three_hole_eligible": row["three_hole_eligible"],
            "cleanup_eligible": row["cleanup_eligible"],
        }

    @staticmethod
    def slot_filter(df: pd.DataFrame, slot: str) -> pd.Series:
        if slot == "1B":
            return df["is_1b"] | df["is_3b"]
        if slot == "LF":
            return df["is_lf"] | df["is_rf"] | df["is_cf"]
        if slot == "RF":
            return df["is_rf"] | df["is_lf"] | df["is_cf"]
        if slot == "DH":
            return df["is_1b"] | df["is_3b"] | df["is_lf"] | df["is_rf"]
        return pd.Series(False, index=df.index)

    def side_edge_bonus(self, row: pd.Series, side: str) -> float:
        bats = str(row["bats"]).upper().strip()
        if side == "RHP" and bats in ["L", "LEFT"]:
            return self.SIDE_EDGE_BONUS
        if side == "LHP" and bats in ["R", "RIGHT"]:
            return self.SIDE_EDGE_BONUS
        if bats in ["S", "SWITCH"]:
            return self.SIDE_EDGE_BONUS / 2.0
        return 0.0

    def score_for_slot(self, row: pd.Series, slot: str, score_col: str, side: str) -> float:
        base = float(row["dh_fit_score"] + row[score_col] * 1.25) if slot == "DH" else float(row[score_col])
        if slot in {"1B", "LF", "RF", "DH"}:
            base += self.side_edge_bonus(row, side)
        return base

    @staticmethod
    def corner_slots() -> list[str]:
        return ["1B", "LF", "RF", "DH"]

    def build_corner_candidate_pool(self, pool: pd.DataFrame, core_names: set[str]) -> pd.DataFrame:
        return pool.loc[
            (~pool["player_name"].isin(core_names))
            & pool["is_hitter"]
            & (~pool["injured_flag"])
            & (pool["pa_val"] > 0)
            & (pool["is_1b"] | pool["is_3b"] | pool["is_lf"] | pool["is_rf"] | pool["is_cf"])
        ].copy()

    def build_corner_combo(self, pool: pd.DataFrame, lineup: pd.DataFrame, score_col: str, side: str, top_n: int = 12) -> dict:
        core_positions = {"C", "SS", "2B", "3B", "CF"}
        core_names = set(lineup.loc[lineup["position"].isin(core_positions), "player_name"].tolist())
        candidate_pool = self.build_corner_candidate_pool(pool, core_names).copy()

        if candidate_pool.empty:
            return {"best_assign": {}, "best_total": 0.0, "candidate_pool": candidate_pool, "ranked_combos": []}

        candidate_pool["corner_side_score"] = candidate_pool.apply(
            lambda r: max(
                self.score_for_slot(r, "1B", score_col, side),
                self.score_for_slot(r, "LF", score_col, side),
                self.score_for_slot(r, "RF", score_col, side),
                self.score_for_slot(r, "DH", score_col, side),
            ),
            axis=1,
        )

        candidate_pool = (
            candidate_pool.sort_values(["corner_side_score", "overall_hitter_score"], ascending=False)
            .drop_duplicates(subset=["player_name"])
            .head(top_n)
            .copy()
        )

        slots = self.corner_slots()
        eligible = {
            slot: candidate_pool.loc[self.slot_filter(candidate_pool, slot), "player_name"].tolist()
            for slot in slots
        }

        candidates = candidate_pool.set_index("player_name", drop=False)
        ranked_combos = []
        all_names = candidate_pool["player_name"].tolist()

        for names in permutations(all_names, 4):
            assign = dict(zip(slots, names))
            if len(set(assign.values())) < 4:
                continue

            valid = True
            total = 0.0
            detail = {}

            for slot in slots:
                name = assign[slot]
                if name not in eligible[slot]:
                    valid = False
                    break
                row = candidates.loc[name]
                slot_score = self.score_for_slot(row, slot, score_col, side)
                total += slot_score
                detail[slot] = {"player_name": name, "slot_score": float(slot_score), "bats": row["bats"]}

            if valid:
                ranked_combos.append({"total_score": float(total), "assign": assign, "detail": detail})

        ranked_combos = sorted(ranked_combos, key=lambda x: x["total_score"], reverse=True)
        if ranked_combos:
            best_assign = ranked_combos[0]["assign"]
            best_total = ranked_combos[0]["total_score"]
        else:
            best_assign = {}
            best_total = 0.0

        return {
            "best_assign": best_assign,
            "best_total": best_total,
            "candidate_pool": candidate_pool,
            "ranked_combos": ranked_combos[:10],
        }

    def optimize_corner_group(self, pool: pd.DataFrame, lineup: pd.DataFrame, score_col: str, side: str) -> pd.DataFrame:
        combo_result = self.build_corner_combo(pool, lineup, score_col, side, top_n=12)
        best_assign = combo_result["best_assign"]

        if not best_assign:
            return lineup

        for slot in self.corner_slots():
            chosen_name = best_assign.get(slot)
            if not chosen_name:
                continue

            row = pool.loc[pool["player_name"] == chosen_name]
            if row.empty:
                continue
            row = row.iloc[0]

            lineup.loc[
                lineup["position"] == slot,
                [
                    "player_name",
                    "obp",
                    "slg",
                    "select_score",
                    "leadoff_score",
                    "two_hole_score",
                    "three_hole_score",
                    "cleanup_score",
                    "overall_hitter_score",
                    "leadoff_eligible",
                    "three_hole_eligible",
                    "cleanup_eligible",
                ],
            ] = [
                row["player_name"],
                row["obp_val"],
                row["slg_val"],
                self.score_for_slot(row, slot, score_col, side),
                row["leadoff_score"],
                row["two_hole_score"],
                row["three_hole_score"],
                row["cleanup_score"],
                row["overall_hitter_score"],
                row["leadoff_eligible"],
                row["three_hole_eligible"],
                row["cleanup_eligible"],
            ]

        return lineup

    def build_lineup(self, df: pd.DataFrame, vs: str = "RHP") -> pd.DataFrame:
        side = vs.upper()
        score_col = "select_score_rhp" if side == "RHP" else "select_score_lhp"

        pool = df.loc[(~df["injured_flag"]) & df["is_hitter"] & (df["pa_val"] > 0)].copy()
        if pool.empty:
            return pd.DataFrame()

        lineup = self.choose_baseline_lineup(pool)
        if lineup.empty:
            return lineup

        lineup = self.optimize_corner_group(pool, lineup, score_col, side)

        remaining = lineup.copy()
        order_idx = []
        idx1 = self.choose_anchor(remaining, "leadoff_eligible", "leadoff_score")
        order_idx.append(idx1)
        remaining = remaining.drop(index=idx1)
        idx2 = self.choose_anchor(remaining, "three_hole_eligible", "two_hole_score")
        order_idx.append(idx2)
        remaining = remaining.drop(index=idx2)
        idx3 = self.choose_anchor(remaining, "three_hole_eligible", "three_hole_score")
        order_idx.append(idx3)
        remaining = remaining.drop(index=idx3)
        idx4 = self.choose_anchor(remaining, "cleanup_eligible", "cleanup_score")
        order_idx.append(idx4)
        remaining = remaining.drop(index=idx4)

        if not remaining.empty:
            remaining = remaining.sort_values(["overall_hitter_score", "slg"], ascending=False)
            order_idx.extend(remaining.index.tolist())

        lineup = lineup.loc[order_idx].reset_index(drop=True)
        lineup.insert(0, "slot", np.arange(1, len(lineup) + 1))
        lineup["score"] = lineup["select_score"]
        return lineup[["slot", "position", "player_name", "obp", "slg", "score"]]

    @staticmethod
    def build_rotation(df: pd.DataFrame) -> pd.DataFrame:
        pool = df.loc[df["is_pitcher"] & ~df["injured_flag"] & (df["ip_val"] > 0)].copy()
        starters = pool.loc[pool["true_starter_flag"]].sort_values("rotation_score", ascending=False).copy()
        chosen = starters.head(5).copy()

        if len(chosen) < 5:
            used = set(chosen["player_name"].tolist())
            swingmen = pool.loc[
                pool["swingman_flag"]
                & ~pool["player_name"].isin(used)
                & (pool["gs_val"] >= 3)
                & (pool["stamina_now"] >= 55)
                & (pool["ip_val"] >= 15)
                & (pool["rotation_score"] >= 8)
            ].sort_values("rotation_score", ascending=False).copy()
            need = 5 - len(chosen)
            if need > 0 and not swingmen.empty:
                chosen = pd.concat([chosen, swingmen.head(need)], ignore_index=True)

        chosen = chosen.head(5).copy()
        if chosen.empty:
            chosen = pd.DataFrame(columns=["player_name", "ip", "era", "fip", "rotation_score"])
        else:
            chosen = chosen[["player_name", "ip_val", "era_val", "fip_val", "rotation_score"]].rename(
                columns={"ip_val": "ip", "era_val": "era", "fip_val": "fip"}
            ).reset_index(drop=True)

        while len(chosen) < 5:
            chosen.loc[len(chosen)] = ["OPEN / BULK ROLE", 0.0, 0.0, 0.0, 0.0]

        chosen.insert(0, "slot", np.arange(1, len(chosen) + 1))
        return chosen

    @staticmethod
    def build_bullpen(df: pd.DataFrame) -> pd.DataFrame:
        pool = df.loc[
            df["is_pitcher"] & ~df["injured_flag"] & (df["ip_val"] > 0) & df["true_reliever_flag"]
        ].sort_values("bullpen_score", ascending=False).copy()
        bullpen = pool[["player_name", "era_val", "fip_val", "bullpen_score"]].rename(
            columns={"era_val": "era", "fip_val": "fip"}
        ).head(7).reset_index(drop=True)
        if not bullpen.empty:
            roles = ["Closer", "Setup 1", "Setup 2", "High Leverage", "Middle Relief", "Middle Relief", "Long Relief"]
            bullpen.insert(0, "role", roles[: len(bullpen)])
        return bullpen

    @staticmethod
    def handedness_edge_text(bats: str, side: str) -> str:
        bats = str(bats).upper().strip()
        if side == "RHP":
            if bats in ["L", "LEFT"]:
                return "advantage"
            if bats in ["S", "SWITCH"]:
                return "some advantage"
            return "disadvantage"
        if bats in ["R", "RIGHT"]:
            return "advantage"
        if bats in ["S", "SWITCH"]:
            return "some advantage"
        return "disadvantage"

    def build_platoon_diagnostics(
        self, df: pd.DataFrame, lineup_rhp: pd.DataFrame, lineup_lhp: pd.DataFrame, top_n: int = 3
    ) -> pd.DataFrame:
        rows = []

        for side, lineup, score_col in [("RHP", lineup_rhp, "select_score_rhp"), ("LHP", lineup_lhp, "select_score_lhp")]:
            pool = df.loc[(~df["injured_flag"]) & df["is_hitter"] & (df["pa_val"] > 0)].copy()

            combo_result = self.build_corner_combo(pool, lineup, score_col, side, top_n=12)
            best_assign = combo_result["best_assign"]
            ranked_combos = combo_result["ranked_combos"]
            candidate_pool = combo_result["candidate_pool"]

            best_combo_total = ranked_combos[0]["total_score"] if ranked_combos else 0.0

            for slot in self.corner_slots():
                chosen_name = best_assign.get(slot, "")
                if chosen_name:
                    chosen_row = candidate_pool.loc[candidate_pool["player_name"] == chosen_name]
                    if not chosen_row.empty:
                        chosen_row = chosen_row.iloc[0]
                        chosen_score = self.score_for_slot(chosen_row, slot, score_col, side)
                        rows.append(
                            {
                                "report_type": "best_combo",
                                "side": side,
                                "slot": slot,
                                "rank": 1,
                                "player_name": chosen_name,
                                "bats": chosen_row["bats"],
                                "score": float(chosen_score),
                                "split_bonus": float(
                                    chosen_row["split_bonus_rhp"] if side == "RHP" else chosen_row["split_bonus_lhp"]
                                ),
                                "incumbent": chosen_name,
                                "handedness_edge": self.handedness_edge_text(chosen_row["bats"], side),
                                "reason_not_chosen": "Chosen in best feasible 4-player combo",
                                "combo_total_score": float(best_combo_total),
                            }
                        )

            for slot in self.corner_slots():
                incumbent_name = best_assign.get(slot, "")
                slot_pool = df.loc[
                    (~df["injured_flag"]) & df["is_hitter"] & (df["pa_val"] > 0) & self.slot_filter(df, slot)
                ].copy()

                if slot_pool.empty:
                    rows.append(
                        {
                            "report_type": "slot_candidates",
                            "side": side,
                            "slot": slot,
                            "rank": 1,
                            "player_name": "",
                            "bats": "",
                            "score": 0.0,
                            "split_bonus": 0.0,
                            "incumbent": incumbent_name,
                            "handedness_edge": "",
                            "reason_not_chosen": "No eligible candidates",
                            "combo_total_score": float(best_combo_total),
                        }
                    )
                    continue

                slot_pool["diag_score"] = slot_pool.apply(lambda r: self.score_for_slot(r, slot, score_col, side), axis=1)
                slot_pool = slot_pool.sort_values("diag_score", ascending=False).head(top_n).copy()

                used_elsewhere = {s: p for s, p in best_assign.items() if s != slot}
                used_names_elsewhere = set(used_elsewhere.values())

                for rank, (_, r) in enumerate(slot_pool.iterrows(), start=1):
                    name = r["player_name"]

                    if name == incumbent_name:
                        reason = "Chosen for this slot in best feasible combo"
                    elif name in used_names_elsewhere:
                        other_slot = next((s for s, p in used_elsewhere.items() if p == name), "")
                        reason = f"Used in best combo at {other_slot}"
                    else:
                        forced_best = None
                        for combo in ranked_combos:
                            if combo["assign"].get(slot) == name:
                                forced_best = combo
                                break

                        if forced_best is None:
                            reason = "No valid 4-player combo with this player in this slot"
                        else:
                            gap = forced_best["total_score"] - best_combo_total
                            if gap < 0:
                                reason = f"Best forced combo trails optimal by {abs(gap):.3f}"
                            else:
                                reason = "Equivalent best combo"

                    rows.append(
                        {
                            "report_type": "slot_candidates",
                            "side": side,
                            "slot": slot,
                            "rank": rank,
                            "player_name": name,
                            "bats": r["bats"],
                            "score": float(r["diag_score"]),
                            "split_bonus": float(r["split_bonus_rhp"] if side == "RHP" else r["split_bonus_lhp"]),
                            "incumbent": incumbent_name,
                            "handedness_edge": self.handedness_edge_text(r["bats"], side),
                            "reason_not_chosen": reason,
                            "combo_total_score": float(best_combo_total),
                        }
                    )

        return pd.DataFrame(rows)
