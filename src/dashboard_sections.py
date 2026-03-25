from __future__ import annotations

import pandas as pd


def build_hitter_dashboard(df: pd.DataFrame, score_col: str) -> pd.DataFrame:
    cols = [
        "player_name",
        "primary_position",
        "pa_val",
        "obp_val",
        "slg_val",
        "ops_val",
        "contact_now",
        "power_now",
        "eye_now",
        score_col,
        "injury_text",
    ]
    return (
        df.loc[df["is_hitter"] & (df["pa_val"] > 0)]
        .sort_values(score_col, ascending=False)[cols]
        .rename(
            columns={
                "pa_val": "pa",
                "obp_val": "obp",
                "slg_val": "slg",
                "ops_val": "ops",
                score_col: "score",
            }
        )
        .assign(pa=lambda x: x["pa"].fillna(0).round().astype(int))
        .head(15)
    )


def build_hitter_standard_stats(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()

    cols = [
        "player_name",
        "primary_position",
        "g",
        "pa",
        "ab",
        "h",
        "2b",
        "3b",
        "hr",
        "rbi",
        "r",
        "bb",
        "k",
        "sb",
        "cs",
        "avg",
        "obp",
        "slg",
        "ops",
        "war",
        "injury_text",
    ]
    present_cols = [c for c in cols if c in df.columns]
    stats = (
        df.loc[df["is_hitter"] & (df["pa"] > 0)]
        .sort_values(["pa", "ops"], ascending=[False, False])[present_cols]
        .copy()
    )
    int_cols = [c for c in ["g", "pa", "ab", "h", "2b", "3b", "hr", "rbi", "r", "bb", "k", "sb", "cs"] if c in stats.columns]
    for col in int_cols:
        stats[col] = stats[col].fillna(0).round().astype(int)
    return stats


def build_active_depth_chart(df: pd.DataFrame, depth_per_position: int = 4) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(
            columns=["position", "rank", "player_name", "listed_position", "bats", "throws", "pa", "ops", "score"]
        )

    active = df.loc[df["is_hitter"]].copy()
    if "status" in active.columns:
        active = active.loc[active["status"].fillna("").astype(str).str.strip().eq("Active")]
    if "injured_flag" in active.columns:
        active = active.loc[~active["injured_flag"].fillna(False)]
    active = active.drop_duplicates(subset=["player_name"])

    if active.empty:
        return pd.DataFrame(
            columns=["position", "rank", "player_name", "listed_position", "bats", "throws", "pa", "ops", "score"]
        )

    plans: list[tuple[str, list[str]]] = [
        ("C", ["is_c"]),
        ("1B", ["is_1b", "is_3b"]),
        ("2B", ["is_2b", "is_ss"]),
        ("3B", ["is_3b", "is_1b", "is_2b"]),
        ("SS", ["is_ss", "is_2b", "is_3b"]),
        ("LF", ["is_lf", "is_rf", "is_cf"]),
        ("CF", ["is_cf", "is_lf", "is_rf"]),
        ("RF", ["is_rf", "is_lf", "is_cf"]),
        ("DH", ["is_hitter"]),
    ]

    def primary_position_for_row(row: pd.Series) -> str:
        raw = str(row.get("primary_position", "")).upper()
        if "C" in raw and "CF" not in raw:
            return "C"
        if "SS" in raw:
            return "SS"
        if "2B" in raw:
            return "2B"
        if "3B" in raw:
            return "3B"
        if "1B" in raw:
            return "1B"
        if "CF" in raw:
            return "CF"
        if "LF" in raw:
            return "LF"
        if "RF" in raw:
            return "RF"
        return "DH"

    def depth_score_frame(frame: pd.DataFrame, position: str) -> pd.Series:
        base_score = pd.to_numeric(frame.get("overall_hitter_score"), errors="coerce").fillna(0)
        if position == "DH":
            return base_score + pd.to_numeric(frame.get("dh_fit_score"), errors="coerce").fillna(0)
        return base_score

    def eligible_for_position(frame: pd.DataFrame, position: str, flags: list[str]) -> pd.Series:
        if position == "DH":
            return frame["is_hitter"].fillna(False)
        return frame[flags].fillna(False).any(axis=1)

    active = active.copy()
    active["depth_primary_position"] = active.apply(primary_position_for_row, axis=1)

    starter_assignments: dict[str, str] = {}
    used_starters: set[str] = set()

    for position, flags in plans:
        primary_candidates = active.loc[
            eligible_for_position(active, position, flags)
            & active["depth_primary_position"].eq(position)
            & ~active["player_name"].isin(used_starters)
        ].copy()
        if primary_candidates.empty:
            continue
        primary_candidates["depth_score"] = depth_score_frame(primary_candidates, position)
        best_primary = primary_candidates.sort_values(["depth_score", "overall_hitter_score", "ops_val"], ascending=False).iloc[0]
        starter_assignments[position] = str(best_primary["player_name"])
        used_starters.add(str(best_primary["player_name"]))

    for position, flags in plans:
        if position in starter_assignments:
            continue
        fallback_candidates = active.loc[
            eligible_for_position(active, position, flags)
            & ~active["player_name"].isin(used_starters)
        ].copy()
        if fallback_candidates.empty:
            continue
        fallback_candidates["depth_score"] = depth_score_frame(fallback_candidates, position)
        best_fallback = fallback_candidates.sort_values(["depth_score", "overall_hitter_score", "ops_val"], ascending=False).iloc[0]
        starter_assignments[position] = str(best_fallback["player_name"])
        used_starters.add(str(best_fallback["player_name"]))

    starter_names = set(starter_assignments.values())

    rows: list[dict[str, object]] = []
    for position, flags in plans:
        candidates = active.loc[eligible_for_position(active, position, flags)].copy()
        candidates["depth_score"] = depth_score_frame(candidates, position)

        if candidates.empty:
            continue

        starter_name = starter_assignments.get(position)
        if starter_name:
            starter_row = candidates.loc[candidates["player_name"].eq(starter_name)].copy()
            remaining_rows = candidates.loc[~candidates["player_name"].eq(starter_name)].copy()
            # Keep starters from occupying backup slots at other positions.
            remaining_rows = remaining_rows.loc[~remaining_rows["player_name"].isin(starter_names)]
            remaining_rows = remaining_rows.sort_values(["depth_score", "overall_hitter_score", "ops_val"], ascending=False)
            candidates = pd.concat([starter_row, remaining_rows], ignore_index=True).head(depth_per_position)
        else:
            candidates = candidates.sort_values(["depth_score", "overall_hitter_score", "ops_val"], ascending=False).head(depth_per_position)

        for rank, (_, row) in enumerate(candidates.iterrows(), start=1):
            pa_val = pd.to_numeric(pd.Series([row.get("pa_val")]), errors="coerce").fillna(0).iloc[0]
            score_val = pd.to_numeric(pd.Series([row.get("depth_score")]), errors="coerce").fillna(0).iloc[0]
            rows.append(
                {
                    "position": position,
                    "rank": rank,
                    "player_name": row.get("player_name", ""),
                    "listed_position": row.get("primary_position", ""),
                    "bats": row.get("bats", ""),
                    "throws": row.get("throws", ""),
                    "pa": int(round(float(pa_val))),
                    "ops": pd.to_numeric(row.get("ops_val"), errors="coerce"),
                    "score": float(score_val),
                }
            )

    if not rows:
        return pd.DataFrame(
            columns=["position", "rank", "player_name", "listed_position", "bats", "throws", "pa", "ops", "score"]
        )

    depth_chart = pd.DataFrame(rows)
    depth_chart["ops"] = pd.to_numeric(depth_chart["ops"], errors="coerce").round(3)
    depth_chart["score"] = pd.to_numeric(depth_chart["score"], errors="coerce").round(2)
    return depth_chart


def build_aaa_hitter_dashboard(df: pd.DataFrame) -> pd.DataFrame:
    return (
        df.loc[df["is_hitter"] & (df["pa_val"] > 0)]
        .sort_values("projection_hitter_score", ascending=False)[
            [
                "player_name",
                "primary_position",
                "pa_val",
                "obp_val",
                "slg_val",
                "ops_val",
                "contact_now",
                "power_now",
                "eye_now",
                "contact_pot",
                "power_pot",
                "eye_pot",
                "projection_hitter_score",
                "injury_text",
            ]
        ]
        .rename(
            columns={
                "pa_val": "pa",
                "obp_val": "obp",
                "slg_val": "slg",
                "ops_val": "ops",
                "projection_hitter_score": "score",
            }
        )
        .assign(pa=lambda x: x["pa"].fillna(0).round().astype(int))
        .head(15)
    )


def build_pitcher_standard_stats(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()

    cols = [
        "player_name",
        "primary_position",
        "g",
        "gs",
        "w",
        "l",
        "sv",
        "hld",
        "ip",
        "ha",
        "hr",
        "er",
        "bb",
        "k",
        "era",
        "fip",
        "whip",
        "k_9",
        "bb_9",
        "hr_9",
        "war",
        "injury_text",
    ]
    present_cols = [c for c in cols if c in df.columns]
    stats = (
        df.loc[df["is_pitcher"] & (df["ip"] > 0)]
        .sort_values(["ip", "era"], ascending=[False, True])[present_cols]
        .copy()
    )
    int_cols = [c for c in ["g", "gs", "w", "l", "sv", "hld", "ha", "hr", "er", "bb", "k"] if c in stats.columns]
    for col in int_cols:
        stats[col] = stats[col].fillna(0).round().astype(int)
    return stats


def build_pitcher_dashboard(df: pd.DataFrame, score_col: str, include_potential: bool = False) -> pd.DataFrame:
    cols = [
        "player_name",
        "primary_position",
        "ip_val",
        "era_val",
        "fip_val",
        "whip_val",
        "stuff_now",
        "movement_now",
        "control_now",
    ]
    if include_potential:
        cols.extend(["stuff_pot", "movement_pot", "control_pot"])
    cols.extend([score_col, "injury_text"])
    return (
        df.loc[df["is_pitcher"] & (df["ip_val"] > 0)]
        .sort_values(score_col, ascending=False)[cols]
        .rename(
            columns={
                "ip_val": "ip",
                "era_val": "era",
                "fip_val": "fip",
                "whip_val": "whip",
                score_col: "score",
            }
        )
        .head(15)
    )
