from __future__ import annotations

from html import escape
from pathlib import Path

import pandas as pd

from src.data_processing import CsvRepository, PlayerDataTransformer
from src.dashboard_html import build_html_shell, html_table as render_html_table
from src.dashboard_types import DashboardOutputs
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
    build_pitcher_dashboard,
    build_pitcher_standard_stats,
)
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
    ) -> str:
        return render_html_table(
            df,
            allow_html=allow_html,
            sortable=sortable,
            highlight_starters=highlight_starters,
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

    def _output_sections(self, outputs: DashboardOutputs) -> list[tuple[str, pd.DataFrame, str | None]]:
        frames = getattr(self, "_latest_frames", {})
        mlb_hitters_stats = self._build_hitter_standard_stats(frames.get("mlb_hitters", pd.DataFrame()))
        mlb_pitchers_stats = self._build_pitcher_standard_stats(frames.get("mlb_pitchers", pd.DataFrame()))
        aaa_hitters_stats = self._build_hitter_standard_stats(frames.get("aaa_hitters", pd.DataFrame()))
        aaa_pitchers_stats = self._build_pitcher_standard_stats(frames.get("aaa_pitchers", pd.DataFrame()))
        mlb_depth_chart = self._build_active_depth_chart(frames.get("mlb_hitters", pd.DataFrame()))

        return [
            (f"{self.mlb_team_name} hitters - current value", outputs.mlb_hitters_dashboard, "mlb_hitters"),
            (f"{self.mlb_team_name} pitchers - current value", outputs.mlb_pitchers_dashboard, "mlb_pitchers"),
            (f"{self.aaa_team_name} hitters - promotion board", outputs.aaa_hitters_dashboard, "aaa_hitters"),
            (f"{self.aaa_team_name} pitchers - promotion board", outputs.aaa_pitchers_dashboard, "aaa_pitchers"),
            (f"{self.mlb_team_name} hitting stats", mlb_hitters_stats, "mlb_hitters"),
            (f"{self.mlb_team_name} pitching stats", mlb_pitchers_stats, "mlb_pitchers"),
            (f"{self.mlb_team_name} active depth chart", mlb_depth_chart, "mlb_hitters"),
            (f"{self.aaa_team_name} hitting stats", aaa_hitters_stats, "aaa_hitters"),
            (f"{self.aaa_team_name} pitching stats", aaa_pitchers_stats, "aaa_pitchers"),
            ("Recommended lineup vs RHP", outputs.recommended_lineup_vs_rhp, "mlb_hitters"),
            ("Recommended lineup vs LHP", outputs.recommended_lineup_vs_lhp, "mlb_hitters"),
            ("Platoon diagnostics", outputs.platoon_diagnostics, "mlb_hitters"),
            ("Recommended rotation", outputs.recommended_rotation, "mlb_pitchers"),
            ("Bullpen roles", outputs.recommended_bullpen_roles, "mlb_pitchers"),
            ("Recommended transactions", outputs.recommended_transactions, None),
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

    def _write_html_outputs(self, outputs: DashboardOutputs) -> None:
        sections = self._output_sections(outputs)
        frames = getattr(self, "_latest_frames", {})
        player_links = self._write_player_detail_pages(frames) if isinstance(frames, dict) else {}
        mlb_home_slug = self._slugify(f"{self.mlb_team_name} team")
        aaa_home_slug = self._slugify(f"{self.aaa_team_name} team")

        # summary_cards = [
        #     (f"{self.mlb_team_name} hitters", len(outputs.mlb_hitters_dashboard)),
        #     (f"{self.mlb_team_name} pitchers", len(outputs.mlb_pitchers_dashboard)),
        #     (f"{self.aaa_team_name} hitters", len(outputs.aaa_hitters_dashboard)),
        #     (f"{self.aaa_team_name} pitchers", len(outputs.aaa_pitchers_dashboard)),
        #     ("Transactions", len(outputs.recommended_transactions)),
        #     ("Platoon notes", len(outputs.platoon_diagnostics)),
        # ]
        # summary_html = "".join(
        #     f'<article class="summary-card"><span class="eyebrow">{escape(label)}</span><strong>{value}</strong></article>'
        #     for label, value in summary_cards
        # )

        overview_sections = []
        for title, df, group in sections:
            slug = self._slugify(title)
            highlight_starters = "active depth chart" in title.lower()
            preview = df.head(8)
            linked_preview = self._link_player_names(preview, player_links.get(group, {})) if group else preview
            overview_sections.append(
                f"""
                <section class="section-card">
                  <h2>{escape(title)}</h2>
                  <p>{len(df)} rows available in this section.</p>
                  <div class="table-wrap">
                                                                                {self.html_table(linked_preview, allow_html=True, sortable=False, highlight_starters=highlight_starters)}
                  </div>
                  <a class="section-link" href="{slug}.html">Open full section</a>
                </section>
                """
            )

        dashboard_body = f"""
        <section class="section-grid">
          {''.join(overview_sections)}
        </section>
        """
        (self.out_dir / "dashboard.html").write_text(
            self._html_shell("OOTP DiamondOps", dashboard_body, active_page="dashboard"),
            encoding="utf-8",
        )

        def team_hub_body(team_name: str, prefix: str, intro: str) -> str:
            cards: list[str] = []
            for title, df, group in sections:
                if not group or not group.startswith(prefix):
                    continue
                slug = self._slugify(title)
                cards.append(
                    f'<article class="summary-card">'
                    f'<span class="eyebrow">Section</span>'
                    f'<strong style="font-size:1.2rem;line-height:1.3;">{escape(title)}</strong>'
                    f'<p style="margin:8px 0 10px;color:var(--muted);font-size:0.92rem;">{len(df)} rows</p>'
                    f'<a class="section-link" href="{slug}.html">Open page</a>'
                    f'</article>'
                )
            if not cards:
                cards.append('<p class="empty-state">No team pages available.</p>')
            return (
                f'<section class="section-card">'
                f'<h2>{escape(team_name)} Team Hub</h2>'
                f'<p>{escape(intro)}</p>'
                f'<section class="summary-grid">{"".join(cards)}</section>'
                f'</section>'
            )

        mlb_hub_body = team_hub_body(
            self.mlb_team_name,
            "mlb_",
            "Current value boards, roster stats, and planning outputs for the MLB club.",
        )
        (self.out_dir / f"{mlb_home_slug}.html").write_text(
            self._html_shell(f"{self.mlb_team_name} Team", mlb_hub_body, active_page=mlb_home_slug),
            encoding="utf-8",
        )

        aaa_hub_body = team_hub_body(
            self.aaa_team_name,
            "aaa_",
            "Promotion boards and roster stat pages for the AAA club.",
        )
        (self.out_dir / f"{aaa_home_slug}.html").write_text(
            self._html_shell(f"{self.aaa_team_name} Team", aaa_hub_body, active_page=aaa_home_slug),
            encoding="utf-8",
        )

        for title, df, group in sections:
            slug = self._slugify(title)
            highlight_starters = "active depth chart" in title.lower()
            linked_df = self._link_player_names(df, player_links.get(group, {})) if group else df
            if group and group.startswith("mlb_"):
                active_nav = mlb_home_slug
            elif group and group.startswith("aaa_"):
                active_nav = aaa_home_slug
            elif title == "Recommended transactions":
                active_nav = "recommended_transactions"
            else:
                active_nav = "dashboard"
            body = f"""
            <section class="section-card">
              <h2>{escape(title)}</h2>
              <p>{len(df)} rows in this report.</p>
              <div class="table-wrap">
                                {self.html_table(linked_df, allow_html=True, highlight_starters=highlight_starters)}
              </div>
            </section>
            """
            (self.out_dir / f"{slug}.html").write_text(
                self._html_shell(title, body, active_page=active_nav),
                encoding="utf-8",
            )

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
        outputs.mlb_hitters_dashboard = self._round_score_columns(outputs.mlb_hitters_dashboard)
        outputs.mlb_pitchers_dashboard = self._round_score_columns(outputs.mlb_pitchers_dashboard)
        outputs.aaa_hitters_dashboard = self._round_score_columns(outputs.aaa_hitters_dashboard)
        outputs.aaa_pitchers_dashboard = self._round_score_columns(outputs.aaa_pitchers_dashboard)
        outputs.recommended_lineup_vs_rhp = self._round_score_columns(outputs.recommended_lineup_vs_rhp)
        outputs.recommended_lineup_vs_lhp = self._round_score_columns(outputs.recommended_lineup_vs_lhp)
        outputs.recommended_rotation = self._round_score_columns(outputs.recommended_rotation)
        outputs.recommended_bullpen_roles = self._round_score_columns(outputs.recommended_bullpen_roles)
        outputs.platoon_diagnostics = self._round_score_columns(outputs.platoon_diagnostics)
        outputs.recommended_transactions = self._round_score_columns(outputs.recommended_transactions)

        outputs.mlb_hitters_dashboard = self._format_ip_columns(outputs.mlb_hitters_dashboard)
        outputs.mlb_pitchers_dashboard = self._format_ip_columns(outputs.mlb_pitchers_dashboard)
        outputs.aaa_hitters_dashboard = self._format_ip_columns(outputs.aaa_hitters_dashboard)
        outputs.aaa_pitchers_dashboard = self._format_ip_columns(outputs.aaa_pitchers_dashboard)
        outputs.recommended_lineup_vs_rhp = self._format_ip_columns(outputs.recommended_lineup_vs_rhp)
        outputs.recommended_lineup_vs_lhp = self._format_ip_columns(outputs.recommended_lineup_vs_lhp)
        outputs.recommended_rotation = self._format_ip_columns(outputs.recommended_rotation)
        outputs.recommended_bullpen_roles = self._format_ip_columns(outputs.recommended_bullpen_roles)
        outputs.platoon_diagnostics = self._format_ip_columns(outputs.platoon_diagnostics)
        outputs.recommended_transactions = self._format_ip_columns(outputs.recommended_transactions)

        mlb_hitters_csv = f"{self._slugify(f'{self.mlb_team_name} hitters')}_dashboard.csv"
        mlb_pitchers_csv = f"{self._slugify(f'{self.mlb_team_name} pitchers')}_dashboard.csv"
        aaa_hitters_csv = f"{self._slugify(f'{self.aaa_team_name} hitters')}_dashboard.csv"
        aaa_pitchers_csv = f"{self._slugify(f'{self.aaa_team_name} pitchers')}_dashboard.csv"

        outputs.mlb_hitters_dashboard.to_csv(self.out_dir / mlb_hitters_csv, index=False)
        outputs.mlb_pitchers_dashboard.to_csv(self.out_dir / mlb_pitchers_csv, index=False)
        outputs.aaa_hitters_dashboard.to_csv(self.out_dir / aaa_hitters_csv, index=False)
        outputs.aaa_pitchers_dashboard.to_csv(self.out_dir / aaa_pitchers_csv, index=False)
        outputs.recommended_lineup_vs_rhp.to_csv(self.out_dir / "recommended_lineup_vs_rhp.csv", index=False)
        outputs.recommended_lineup_vs_lhp.to_csv(self.out_dir / "recommended_lineup_vs_lhp.csv", index=False)
        outputs.recommended_rotation.to_csv(self.out_dir / "recommended_rotation.csv", index=False)
        outputs.recommended_bullpen_roles.to_csv(self.out_dir / "recommended_bullpen_roles.csv", index=False)
        outputs.recommended_transactions.to_csv(self.out_dir / "recommended_transactions.csv", index=False)
        outputs.platoon_diagnostics.to_csv(self.out_dir / "platoon_diagnostics.csv", index=False)

        report = f"""# OOTP DiamondOps

    ## {self.mlb_team_name} hitters - current value
{self.md_table(outputs.mlb_hitters_dashboard)}

    ## {self.mlb_team_name} pitchers - current value
{self.md_table(outputs.mlb_pitchers_dashboard)}

    ## {self.aaa_team_name} hitters - promotion board
{self.md_table(outputs.aaa_hitters_dashboard)}

    ## {self.aaa_team_name} pitchers - promotion board
{self.md_table(outputs.aaa_pitchers_dashboard)}

## Recommended lineup vs RHP
{self.md_table(outputs.recommended_lineup_vs_rhp)}

## Recommended lineup vs LHP
{self.md_table(outputs.recommended_lineup_vs_lhp)}

## Platoon diagnostics
{self.md_table(outputs.platoon_diagnostics)}

## Recommended rotation
{self.md_table(outputs.recommended_rotation)}

## Bullpen roles
{self.md_table(outputs.recommended_bullpen_roles)}

  ## Recommended transactions
{self.md_table(outputs.recommended_transactions)}
"""
        (self.out_dir / "ootp_gm_dashboard.md").write_text(report, encoding="utf-8")
        self._write_html_outputs(outputs)

    def run(self) -> DashboardOutputs:
        outputs = self.build_outputs()
        self.write_outputs(outputs)
        return outputs
