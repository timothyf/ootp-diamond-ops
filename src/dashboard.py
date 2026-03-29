from __future__ import annotations

from html import escape
from pathlib import Path

import pandas as pd

from src.data_processing import CsvRepository, PlayerDataTransformer
from src.dashboard_html import build_html_shell, html_table as render_html_table
from src.dashboard_types import DashboardOutputs, DashboardSection
from src.dashboard_utils import (
    format_ip_columns,
    md_table,
    normalize_key,
    round_score_columns,
    slugify,
    team_name_from_filename,
)
from src.dashboard_sections import (
    build_aaa_hitter_dashboard,
    build_active_depth_chart,
    build_hitter_dashboard,
    build_hitter_standard_stats,
    build_hitter_toggle_dashboard,
    build_pitcher_dashboard,
    build_pitcher_standard_stats,
    build_pitcher_toggle_dashboard,
)
from src.dashboard_writers import DashboardOutputWriter
from src.metrics import MetricsCalculator
from src.player_detail_pages import PlayerDetailPageWriter
from src.roster_planning import LineupPlanner
from src.transactions import TransactionEngine


class DashboardGenerator:
    def __init__(
        self,
        data_dir: Path | str = "data",
        out_dir: Path | str = "output",
        repository: CsvRepository | None = None,
        transformer: PlayerDataTransformer | None = None,
        metrics: MetricsCalculator | None = None,
        lineup_planner: LineupPlanner | None = None,
        transaction_engine: TransactionEngine | None = None,
    ) -> None:
        self.data_dir = Path(data_dir)
        self.out_dir = Path(out_dir)
        self.out_dir.mkdir(exist_ok=True)

        self.repository = repository or CsvRepository(self.data_dir)

        repo_has_team_prefixes = hasattr(self.repository, "mlb_file_prefix") and hasattr(self.repository, "aaa_file_prefix")
        if repo_has_team_prefixes:
            # DB repositories provide explicit team prefixes; avoid scanning CSV files in this mode.
            mlb_prefix = str(getattr(self.repository, "mlb_file_prefix", "")).strip() or "mlb"
            aaa_prefix = str(getattr(self.repository, "aaa_file_prefix", "")).strip() or "aaa"
        else:
            default_mlb_prefix, default_aaa_prefix = self._discover_team_file_prefixes()
            mlb_prefix = str(getattr(self.repository, "mlb_file_prefix", default_mlb_prefix)).strip() or default_mlb_prefix
            aaa_prefix = str(getattr(self.repository, "aaa_file_prefix", default_aaa_prefix)).strip() or default_aaa_prefix

        self.mlb_batting_filename = f"{mlb_prefix}_batting.csv"
        self.mlb_pitching_filename = f"{mlb_prefix}_pitching.csv"
        self.mlb_roster_filename = f"{mlb_prefix}_roster.csv"
        self.mlb_team_name = self._team_name_from_filename(self.mlb_batting_filename)

        self.aaa_batting_filename = f"{aaa_prefix}_batting.csv"
        self.aaa_pitching_filename = f"{aaa_prefix}_pitching.csv"
        self.aaa_roster_filename = f"{aaa_prefix}_roster.csv"
        self.aaa_team_name = self._team_name_from_filename(self.aaa_batting_filename)

        if hasattr(self.repository, "mlb_team_name"):
            self.mlb_team_name = str(self.repository.mlb_team_name).split()[0]
        if hasattr(self.repository, "aaa_team_name"):
            self.aaa_team_name = str(self.repository.aaa_team_name).split()[0]

        export_date = self.repository.get_export_date() if hasattr(self.repository, "get_export_date") else None
        self.ootp_export_date = str(export_date).strip() if export_date else None
        self.transformer = transformer or PlayerDataTransformer()
        self.metrics = metrics or MetricsCalculator(self.transformer)
        self.lineup_planner = lineup_planner or LineupPlanner()
        self.transaction_engine = transaction_engine or TransactionEngine()

    @staticmethod
    def md_table(df: pd.DataFrame) -> str:
        return md_table(df)

    @staticmethod
    def html_table(
        df: pd.DataFrame,
        allow_html: bool = False,
        sortable: bool = True,
        highlight_starters: bool = False,
        column_modes: dict[str, list[str]] | None = None,
        column_labels: dict[str, str] | None = None,
        default_mode: str | None = None,
    ) -> str:
        return render_html_table(
            df,
            allow_html=allow_html,
            sortable=sortable,
            highlight_starters=highlight_starters,
            column_modes=column_modes,
            column_labels=column_labels,
            default_mode=default_mode,
        )

    @staticmethod
    def _round_score_columns(df: pd.DataFrame) -> pd.DataFrame:
        return round_score_columns(df)

    @staticmethod
    def _format_ip_columns(df: pd.DataFrame) -> pd.DataFrame:
        return format_ip_columns(df)

    @staticmethod
    def _slugify(title: str) -> str:
        return slugify(title)

    @staticmethod
    def _team_name_from_filename(filename: str) -> str:
        return team_name_from_filename(filename)

    def _discover_team_file_prefixes(self) -> tuple[str, str]:
        prefixes: list[str] = []
        for batting_file in sorted(self.data_dir.glob("*_batting.csv")):
            prefix = batting_file.stem.rsplit("_", 1)[0]
            if not prefix:
                continue
            if (self.data_dir / f"{prefix}_pitching.csv").exists() and (self.data_dir / f"{prefix}_roster.csv").exists():
                prefixes.append(prefix)

        unique_prefixes = sorted(set(prefixes))
        if len(unique_prefixes) >= 2:
            return unique_prefixes[0], unique_prefixes[1]
        if len(unique_prefixes) == 1:
            return unique_prefixes[0], "aaa"
        return "mlb", "aaa"

    def _html_shell(self, title: str, body: str, active_page: str | None = None) -> str:
                return build_html_shell(
                        title=title,
                        body=body,
                        mlb_team_name=self.mlb_team_name,
                        aaa_team_name=self.aaa_team_name,
                        ootp_export_date=self.ootp_export_date,
                        active_page=active_page,
                )

    def _output_sections(self, outputs: DashboardOutputs) -> list[DashboardSection]:
        frames = getattr(self, "_latest_frames", {})
        mlb_depth_chart = self._build_active_depth_chart(frames.get("mlb_hitters", pd.DataFrame()))
        mlb_hitters_toggle_df, mlb_hitters_modes, mlb_hitters_labels = build_hitter_toggle_dashboard(
            frames.get("mlb_hitters", pd.DataFrame()),
            "overall_hitter_score",
        )
        mlb_pitchers_toggle_df, mlb_pitchers_modes, mlb_pitchers_labels = build_pitcher_toggle_dashboard(
            frames.get("mlb_pitchers", pd.DataFrame()),
            "score",
        )
        aaa_hitters_toggle_df, aaa_hitters_modes, aaa_hitters_labels = build_hitter_toggle_dashboard(
            frames.get("aaa_hitters", pd.DataFrame()),
            "projection_hitter_score",
            include_potential=True,
        )
        aaa_pitchers_toggle_df, aaa_pitchers_modes, aaa_pitchers_labels = build_pitcher_toggle_dashboard(
            frames.get("aaa_pitchers", pd.DataFrame()),
            "projection_pitcher_score",
            include_potential=True,
        )

        mlb_hitters_toggle_df = self._format_ip_columns(self._round_score_columns(mlb_hitters_toggle_df))
        mlb_pitchers_toggle_df = self._format_ip_columns(self._round_score_columns(mlb_pitchers_toggle_df))
        aaa_hitters_toggle_df = self._format_ip_columns(self._round_score_columns(aaa_hitters_toggle_df))
        aaa_pitchers_toggle_df = self._format_ip_columns(self._round_score_columns(aaa_pitchers_toggle_df))
        mlb_depth_chart = self._format_ip_columns(self._round_score_columns(mlb_depth_chart))

        return [
            DashboardSection(
                title=f"{self.mlb_team_name} hitters",
                df=mlb_hitters_toggle_df,
                group="mlb_hitters",
                column_modes=mlb_hitters_modes,
                column_labels=mlb_hitters_labels,
                default_mode="current",
            ),
            DashboardSection(
                title=f"{self.mlb_team_name} pitchers",
                df=mlb_pitchers_toggle_df,
                group="mlb_pitchers",
                column_modes=mlb_pitchers_modes,
                column_labels=mlb_pitchers_labels,
                default_mode="current",
            ),
            DashboardSection(
                title=f"{self.aaa_team_name} hitters",
                df=aaa_hitters_toggle_df,
                group="aaa_hitters",
                column_modes=aaa_hitters_modes,
                column_labels=aaa_hitters_labels,
                default_mode="current",
            ),
            DashboardSection(
                title=f"{self.aaa_team_name} pitchers",
                df=aaa_pitchers_toggle_df,
                group="aaa_pitchers",
                column_modes=aaa_pitchers_modes,
                column_labels=aaa_pitchers_labels,
                default_mode="current",
            ),
            DashboardSection(
                title=f"{self.mlb_team_name} active depth chart",
                df=mlb_depth_chart,
                group="mlb_hitters",
                highlight_starters=True,
            ),
            DashboardSection(title="Recommended lineup vs RHP", df=outputs.recommended_lineup_vs_rhp, group="mlb_hitters"),
            DashboardSection(title="Recommended lineup vs LHP", df=outputs.recommended_lineup_vs_lhp, group="mlb_hitters"),
            DashboardSection(title="Platoon diagnostics", df=outputs.platoon_diagnostics, group="mlb_hitters"),
            DashboardSection(title="Recommended rotation", df=outputs.recommended_rotation, group="mlb_pitchers"),
            DashboardSection(title="Bullpen roles", df=outputs.recommended_bullpen_roles, group="mlb_pitchers"),
            DashboardSection(title="Recommended transactions", df=outputs.recommended_transactions, group=None),
        ]

    @staticmethod
    def _normalize_key(series: pd.Series) -> pd.Series:
        return normalize_key(series)

    def _player_detail_filename(self, group: str, player_name: str) -> str:
        safe_name = self._slugify(player_name).replace("__", "_").strip("_")
        # Replace the 'mlb'/'aaa' prefix with the actual city name for readability.
        file_group = (
            group
            .replace("mlb_", f"{self.mlb_team_name.lower()}_")
            .replace("aaa_", f"{self.aaa_team_name.lower()}_")
        )
        return f"player_{file_group}_{safe_name}.html"

    def _player_detail_writer(self) -> PlayerDetailPageWriter:
        return PlayerDetailPageWriter(
            out_dir=self.out_dir,
            html_table=self.html_table,
            html_shell=lambda title, body: self._html_shell(title, body),
            player_detail_filename=self._player_detail_filename,
            normalize_key=self._normalize_key,
        )

    def _link_player_names(self, df: pd.DataFrame, player_links: dict[str, str]) -> pd.DataFrame:
        if "player_name" not in df.columns:
            return df
        linked = df.copy()
        keys = self._normalize_key(linked["player_name"])
        hrefs = keys.map(player_links)
        linked["player_name"] = [
            f'<a href="{href}">{escape(str(name))}</a>' if isinstance(href, str) else escape(str(name))
            for name, href in zip(linked["player_name"], hrefs)
        ]
        return linked

    @staticmethod
    def _score_narrative(row: pd.Series, group: str) -> str:  # noqa: C901
        return PlayerDetailPageWriter.score_narrative(row, group)

    @staticmethod
    def _component_rows(
        frame_row: pd.Series,
        fields: list[tuple[str, str] | tuple[str, str, str]],
        include_weight: bool = False,
    ) -> pd.DataFrame:
        return PlayerDetailPageWriter.component_rows(frame_row, fields, include_weight)

    def _write_player_detail_pages(self, group_frames: dict[str, pd.DataFrame]) -> dict[str, dict[str, str]]:
        return self._player_detail_writer().write_player_detail_pages(group_frames)

    def _output_writer(self) -> DashboardOutputWriter:
        return DashboardOutputWriter(
            out_dir=self.out_dir,
            mlb_team_name=self.mlb_team_name,
            aaa_team_name=self.aaa_team_name,
            slugify=self._slugify,
            md_table=self.md_table,
            html_table=self.html_table,
            html_shell=self._html_shell,
            output_sections=self._output_sections,
            write_player_detail_pages=self._write_player_detail_pages,
            link_player_names=self._link_player_names,
            round_score_columns=self._round_score_columns,
            format_ip_columns=self._format_ip_columns,
        )

    def _write_html_outputs(self, outputs: DashboardOutputs) -> None:
        self._output_writer()._write_html_outputs(outputs, getattr(self, "_latest_frames", {}))

    def _load_named_csv(self, filename: str) -> pd.DataFrame:
        df = self.repository.load(filename)
        df = self.transformer.clean_cols(df)
        df = self.transformer.attach_name(df)
        return self.transformer.dedupe(df)

    def _load_team_frames(self) -> dict[str, pd.DataFrame]:
        mlb_bat = self._load_named_csv(self.mlb_batting_filename)
        mlb_pitch = self._load_named_csv(self.mlb_pitching_filename)
        mlb_roster = self.transformer.prep_roster(self._load_named_csv(self.mlb_roster_filename))

        aaa_bat = self._load_named_csv(self.aaa_batting_filename)
        aaa_pitch = self._load_named_csv(self.aaa_pitching_filename)
        aaa_roster = self.transformer.prep_roster(self._load_named_csv(self.aaa_roster_filename))

        players_raw = self._load_named_csv("player_ratings.csv")
        players = self.transformer.prepare_ratings(players_raw)

        mlb_hitters = self.transformer.merge_ratings(self.transformer.stat_merge(mlb_roster, mlb_bat), players)
        mlb_pitchers = self.transformer.merge_ratings(self.transformer.stat_merge(mlb_roster, mlb_pitch), players)
        aaa_hitters = self.transformer.merge_ratings(self.transformer.stat_merge(aaa_roster, aaa_bat), players)
        aaa_pitchers = self.transformer.merge_ratings(self.transformer.stat_merge(aaa_roster, aaa_pitch), players)

        mlb_hitters = self.transformer.add_positional_bucket(mlb_hitters)
        aaa_hitters = self.transformer.add_positional_bucket(aaa_hitters)

        mlb_hitters = self.metrics.add_hitting_metrics(mlb_hitters)
        aaa_hitters = self.metrics.add_hitting_metrics(aaa_hitters)
        mlb_pitchers = self.metrics.add_pitching_metrics(mlb_pitchers)
        aaa_pitchers = self.metrics.add_pitching_metrics(aaa_pitchers)

        return {
            "mlb_hitters": mlb_hitters,
            "mlb_pitchers": mlb_pitchers,
            "aaa_hitters": aaa_hitters,
            "aaa_pitchers": aaa_pitchers,
        }

    @staticmethod
    def _build_hitter_dashboard(df: pd.DataFrame, score_col: str) -> pd.DataFrame:
        return build_hitter_dashboard(df, score_col)

    @staticmethod
    def _build_hitter_standard_stats(df: pd.DataFrame) -> pd.DataFrame:
        return build_hitter_standard_stats(df)

    @staticmethod
    def _build_active_depth_chart(df: pd.DataFrame, depth_per_position: int = 4) -> pd.DataFrame:
        return build_active_depth_chart(df, depth_per_position)

    @staticmethod
    def _build_aaa_hitter_dashboard(df: pd.DataFrame) -> pd.DataFrame:
        return build_aaa_hitter_dashboard(df)

    @staticmethod
    def _build_pitcher_standard_stats(df: pd.DataFrame) -> pd.DataFrame:
        return build_pitcher_standard_stats(df)

    @staticmethod
    def _build_pitcher_dashboard(df: pd.DataFrame, score_col: str, include_potential: bool = False) -> pd.DataFrame:
        return build_pitcher_dashboard(df, score_col, include_potential)

    def build_outputs(self) -> DashboardOutputs:
        frames = self._load_team_frames()
        self._latest_frames = frames

        recommended_lineup_vs_rhp = self.lineup_planner.build_lineup(frames["mlb_hitters"], "RHP")
        recommended_lineup_vs_lhp = self.lineup_planner.build_lineup(frames["mlb_hitters"], "LHP")
        recommended_rotation = self.lineup_planner.build_rotation(frames["mlb_pitchers"])
        recommended_bullpen_roles = self.lineup_planner.build_bullpen(frames["mlb_pitchers"])

        platoon_diagnostics = self.lineup_planner.build_platoon_diagnostics(
            frames["mlb_hitters"],
            recommended_lineup_vs_rhp,
            recommended_lineup_vs_lhp,
            top_n=3,
        )

        _, _, recommended_transactions = self.transaction_engine.build_recommended_transactions(
            frames["aaa_hitters"],
            frames["aaa_pitchers"],
            frames["mlb_hitters"],
            frames["mlb_pitchers"],
        )

        return DashboardOutputs(
            mlb_hitters_dashboard=self._build_hitter_dashboard(frames["mlb_hitters"], "overall_hitter_score"),
            mlb_pitchers_dashboard=self._build_pitcher_dashboard(frames["mlb_pitchers"], "score"),
            aaa_hitters_dashboard=self._build_aaa_hitter_dashboard(frames["aaa_hitters"]),
            aaa_pitchers_dashboard=self._build_pitcher_dashboard(
                frames["aaa_pitchers"], "projection_pitcher_score", include_potential=True
            ),
            recommended_lineup_vs_rhp=recommended_lineup_vs_rhp,
            recommended_lineup_vs_lhp=recommended_lineup_vs_lhp,
            recommended_rotation=recommended_rotation,
            recommended_bullpen_roles=recommended_bullpen_roles,
            platoon_diagnostics=platoon_diagnostics,
            recommended_transactions=recommended_transactions,
        )

    def write_outputs(self, outputs: DashboardOutputs) -> None:
        self._output_writer().write_outputs(outputs, getattr(self, "_latest_frames", {}))

    def run(self) -> DashboardOutputs:
        outputs = self.build_outputs()
        self.write_outputs(outputs)
        return outputs
