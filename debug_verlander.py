#!/usr/bin/env python3
import os
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, ".")

from src.dashboard import DashboardGenerator
from src.data_processing import MySqlRepository


def _fmt(v: float) -> str:
    return f"{float(v):.4f}"


def _first_value(frame: pd.DataFrame, col: str, default: float = 0.0) -> float:
    if col not in frame.columns:
        return default
    value = frame.iloc[0][col]
    if value is None or str(value) in ("", "nan", "None"):
        return default
    return float(value)


db_url = os.environ.get("OOTP_DB_URL", "mysql+pymysql://root@127.0.0.1:3306/ootp_db")
print(f"Connecting to database: {db_url.split('@')[1] if '@' in db_url else db_url}")

try:
    repository = MySqlRepository(connection_url=db_url)
    generator = DashboardGenerator(
        data_dir=Path("src/data"),
        out_dir=Path("output"),
        repository=repository,
    )

    # Build computed frames without writing output files.
    generator.build_outputs()
    frames = getattr(generator, "_latest_frames", {})

    candidates: list[tuple[str, pd.DataFrame]] = []
    for key in ("mlb_pitchers", "aaa_pitchers", "mlb_hitters", "aaa_hitters"):
        frame = frames.get(key, pd.DataFrame())
        if frame.empty or "player_name" not in frame.columns:
            continue
        hit = frame[frame["player_name"].astype(str).str.contains("Verlander", case=False, na=False)]
        if not hit.empty:
            candidates.append((key, hit))

    if not candidates:
        print("Verlander not found in computed team frames.")
        sys.exit(0)

    for key, hit in candidates:
        row = hit.iloc[[0]].copy()
        print("\n" + "=" * 72)
        print(f"Frame: {key}")
        print(f"Player: {row.iloc[0].get('player_name', 'Unknown')}")

        cols = [
            "age_val",
            "age_bonus",
            "ip_val",
            "gs_val",
            "results_pitcher_score",
            "results_pitcher_score_regressed",
            "ratings_pitcher_now",
            "ratings_pitcher_future",
            "ratings_pitcher_now_component",
            "ratings_pitcher_future_component",
            "command_dominance_component",
            "contact_management_component",
            "durability_component",
            "score",
            "projection_pitcher_score",
            "overall_hitter_score",
            "projection_hitter_score",
        ]
        for col in cols:
            if col in row.columns:
                print(f"{col}: {row.iloc[0][col]}")

        if "projection_pitcher_score" in row.columns and "score" in row.columns:
            results = _first_value(row, "results_pitcher_score_regressed")
            now = _first_value(row, "ratings_pitcher_now_component")
            future = _first_value(row, "ratings_pitcher_future_component")
            age_bonus = _first_value(row, "age_bonus")
            command = _first_value(row, "command_dominance_component")
            contact = _first_value(row, "contact_management_component")
            durability = _first_value(row, "durability_component")
            current_score = _first_value(row, "score")
            projection_score = _first_value(row, "projection_pitcher_score")

            proj_calc = (
                results * 0.50
                + now * 0.22
                + future * 0.24
                + age_bonus * 0.30
                + command * 0.20
                + contact * 0.14
                + durability * 0.10
            )
            baseline = _first_value(row, "score_baseline_offset", 0.0)

            print("\nProjection score contribution breakdown:")
            print(f"results_regressed * 0.50: {_fmt(results * 0.50)}")
            print(f"ratings_now * 0.22: {_fmt(now * 0.22)}")
            print(f"ratings_future * 0.24: {_fmt(future * 0.24)}")
            print(f"age_bonus * 0.30: {_fmt(age_bonus * 0.30)}")
            print(f"command * 0.20: {_fmt(command * 0.20)}")
            print(f"contact * 0.14: {_fmt(contact * 0.14)}")
            print(f"durability * 0.10: {_fmt(durability * 0.10)}")
            print(f"baseline offset: {_fmt(baseline)}")
            print(f"projection (calculated, pre-baseline): {_fmt(proj_calc)}")
            print(f"projection (calculated, final): {_fmt(proj_calc + baseline)}")
            print(f"projection (stored): {_fmt(projection_score)}")
            print(f"current score: {_fmt(current_score)}")
            if abs(current_score) > 1e-9:
                print(f"projection/current ratio: {_fmt(projection_score / current_score)}")

except Exception as e:
    msg = str(e)
    print(f"Error: {msg}")
    if "cryptography" in msg and ("sha256_password" in msg or "caching_sha2_password" in msg):
        print("\nMySQL 8 auth requires the 'cryptography' package for PyMySQL.")
        print("Install with one of:")
        print("  python -m pip install cryptography")
        print("  conda install cryptography")
        print("Then rerun this script.")
    else:
        print("\nTips:")
        print("- Ensure OOTP_DB_URL has no password if root has none, e.g. mysql+pymysql://root@127.0.0.1:3306/ootp_db")
        print("- If you previously exported a URL with :password, overwrite it in this shell before rerunning")
