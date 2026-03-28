from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass
class DashboardSection:
    title: str
    df: pd.DataFrame
    group: str | None = None
    column_modes: dict[str, list[str]] | None = None
    column_labels: dict[str, str] | None = None
    default_mode: str | None = None
    highlight_starters: bool = False


@dataclass
class DashboardOutputs:
    mlb_hitters_dashboard: pd.DataFrame
    mlb_pitchers_dashboard: pd.DataFrame
    aaa_hitters_dashboard: pd.DataFrame
    aaa_pitchers_dashboard: pd.DataFrame
    recommended_lineup_vs_rhp: pd.DataFrame
    recommended_lineup_vs_lhp: pd.DataFrame
    recommended_rotation: pd.DataFrame
    recommended_bullpen_roles: pd.DataFrame
    platoon_diagnostics: pd.DataFrame
    recommended_transactions: pd.DataFrame
