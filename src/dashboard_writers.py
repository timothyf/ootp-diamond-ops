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