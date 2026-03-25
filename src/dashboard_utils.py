from __future__ import annotations

from pathlib import Path

import pandas as pd


def md_table(df: pd.DataFrame) -> str:
    if df.empty:
        return "_No rows_"
    return df.to_markdown(index=False)


def round_score_columns(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    rounded = df.copy()
    for col in rounded.columns:
        if "score" not in str(col).lower():
            continue
        numeric = pd.to_numeric(rounded[col], errors="coerce")
        if numeric.notna().any():
            rounded[col] = numeric.round(2)
    return rounded


def format_ip_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Format innings columns using MLB notation (.1/.2 for 1/3 and 2/3)."""
    if df.empty:
        return df

    formatted = df.copy()
    ip_cols = [c for c in formatted.columns if str(c).lower() in {"ip", "innings_pitched"}]
    if not ip_cols:
        return formatted

    for col in ip_cols:
        numeric = pd.to_numeric(formatted[col], errors="coerce")
        if not numeric.notna().any():
            continue

        whole = numeric.fillna(0).floordiv(1)
        frac = numeric - whole

        is_notation_frac = (
            (frac - 0.0).abs() < 1e-6
        ) | ((frac - 0.1).abs() < 1e-6) | ((frac - 0.2).abs() < 1e-6)
        is_decimal_frac = ((frac - (1.0 / 3.0)).abs() < 0.02) | ((frac - (2.0 / 3.0)).abs() < 0.02)

        mlb_frac = pd.Series(0.0, index=formatted.index)
        mlb_frac = mlb_frac.mask(((frac - 0.1).abs() < 0.02) | ((frac - (1.0 / 3.0)).abs() < 0.02), 0.1)
        mlb_frac = mlb_frac.mask(((frac - 0.2).abs() < 0.02) | ((frac - (2.0 / 3.0)).abs() < 0.02), 0.2)

        converted = (whole + mlb_frac).where(is_notation_frac | is_decimal_frac, numeric.round(1))
        formatted[col] = converted.round(1)

    return formatted


def slugify(title: str) -> str:
    return (
        title.lower()
        .replace(" - ", "_")
        .replace(" ", "_")
        .replace("/", "_")
    )


def team_name_from_filename(filename: str) -> str:
    stem = Path(filename).stem
    base = stem.rsplit("_", 1)[0] if "_" in stem else stem
    name = base.replace("_", " ").replace("-", " ").strip()
    return name.title() if name else "MLB"


def normalize_key(series: pd.Series) -> pd.Series:
    return (
        series.fillna("")
        .astype(str)
        .str.lower()
        .str.strip()
        .str.replace(r"[.,'`-]", "", regex=True)
        .str.replace(r"\\s+", " ", regex=True)
    )
