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
class CompletedSeasonTeamSummary:
    team_name: str
    wins: int | None = None
    losses: int | None = None
    position: int | None = None
    gb: float | None = None
    made_playoffs: bool = False
    won_playoffs: bool = False
    best_hitter: str | None = None
    best_pitcher: str | None = None
    best_rookie: str | None = None


@dataclass
class CompletedSeasonSummary:
    season_year: int
    mlb: CompletedSeasonTeamSummary
    aaa: CompletedSeasonTeamSummary


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
