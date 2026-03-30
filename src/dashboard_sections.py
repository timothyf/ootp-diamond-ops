from __future__ import annotations

import pandas as pd


POSITION_BUCKET_LABELS = {
    "C": "catcher",
    "SS": "shortstop",
    "2B": "second base",
    "3B": "third base",
    "1B": "first base",
    "CF": "center field",
    "COF": "corner outfield",
    "DH": "designated hitter",
}

POSITION_BUCKET_FALLBACKS = {
    "C": ["C"],
    "SS": ["SS", "2B"],
    "2B": ["2B", "SS", "3B"],
    "3B": ["3B", "1B", "2B"],
    "1B": ["1B", "3B", "DH"],
    "CF": ["CF", "COF"],
    "COF": ["COF", "CF", "DH"],
    "DH": ["DH", "1B", "COF"],
}


def _healthy_hitters(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()
    hitters = df.loc[df["is_hitter"] & ~df["injured_flag"] & (df["pa_val"] > 0)].copy()
    if "status" in hitters.columns:
        active_mask = hitters["status"].fillna("").astype(str).str.strip()
        hitters = hitters.loc[active_mask.eq("Active") | active_mask.eq("")]
    return hitters


def _healthy_pitchers(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()
    return df.loc[df["is_pitcher"] & ~df["injured_flag"] & (df["ip_val"] > 0)].copy()


def _top_bucket_candidate(df: pd.DataFrame, bucket: str, score_col: str) -> pd.Series | None:
    if df.empty:
        return None
    for search_bucket in POSITION_BUCKET_FALLBACKS.get(bucket, [bucket]):
        pool = df.loc[df["pos_bucket"] == search_bucket].sort_values(score_col, ascending=False)
        if not pool.empty:
            return pool.iloc[0]
    return None


def _format_age(value: object) -> str:
    age = pd.to_numeric(pd.Series([value]), errors="coerce").fillna(0).iloc[0]
    return "?" if age <= 0 else str(int(round(float(age))))


def _format_hand(value: object) -> str:
    hand = str(value).strip().upper()
    return hand if hand else "?"


def _numeric_series(df: pd.DataFrame, column: str) -> pd.Series:
    if column in df.columns:
        return pd.to_numeric(df[column], errors="coerce").fillna(0)
    return pd.Series(0.0, index=df.index, dtype=float)


def _format_hitter_option(row: pd.Series | None, score_col: str) -> str:
    if row is None:
        return "No healthy internal option"
    score = pd.to_numeric(pd.Series([row.get(score_col)]), errors="coerce").fillna(0).iloc[0]
    ops = pd.to_numeric(pd.Series([row.get("ops_val", row.get("ops"))]), errors="coerce").fillna(0).iloc[0]
    return (
        f'{row.get("player_name", "")} '
        f'({score:.2f} score, {ops:.3f} OPS, age {_format_age(row.get("age_val"))}, {_format_hand(row.get("bats"))}-bat)'
    )


def _format_pitcher_option(row: pd.Series | None, score_col: str) -> str:
    if row is None:
        return "No healthy internal option"
    score = pd.to_numeric(pd.Series([row.get(score_col)]), errors="coerce").fillna(0).iloc[0]
    era = pd.to_numeric(pd.Series([row.get("era_val", row.get("era"))]), errors="coerce").fillna(0).iloc[0]
    return (
        f'{row.get("player_name", "")} '
        f'({score:.2f} score, {era:.2f} ERA, age {_format_age(row.get("age_val"))}, throws {_format_hand(row.get("throws"))})'
    )


def build_team_needs(
    mlb_hitters: pd.DataFrame,
    aaa_hitters: pd.DataFrame,
    mlb_pitchers: pd.DataFrame,
    aaa_pitchers: pd.DataFrame,
) -> pd.DataFrame:
    mlb_hitters_healthy = _healthy_hitters(mlb_hitters)
    aaa_hitters_healthy = _healthy_hitters(aaa_hitters)
    mlb_pitchers_healthy = _healthy_pitchers(mlb_pitchers)
    aaa_pitchers_healthy = _healthy_pitchers(aaa_pitchers)

    needs: list[dict[str, object]] = []

    hitter_baseline = (
        pd.to_numeric(mlb_hitters_healthy.get("overall_hitter_score"), errors="coerce").fillna(0).median()
        if not mlb_hitters_healthy.empty
        else 0.0
    )
    aaa_hitter_baseline = (
        pd.to_numeric(aaa_hitters_healthy.get("projection_hitter_score"), errors="coerce").fillna(0).median()
        if not aaa_hitters_healthy.empty
        else 0.0
    )

    for bucket in ["C", "SS", "CF", "3B", "1B", "COF"]:
        mlb_row = _top_bucket_candidate(mlb_hitters_healthy, bucket, "overall_hitter_score")
        aaa_row = _top_bucket_candidate(aaa_hitters_healthy, bucket, "projection_hitter_score")
        if mlb_row is None:
            continue

        mlb_score = float(pd.to_numeric(pd.Series([mlb_row.get("overall_hitter_score")]), errors="coerce").fillna(0).iloc[0])
        aaa_score = float(pd.to_numeric(pd.Series([aaa_row.get("projection_hitter_score")]), errors="coerce").fillna(0).iloc[0]) if aaa_row is not None else 0.0
        age_risk = 0.7 if pd.to_numeric(pd.Series([mlb_row.get("age_val")]), errors="coerce").fillna(0).iloc[0] >= 31 else 0.0
        need_score = max(0.0, hitter_baseline - mlb_score) + max(0.0, aaa_hitter_baseline - aaa_score) * 0.8 + age_risk

        if need_score < 0.75:
            continue

        desired_side = ""
        if bucket in {"1B", "COF"}:
            bats = _format_hand(mlb_row.get("bats"))
            if bats == "R":
                desired_side = " Prefer a left-handed or switch-hitting target."
            elif bats == "L":
                desired_side = " Prefer a right-handed or switch-hitting target."

        needs.append(
            {
                "priority_value": round(need_score, 2),
                "priority": "High" if need_score >= 2.0 else "Medium",
                "area": POSITION_BUCKET_LABELS.get(bucket, bucket).title(),
                "need": f"Upgrade or deepen {POSITION_BUCKET_LABELS.get(bucket, bucket)}",
                "why": (
                    f"Best healthy MLB option: {_format_hitter_option(mlb_row, 'overall_hitter_score')}. "
                    f"Best AAA fallback: {_format_hitter_option(aaa_row, 'projection_hitter_score')}."
                ),
                "target_profile": (
                    f"Look for a {'younger' if bucket in {'C', 'SS', 'CF'} else 'bat-first'} "
                    f"{POSITION_BUCKET_LABELS.get(bucket, bucket)} option with at least average current ratings and an above-current organizational score.{desired_side}"
                ).strip(),
                "internal_options": ", ".join(
                    [
                        item
                        for item in [
                            str(aaa_row.get("player_name", "")).strip() if aaa_row is not None else "",
                            str(mlb_row.get("player_name", "")).strip(),
                        ]
                        if item
                    ]
                ),
            }
        )

    rotation_pool = mlb_pitchers_healthy.sort_values("rotation_score", ascending=False).copy()
    starters = rotation_pool.loc[rotation_pool["true_starter_flag"]].head(5).copy()
    depth = rotation_pool.loc[~rotation_pool["player_name"].isin(starters["player_name"]) & (rotation_pool["true_starter_flag"] | rotation_pool["swingman_flag"])].copy()
    fifth = starters.iloc[-1] if len(starters) >= 5 else (starters.iloc[-1] if not starters.empty else None)
    next_starter = depth.iloc[0] if not depth.empty else None
    pitcher_baseline = (
        pd.to_numeric(rotation_pool.get("rotation_score"), errors="coerce").fillna(0).median()
        if not rotation_pool.empty
        else 0.0
    )
    fifth_score = float(pd.to_numeric(pd.Series([fifth.get("rotation_score")]), errors="coerce").fillna(0).iloc[0]) if fifth is not None else 0.0
    next_score = float(pd.to_numeric(pd.Series([next_starter.get("rotation_score")]), errors="coerce").fillna(0).iloc[0]) if next_starter is not None else 0.0
    rotation_need_score = max(0.0, pitcher_baseline - fifth_score) + max(0.0, 9.5 - next_score)
    if rotation_need_score >= 0.5:
        needs.append(
            {
                "priority_value": round(rotation_need_score, 2),
                "priority": "High" if rotation_need_score >= 2.0 else "Medium",
                "area": "Rotation",
                "need": "Add back-end starter or sixth-starter depth",
                "why": (
                    f"Current back-end anchor: {_format_pitcher_option(fifth, 'rotation_score')}. "
                    f"Next healthy depth arm: {_format_pitcher_option(next_starter, 'rotation_score')}."
                ),
                "target_profile": (
                    "Look for a durable starter with 55+ stamina, credible strike-throwing, and enough current value "
                    "to stabilize the fifth spot or cover injuries without a major drop-off."
                ),
                "internal_options": ", ".join(
                    [
                        item
                        for item in [
                            str(next_starter.get("player_name", "")).strip() if next_starter is not None else "",
                            str(_top_bucket_candidate(aaa_pitchers_healthy.assign(pos_bucket='P'), 'P', 'projection_pitcher_score').get("player_name", "")).strip()
                            if not aaa_pitchers_healthy.empty
                            else "",
                        ]
                        if item
                    ]
                ),
            }
        )

    bullpen = mlb_pitchers_healthy.loc[mlb_pitchers_healthy["true_reliever_flag"]].sort_values("bullpen_score", ascending=False).copy()
    top_bullpen = bullpen.head(4)
    lefty_count = int(top_bullpen["throws"].fillna("").astype(str).str.upper().isin(["L", "LEFT"]).sum()) if not top_bullpen.empty else 0
    leverage_arm = top_bullpen.iloc[-1] if len(top_bullpen) >= 4 else (top_bullpen.iloc[-1] if not top_bullpen.empty else None)
    next_relief = bullpen.iloc[4] if len(bullpen) >= 5 else None
    bullpen_baseline = (
        pd.to_numeric(bullpen.get("bullpen_score"), errors="coerce").fillna(0).median()
        if not bullpen.empty
        else 0.0
    )
    leverage_score = float(pd.to_numeric(pd.Series([leverage_arm.get("bullpen_score")]), errors="coerce").fillna(0).iloc[0]) if leverage_arm is not None else 0.0
    bullpen_need_score = max(0.0, bullpen_baseline - leverage_score) + (0.8 if lefty_count == 0 else 0.3 if lefty_count == 1 else 0.0)
    if bullpen_need_score >= 0.5:
        need_name = "Add left-handed leverage relief" if lefty_count <= 1 else "Add another leverage reliever"
        target_profile = (
            "Look for a left-handed reliever with swing-and-miss stuff and late-inning viability."
            if lefty_count <= 1
            else "Look for another leverage arm with enough stuff and control to protect late innings."
        )
        needs.append(
            {
                "priority_value": round(bullpen_need_score, 2),
                "priority": "High" if bullpen_need_score >= 1.8 else "Medium",
                "area": "Bullpen",
                "need": need_name,
                "why": (
                    f"Current leverage group thins out quickly after {_format_pitcher_option(leverage_arm, 'bullpen_score')}. "
                    f"Next option: {_format_pitcher_option(next_relief, 'bullpen_score')}. "
                    f"Top four bullpen arms include {lefty_count} left-handed option(s)."
                ),
                "target_profile": target_profile,
                "internal_options": ", ".join(
                    [
                        item
                        for item in [
                            str(next_relief.get("player_name", "")).strip() if next_relief is not None else "",
                            str(
                                aaa_pitchers_healthy.loc[
                                    aaa_pitchers_healthy["throws"].fillna("").astype(str).str.upper().isin(["L", "LEFT"])
                                ]
                                .sort_values("projection_pitcher_score", ascending=False)
                                .head(1)["player_name"]
                                .astype(str)
                                .tolist()[0]
                            ).strip()
                            if lefty_count <= 1
                            and not aaa_pitchers_healthy.loc[
                                aaa_pitchers_healthy["throws"].fillna("").astype(str).str.upper().isin(["L", "LEFT"])
                            ].empty
                            else "",
                        ]
                        if item
                    ]
                ),
            }
        )

    corner_mlb = mlb_hitters_healthy.loc[mlb_hitters_healthy["pos_bucket"].isin(["1B", "COF", "DH"])].copy()
    corner_aaa = aaa_hitters_healthy.loc[aaa_hitters_healthy["pos_bucket"].isin(["1B", "COF", "DH"])].copy()
    if not corner_mlb.empty:
        rhp_score = float(_numeric_series(corner_mlb, "select_score_rhp").sort_values(ascending=False).head(3).mean())
        lhp_score = float(_numeric_series(corner_mlb, "select_score_lhp").sort_values(ascending=False).head(3).mean())
        split_gap = abs(rhp_score - lhp_score)
        if split_gap >= 0.6:
            needs.append(
                {
                    "priority_value": round(split_gap, 2),
                    "priority": "Medium",
                    "area": "Bench / Platoon",
                    "need": "Add a matchup bat for the short side of the corner mix",
                    "why": (
                        f"Current corner group scores better against {'right-handed' if rhp_score > lhp_score else 'left-handed'} pitching "
                        f"({max(rhp_score, lhp_score):.2f}) than the opposite side ({min(rhp_score, lhp_score):.2f}). "
                        f"Best AAA corner projection: {_format_hitter_option(corner_aaa.sort_values('projection_hitter_score', ascending=False).iloc[0] if not corner_aaa.empty else None, 'projection_hitter_score')}."
                    ),
                    "target_profile": (
                        f"Look for a {'right-handed' if rhp_score > lhp_score else 'left-handed'} bat who can handle a corner role or DH and raise the club's weaker platoon side."
                    ),
                    "internal_options": ", ".join(corner_aaa.sort_values("projection_hitter_score", ascending=False).head(2)["player_name"].astype(str).tolist()),
                }
            )

    if not needs:
        return pd.DataFrame(
            [
                {
                    "priority": "Monitor",
                    "area": "Roster",
                    "need": "No obvious short-term acquisition gap",
                    "why": "Current MLB contributors and AAA depth look balanced across the major roster buckets.",
                    "target_profile": "Continue monitoring for opportunistic upgrades rather than a forced need buy.",
                    "internal_options": "",
                }
            ]
        )

    needs_df = pd.DataFrame(needs).sort_values(["priority_value", "priority"], ascending=[False, True]).reset_index(drop=True)
    return needs_df.drop(columns=["priority_value"], errors="ignore")


def build_hitter_toggle_dashboard(
    df: pd.DataFrame,
    score_col: str,
    include_potential: bool = False,
) -> tuple[pd.DataFrame, dict[str, list[str]], dict[str, str]]:
    int_stats_cols = ["g", "stats_pa", "ab", "h", "2b", "3b", "hr", "rbi", "r", "bb", "k", "sb", "cs"]
    current_cols = [
        "cv_pa",
        "cv_obp",
        "cv_slg",
        "cv_ops",
        "contact_now",
        "power_now",
        "eye_now",
    ]
    if include_potential:
        current_cols.extend(["contact_pot", "power_pot", "eye_pot"])
    current_cols.extend(["score", "projection_score", "injury_text"])
    stats_cols = [
        "g",
        "stats_pa",
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
        "stats_obp",
        "stats_slg",
        "stats_ops",
        "war",
    ]
    labels = {
        "player_name": "player_name",
        "primary_position": "pos",
        "cv_pa": "pa",
        "cv_obp": "obp",
        "cv_slg": "slg",
        "cv_ops": "ops",
        "contact_now": "contact_now",
        "power_now": "power_now",
        "eye_now": "eye_now",
        "contact_pot": "contact_pot",
        "power_pot": "power_pot",
        "eye_pot": "eye_pot",
        "score": "score",
        "projection_score": "proj_score",
        "g": "g",
        "stats_pa": "pa",
        "ab": "ab",
        "h": "h",
        "2b": "2b",
        "3b": "3b",
        "hr": "hr",
        "rbi": "rbi",
        "r": "r",
        "bb": "bb",
        "k": "k",
        "sb": "sb",
        "cs": "cs",
        "avg": "avg",
        "stats_obp": "obp",
        "stats_slg": "slg",
        "stats_ops": "ops",
        "war": "war",
        "injury_text": "injury_text",
    }
    display_columns = ["player_name", "primary_position", *current_cols, *stats_cols]
    if df.empty:
        return pd.DataFrame(columns=display_columns), {"current": current_cols, "stats": stats_cols}, labels
    display = (
        df.loc[df["is_hitter"] & (df["pa_val"] > 0)]
        .sort_values(score_col, ascending=False)
        .assign(
            cv_pa=lambda x: x["pa_val"].fillna(0).round().astype(int),
            stats_pa=lambda x: x["pa"].fillna(0).round().astype(int),
            cv_obp=lambda x: x["obp_val"],
            cv_slg=lambda x: x["slg_val"],
            cv_ops=lambda x: x["ops_val"],
            stats_obp=lambda x: x["obp"],
            stats_slg=lambda x: x["slg"],
            stats_ops=lambda x: x["ops"],
            score=lambda x: x[score_col],
            projection_score=lambda x: x["projection_hitter_score"],
        )[display_columns]
        .head(15)
        .copy()
    )
    for col in int_stats_cols:
        if col in display.columns:
            display[col] = pd.to_numeric(display[col], errors="coerce").fillna(0).round().astype(int)
    return display, {"current": current_cols, "stats": stats_cols}, labels


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


def build_pitcher_toggle_dashboard(
    df: pd.DataFrame,
    score_col: str,
    include_potential: bool = False,
) -> tuple[pd.DataFrame, dict[str, list[str]], dict[str, str]]:
    int_stats_cols = ["g", "gs", "w", "l", "sv", "hld", "ha", "hr", "er", "bb", "k"]
    current_cols = [
        "cv_ip",
        "cv_era",
        "cv_fip",
        "cv_whip",
        "stuff_now",
        "movement_now",
        "control_now",
    ]
    if include_potential:
        current_cols.extend(["stuff_pot", "movement_pot", "control_pot"])
    current_cols.extend(["score", "projection_score", "injury_text"])
    stats_cols = [
        "g",
        "gs",
        "w",
        "l",
        "sv",
        "hld",
        "stats_ip",
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
    ]
    labels = {
        "player_name": "player_name",
        "primary_position": "pos",
        "cv_ip": "ip",
        "cv_era": "era",
        "cv_fip": "fip",
        "cv_whip": "whip",
        "stuff_now": "stuff_now",
        "movement_now": "movement_now",
        "control_now": "control_now",
        "stuff_pot": "stuff_pot",
        "movement_pot": "movement_pot",
        "control_pot": "control_pot",
        "score": "score",
        "g": "g",
        "gs": "gs",
        "w": "w",
        "l": "l",
        "sv": "sv",
        "hld": "hld",
        "stats_ip": "ip",
        "ha": "ha",
        "hr": "hr",
        "er": "er",
        "bb": "bb",
        "k": "k",
        "era": "era",
        "fip": "fip",
        "whip": "whip",
        "k_9": "k_9",
        "bb_9": "bb_9",
        "hr_9": "hr_9",
        "war": "war",
        "projection_score": "proj_score",
        "injury_text": "injury_text",
    }
    display_columns = ["player_name", "primary_position", *current_cols, *stats_cols]
    if df.empty:
        return pd.DataFrame(columns=display_columns), {"current": current_cols, "stats": stats_cols}, labels
    display = (
        df.loc[df["is_pitcher"] & (df["ip_val"] > 0)]
        .sort_values(score_col, ascending=False)
        .assign(
            cv_ip=lambda x: x["ip_val"],
            cv_era=lambda x: x["era_val"],
            cv_fip=lambda x: x["fip_val"],
            cv_whip=lambda x: x["whip_val"],
            stats_ip=lambda x: x["ip"],
            score=lambda x: x[score_col],
            projection_score=lambda x: x["projection_pitcher_score"],
        )[display_columns]
        .head(15)
        .copy()
    )
    for col in int_stats_cols:
        if col in display.columns:
            display[col] = pd.to_numeric(display[col], errors="coerce").fillna(0).round().astype(int)
    return display, {"current": current_cols, "stats": stats_cols}, labels


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
