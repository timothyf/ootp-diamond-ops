from __future__ import annotations

from html import escape
from pathlib import Path
from typing import Callable

import pandas as pd

from src.dashboard_types import DashboardOutputs, DashboardSection


class DashboardOutputWriter:
    def __init__(
        self,
        out_dir: Path,
        mlb_team_name: str,
        aaa_team_name: str,
        slugify: Callable[[str], str],
        md_table: Callable[[pd.DataFrame], str],
        html_table: Callable[..., str],
        html_shell: Callable[[str, str, str | None], str],
        output_sections: Callable[[DashboardOutputs], list[DashboardSection]],
        write_player_detail_pages: Callable[[dict[str, pd.DataFrame]], dict[str, dict[str, str]]],
        link_player_names: Callable[[pd.DataFrame, dict[str, str]], pd.DataFrame],
        round_score_columns: Callable[[pd.DataFrame], pd.DataFrame],
        format_ip_columns: Callable[[pd.DataFrame], pd.DataFrame],
    ) -> None:
        self.out_dir = out_dir
        self.mlb_team_name = mlb_team_name
        self.aaa_team_name = aaa_team_name
        self.slugify = slugify
        self.md_table = md_table
        self.html_table = html_table
        self.html_shell = html_shell
        self.output_sections = output_sections
        self.write_player_detail_pages = write_player_detail_pages
        self.link_player_names = link_player_names
        self.round_score_columns = round_score_columns
        self.format_ip_columns = format_ip_columns

    @staticmethod
    def _series(df: pd.DataFrame, column: str) -> pd.Series:
        if column in df.columns:
            return pd.to_numeric(df[column], errors="coerce").fillna(0.0)
        return pd.Series(0.0, index=df.index, dtype=float)

    @staticmethod
    def _zscore(series: pd.Series) -> pd.Series:
        centered = pd.to_numeric(series, errors="coerce").fillna(0.0)
        std_dev = float(centered.std(ddof=0))
        if std_dev == 0.0:
            return pd.Series(0.0, index=centered.index)
        return (centered - float(centered.mean())) / std_dev

    @staticmethod
    def _pct(stats: float, ratings: float, other: float) -> tuple[float, float, float]:
        total = float(stats + ratings + other)
        if total == 0.0:
            return 0.0, 0.0, 0.0
        return stats * 100.0 / total, ratings * 100.0 / total, other * 100.0 / total

    def _normalized_share(self, components: dict[str, tuple[str, pd.Series]]) -> tuple[float, float, float]:
        sums = {"stats": 0.0, "ratings": 0.0, "other": 0.0}
        for category, values in components.values():
            z_values = self._zscore(values)
            sums[category] += float(z_values.abs().sum())
        return self._pct(sums["stats"], sums["ratings"], sums["other"])

    def _compute_score_breakdown(self, frames: dict[str, pd.DataFrame]) -> dict[str, tuple[float, float, float]]:
        hitters = pd.concat(
            [frames.get("mlb_hitters", pd.DataFrame()), frames.get("aaa_hitters", pd.DataFrame())],
            ignore_index=True,
        )
        pitchers = pd.concat(
            [frames.get("mlb_pitchers", pd.DataFrame()), frames.get("aaa_pitchers", pd.DataFrame())],
            ignore_index=True,
        )

        hitter_current_formula = self._pct(0.60 + 0.80, 0.22 + 0.60 + 0.50 + 0.25, 0.40)
        hitter_projection_formula = self._pct(0.28 + 0.90, 0.27 + 0.34 + 0.70 + 0.35 + 0.20, 0.50)

        command_stats = 0.9
        command_ratings = 0.06 + 0.04 + 0.4
        contact_stats = 2.0 + 0.25
        contact_ratings = 0.03 + 0.01
        durability_stats = 0.015 + 0.12
        durability_ratings = 0.03

        pitcher_current_stats_weight = (
            0.58
            + 0.20 * (command_stats / (command_stats + command_ratings))
            + 0.14 * (contact_stats / (contact_stats + contact_ratings))
            + 0.12 * (durability_stats / (durability_stats + durability_ratings))
        )
        pitcher_current_ratings_weight = (
            0.30
            + 0.20 * (command_ratings / (command_stats + command_ratings))
            + 0.14 * (contact_ratings / (contact_stats + contact_ratings))
            + 0.12 * (durability_ratings / (durability_stats + durability_ratings))
        )
        pitcher_current_formula = self._pct(pitcher_current_stats_weight, pitcher_current_ratings_weight, 0.0)

        pitcher_projection_stats_weight = (
            0.26
            + 0.22 * (command_stats / (command_stats + command_ratings))
            + 0.14 * (contact_stats / (contact_stats + contact_ratings))
            + 0.10 * (durability_stats / (durability_stats + durability_ratings))
        )
        pitcher_projection_ratings_weight = (
            0.24
            + 0.34
            + 0.22 * (command_ratings / (command_stats + command_ratings))
            + 0.14 * (contact_ratings / (contact_stats + contact_ratings))
            + 0.10 * (durability_ratings / (durability_stats + durability_ratings))
        )
        pitcher_projection_formula = self._pct(pitcher_projection_stats_weight, pitcher_projection_ratings_weight, 0.5)

        h = hitters
        hitter_current_empirical = self._normalized_share(
            {
                "offense": ("stats", self._series(h, "offense_score_regressed") * 0.52),
                "discipline": ("stats", self._series(h, "discipline_component") * 0.80),
                "contact_quality": ("stats", self._series(h, "contact_quality_component") * 0.08),
                "ratings_now": ("ratings", self._series(h, "ratings_hitter_now") * 0.22),
                "platoon": ("ratings", self._series(h, "platoon_skill_component") * 0.60),
                "defense": ("ratings", self._series(h, "defensive_component") * 0.50),
                "running": ("ratings", self._series(h, "running_component") * 0.25),
                "scarcity": ("other", self._series(h, "scarcity_bonus") * 0.40),
            }
        )
        hitter_projection_empirical = self._normalized_share(
            {
                "offense": ("stats", self._series(h, "offense_score_regressed") * 0.26),
                "discipline": ("stats", self._series(h, "discipline_component") * 0.90),
                "contact_quality": ("stats", self._series(h, "contact_quality_component") * 0.04),
                "ratings_now": ("ratings", self._series(h, "ratings_hitter_now") * 0.27),
                "ratings_future": ("ratings", self._series(h, "ratings_hitter_future") * 0.34),
                "platoon": ("ratings", self._series(h, "platoon_skill_component") * 0.70),
                "defense": ("ratings", self._series(h, "defensive_component") * 0.35),
                "running": ("ratings", self._series(h, "running_component") * 0.20),
                "age": ("other", self._series(h, "age_bonus") * 0.50),
            }
        )

        p = pitchers
        command_stat = self._series(p, "k_bb_9_val") * 0.9
        command_ratings = (
            self._series(p, "control_now") * 0.06
            + self._series(p, "stuff_now") * 0.04
            + self._series(p, "pitcher_platoon_component") * 0.4
        )
        contact_stat = self._series(p, "gb_share_val") * 2.0 + (-self._series(p, "hr_9_val") * 0.25)
        contact_ratings = self._series(p, "movement_now") * 0.03 + ((self._series(p, "pitch_ground_fly") - 50.0) / 100.0)

        pitch_stamina = self._series(p, "pitch_stamina")
        stamina_now = self._series(p, "stamina_now")
        stamina_source = pitch_stamina.where(pitch_stamina > 0.0, stamina_now)
        durability_stat = self._series(p, "ip_val") * 0.015 + self._series(p, "gs_val") * 0.12
        durability_ratings = stamina_source.sub(50.0).clip(-30.0, 30.0) * 0.03

        pitcher_current_empirical = self._normalized_share(
            {
                "results": ("stats", self._series(p, "results_pitcher_score_regressed") * 0.58),
                "ratings_now": ("ratings", self._series(p, "ratings_pitcher_now") * 0.30),
                "command_stat": ("stats", command_stat * 0.20),
                "command_ratings": ("ratings", command_ratings * 0.20),
                "contact_stat": ("stats", contact_stat * 0.14),
                "contact_ratings": ("ratings", contact_ratings * 0.14),
                "durability_stat": ("stats", durability_stat * 0.12),
                "durability_ratings": ("ratings", durability_ratings * 0.12),
            }
        )
        pitcher_projection_empirical = self._normalized_share(
            {
                "results": ("stats", self._series(p, "results_pitcher_score_regressed") * 0.26),
                "ratings_now": ("ratings", self._series(p, "ratings_pitcher_now") * 0.24),
                "ratings_future": ("ratings", self._series(p, "ratings_pitcher_future") * 0.34),
                "age": ("other", self._series(p, "age_bonus") * 0.5),
                "command_stat": ("stats", command_stat * 0.22),
                "command_ratings": ("ratings", command_ratings * 0.22),
                "contact_stat": ("stats", contact_stat * 0.14),
                "contact_ratings": ("ratings", contact_ratings * 0.14),
                "durability_stat": ("stats", durability_stat * 0.10),
                "durability_ratings": ("ratings", durability_ratings * 0.10),
            }
        )

        return {
            "hitter_current_formula": hitter_current_formula,
            "hitter_projection_formula": hitter_projection_formula,
            "pitcher_current_formula": pitcher_current_formula,
            "pitcher_projection_formula": pitcher_projection_formula,
            "hitter_current_empirical": hitter_current_empirical,
            "hitter_projection_empirical": hitter_projection_empirical,
            "pitcher_current_empirical": pitcher_current_empirical,
            "pitcher_projection_empirical": pitcher_projection_empirical,
            "hitter_n": (float(len(hitters)), 0.0, 0.0),
            "pitcher_n": (float(len(pitchers)), 0.0, 0.0),
        }

    @staticmethod
    def _score_row(label: str, values: tuple[float, float, float]) -> str:
        stats, ratings, other = values
        return (
            "<tr>"
            f"<td>{escape(label)}</td>"
            f"<td>{stats:.2f}%</td>"
            f"<td>{ratings:.2f}%</td>"
            f"<td>{other:.2f}%</td>"
            "</tr>"
        )

    def _write_scoring_info_page(self, frames: dict[str, pd.DataFrame]) -> None:
        breakdown = self._compute_score_breakdown(frames)
        hitter_count = int(breakdown["hitter_n"][0])
        pitcher_count = int(breakdown["pitcher_n"][0])

        formula_rows = "".join(
            [
                self._score_row("Hitters - Current (overall_hitter_score)", breakdown["hitter_current_formula"]),
                self._score_row("Hitters - Projection (projection_hitter_score)", breakdown["hitter_projection_formula"]),
                self._score_row("Pitchers - Current (score)", breakdown["pitcher_current_formula"]),
                self._score_row("Pitchers - Projection (projection_pitcher_score)", breakdown["pitcher_projection_formula"]),
            ]
        )
        empirical_rows = "".join(
            [
                self._score_row("Hitters - Current", breakdown["hitter_current_empirical"]),
                self._score_row("Hitters - Projection", breakdown["hitter_projection_empirical"]),
                self._score_row("Pitchers - Current", breakdown["pitcher_current_empirical"]),
                self._score_row("Pitchers - Projection", breakdown["pitcher_projection_empirical"]),
            ]
        )

        table_head = (
            "<thead><tr><th>Score</th><th>Stats</th><th>Ratings</th><th>Other</th></tr></thead>"
        )

        body = f"""
        <section class="section-card">
          <h2>Score Breakdown Guide</h2>
          <p>
            This page explains how player scores blend real performance stats and OOTP ratings.
            Formula-share values are based on configured score weights. Empirical-share values are
            computed from the current dataset using normalized (z-scored) weighted contributions.
          </p>
          <div class="narrative-card">
            <h3>Current Sample</h3>
            <p class="narrative-intro">Hitters analyzed: {hitter_count}. Pitchers analyzed: {pitcher_count}.</p>
          </div>
          <div class="narrative-card">
            <h3>Formula Weight Shares</h3>
            <div class="table-wrap">
              <table class="data-table" data-sortable="false" data-highlight-starters="false" data-default-mode="">{table_head}<tbody>{formula_rows}</tbody></table>
            </div>
          </div>
          <div class="narrative-card">
            <h3>Empirical Normalized Shares</h3>
            <p class="narrative-intro">
              Based on absolute z-scored contribution magnitudes from current MLB + AAA frames.
            </p>
            <div class="table-wrap">
              <table class="data-table" data-sortable="false" data-highlight-starters="false" data-default-mode="">{table_head}<tbody>{empirical_rows}</tbody></table>
            </div>
          </div>
        </section>
        """
        (self.out_dir / "scoring_info.html").write_text(
            self.html_shell("Scoring Breakdown", body, "scoring_info"),
            encoding="utf-8",
        )

    @staticmethod
    def _overview_group_label(section: DashboardSection) -> str:
        if section.title == "Recommended transactions":
            return "Decisions"
        if section.group == "mlb_hitters":
            if "lineup" in section.title.lower() or "platoon" in section.title.lower():
                return "Decisions"
            return "MLB overview"
        if section.group == "mlb_pitchers":
            if "rotation" in section.title.lower() or "bullpen" in section.title.lower():
                return "Decisions"
            return "MLB overview"
        if section.group and section.group.startswith("aaa_"):
            return "AAA watchlist"
        return "Other"

    @staticmethod
    def _overview_preview_limit(section: DashboardSection) -> int:
        if section.title == "Platoon diagnostics":
            return 4
        return 5

    @staticmethod
    def _overview_preview_columns(section: DashboardSection) -> list[str] | None:
        preview_columns = {
            "Recommended transactions": ["move_type", "player_name", "possible_replace", "score_gap"],
            "Platoon diagnostics": ["slot", "player_name", "score", "handedness_edge"],
            "Recommended lineup vs RHP": ["slot", "position", "player_name", "obp", "score"],
            "Recommended lineup vs LHP": ["slot", "position", "player_name", "obp", "score"],
            "Recommended rotation": ["slot", "player_name", "era", "fip", "rotation_score"],
            "Bullpen roles": ["role", "player_name", "era", "fip", "bullpen_score"],
        }
        if section.title in preview_columns:
            return preview_columns[section.title]
        if section.group == "mlb_hitters":
            if "depth chart" in section.title.lower():
                return ["position", "rank", "player_name", "ops", "score"]
            return ["player_name", "primary_position", "cv_ops", "score", "injury_text"]
        if section.group == "aaa_hitters":
            return ["player_name", "primary_position", "cv_ops", "score", "injury_text"]
        if section.group in {"mlb_pitchers", "aaa_pitchers"}:
            return ["player_name", "cv_ip", "cv_era", "cv_fip", "score", "injury_text"]
        return None

    def _build_overview_preview(
        self,
        section: DashboardSection,
    ) -> tuple[pd.DataFrame, dict[str, list[str]] | None, dict[str, str] | None, str | None]:
        preview = section.df.head(self._overview_preview_limit(section)).copy()
        preview_columns = self._overview_preview_columns(section)
        if preview_columns:
            present_columns = [column for column in preview_columns if column in preview.columns]
            if present_columns:
                preview = preview[present_columns]

        column_modes = None
        if section.column_modes:
            available_columns = set(preview.columns)
            filtered_modes = {
                mode: [column for column in columns if column in available_columns]
                for mode, columns in section.column_modes.items()
            }
            column_modes = {mode: columns for mode, columns in filtered_modes.items() if columns}
            if len(column_modes) < 2:
                column_modes = None

        column_labels = None
        if section.column_labels:
            column_labels = {
                column: label for column, label in section.column_labels.items() if column in preview.columns
            }

        default_mode = section.default_mode if column_modes and section.default_mode in column_modes else None
        return preview, column_modes, column_labels, default_mode

    def _write_html_outputs(self, outputs: DashboardOutputs, frames: dict[str, pd.DataFrame]) -> None:
        sections = self.output_sections(outputs)
        player_links = self.write_player_detail_pages(frames) if isinstance(frames, dict) else {}
        mlb_home_slug = self.slugify(f"{self.mlb_team_name} team")
        aaa_home_slug = self.slugify(f"{self.aaa_team_name} team")

        overview_sections_by_group: dict[str, list[str]] = {
            "MLB overview": [],
            "AAA watchlist": [],
            "Decisions": [],
        }
        for section in sections:
            slug = self.slugify(section.title)
            preview, preview_modes, preview_labels, preview_default_mode = self._build_overview_preview(section)
            linked_preview = (
                self.link_player_names(preview, player_links.get(section.group, {})) if section.group else preview
            )
            group_label = self._overview_group_label(section)
            overview_sections_by_group.setdefault(group_label, []).append(
                f"""
                <section class="section-card section-card-compact">
                  <header class="section-card-header">
                    <div>
                      <p class="section-kicker">{escape(group_label)}</p>
                      <h2>{escape(section.title)}</h2>
                    </div>
                    <a class="section-link section-link-inline" href="{slug}.html">Open</a>
                  </header>
                  <div class="section-meta-row">
                    <span class="section-meta-pill">{len(section.df)} rows</span>
                    <span class="section-meta-pill">Preview</span>
                  </div>
                  <div class="table-wrap">
                    {self.html_table(
                        linked_preview,
                        allow_html=True,
                        sortable=False,
                        highlight_starters=section.highlight_starters,
                        column_modes=preview_modes,
                        column_labels=preview_labels,
                        default_mode=preview_default_mode,
                    )}
                  </div>
                </section>
                """
            )

        overview_groups = []
        for label in ("MLB overview", "AAA watchlist", "Decisions"):
            cards = overview_sections_by_group.get(label, [])
            if not cards:
                continue
            overview_groups.append(
                f"""
                <section class="dashboard-group">
                  <div class="dashboard-group-heading">
                    <h2>{escape(label)}</h2>
                  </div>
                  <section class="section-grid section-grid-overview">
                    {''.join(cards)}
                  </section>
                </section>
                """
            )

        dashboard_body = f"""
        <section class="dashboard-overview">
          {''.join(overview_groups)}
        </section>
        """
        (self.out_dir / "dashboard.html").write_text(
            self.html_shell("OOTP DiamondOps", dashboard_body, "dashboard"),
            encoding="utf-8",
        )
        self._write_scoring_info_page(frames)

        def team_hub_body(team_name: str, prefix: str, intro: str) -> str:
            cards: list[str] = []
            for section in sections:
                if not section.group or not section.group.startswith(prefix):
                    continue
                slug = self.slugify(section.title)
                cards.append(
                    f'<article class="summary-card">'
                    f'<span class="eyebrow">Section</span>'
                    f'<strong style="font-size:1.2rem;line-height:1.3;">{escape(section.title)}</strong>'
                    f'<p style="margin:8px 0 10px;color:var(--muted);font-size:0.92rem;">{len(section.df)} rows</p>'
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
            "Current value boards with stat toggles, roster depth, and planning outputs for the MLB club.",
        )
        (self.out_dir / f"{mlb_home_slug}.html").write_text(
            self.html_shell(f"{self.mlb_team_name} Team", mlb_hub_body, mlb_home_slug),
            encoding="utf-8",
        )

        aaa_hub_body = team_hub_body(
            self.aaa_team_name,
            "aaa_",
            "Promotion boards with stat toggles and roster planning pages for the AAA club.",
        )
        (self.out_dir / f"{aaa_home_slug}.html").write_text(
            self.html_shell(f"{self.aaa_team_name} Team", aaa_hub_body, aaa_home_slug),
            encoding="utf-8",
        )

        for section in sections:
            slug = self.slugify(section.title)
            linked_df = (
                self.link_player_names(section.df, player_links.get(section.group, {}))
                if section.group
                else section.df
            )
            if section.group and section.group.startswith("mlb_"):
                active_nav = mlb_home_slug
            elif section.group and section.group.startswith("aaa_"):
                active_nav = aaa_home_slug
            elif section.title == "Recommended transactions":
                active_nav = "recommended_transactions"
            else:
                active_nav = "dashboard"
            body = f"""
            <section class="section-card">
              <h2>{escape(section.title)}</h2>
              <p>{len(section.df)} rows in this report.</p>
              <div class="table-wrap">
                                {self.html_table(linked_df, allow_html=True, highlight_starters=section.highlight_starters, column_modes=section.column_modes, column_labels=section.column_labels, default_mode=section.default_mode)}
              </div>
            </section>
            """
            (self.out_dir / f"{slug}.html").write_text(
                self.html_shell(section.title, body, active_nav),
                encoding="utf-8",
            )

    def write_outputs(self, outputs: DashboardOutputs, frames: dict[str, pd.DataFrame]) -> None:
        outputs.mlb_hitters_dashboard = self.round_score_columns(outputs.mlb_hitters_dashboard)
        outputs.mlb_pitchers_dashboard = self.round_score_columns(outputs.mlb_pitchers_dashboard)
        outputs.aaa_hitters_dashboard = self.round_score_columns(outputs.aaa_hitters_dashboard)
        outputs.aaa_pitchers_dashboard = self.round_score_columns(outputs.aaa_pitchers_dashboard)
        outputs.recommended_lineup_vs_rhp = self.round_score_columns(outputs.recommended_lineup_vs_rhp)
        outputs.recommended_lineup_vs_lhp = self.round_score_columns(outputs.recommended_lineup_vs_lhp)
        outputs.recommended_rotation = self.round_score_columns(outputs.recommended_rotation)
        outputs.recommended_bullpen_roles = self.round_score_columns(outputs.recommended_bullpen_roles)
        outputs.platoon_diagnostics = self.round_score_columns(outputs.platoon_diagnostics)
        outputs.recommended_transactions = self.round_score_columns(outputs.recommended_transactions)

        outputs.mlb_hitters_dashboard = self.format_ip_columns(outputs.mlb_hitters_dashboard)
        outputs.mlb_pitchers_dashboard = self.format_ip_columns(outputs.mlb_pitchers_dashboard)
        outputs.aaa_hitters_dashboard = self.format_ip_columns(outputs.aaa_hitters_dashboard)
        outputs.aaa_pitchers_dashboard = self.format_ip_columns(outputs.aaa_pitchers_dashboard)
        outputs.recommended_lineup_vs_rhp = self.format_ip_columns(outputs.recommended_lineup_vs_rhp)
        outputs.recommended_lineup_vs_lhp = self.format_ip_columns(outputs.recommended_lineup_vs_lhp)
        outputs.recommended_rotation = self.format_ip_columns(outputs.recommended_rotation)
        outputs.recommended_bullpen_roles = self.format_ip_columns(outputs.recommended_bullpen_roles)
        outputs.platoon_diagnostics = self.format_ip_columns(outputs.platoon_diagnostics)
        outputs.recommended_transactions = self.format_ip_columns(outputs.recommended_transactions)

        mlb_hitters_csv = f"{self.slugify(f'{self.mlb_team_name} hitters')}_dashboard.csv"
        mlb_pitchers_csv = f"{self.slugify(f'{self.mlb_team_name} pitchers')}_dashboard.csv"
        aaa_hitters_csv = f"{self.slugify(f'{self.aaa_team_name} hitters')}_dashboard.csv"
        aaa_pitchers_csv = f"{self.slugify(f'{self.aaa_team_name} pitchers')}_dashboard.csv"

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
        self._write_html_outputs(outputs, frames)