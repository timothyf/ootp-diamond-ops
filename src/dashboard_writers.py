from __future__ import annotations

from html import escape
from pathlib import Path
from typing import Callable

import pandas as pd

from src.dashboard_types import DashboardOutputs


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
        output_sections: Callable[[DashboardOutputs], list[tuple[str, pd.DataFrame, str | None]]],
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

    def _write_html_outputs(self, outputs: DashboardOutputs, frames: dict[str, pd.DataFrame]) -> None:
        sections = self.output_sections(outputs)
        player_links = self.write_player_detail_pages(frames) if isinstance(frames, dict) else {}
        mlb_home_slug = self.slugify(f"{self.mlb_team_name} team")
        aaa_home_slug = self.slugify(f"{self.aaa_team_name} team")

        overview_sections = []
        for title, df, group in sections:
            slug = self.slugify(title)
            highlight_starters = "active depth chart" in title.lower()
            preview = df.head(8)
            linked_preview = self.link_player_names(preview, player_links.get(group, {})) if group else preview
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
            self.html_shell("OOTP DiamondOps", dashboard_body, "dashboard"),
            encoding="utf-8",
        )

        def team_hub_body(team_name: str, prefix: str, intro: str) -> str:
            cards: list[str] = []
            for title, df, group in sections:
                if not group or not group.startswith(prefix):
                    continue
                slug = self.slugify(title)
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
            self.html_shell(f"{self.mlb_team_name} Team", mlb_hub_body, mlb_home_slug),
            encoding="utf-8",
        )

        aaa_hub_body = team_hub_body(
            self.aaa_team_name,
            "aaa_",
            "Promotion boards and roster stat pages for the AAA club.",
        )
        (self.out_dir / f"{aaa_home_slug}.html").write_text(
            self.html_shell(f"{self.aaa_team_name} Team", aaa_hub_body, aaa_home_slug),
            encoding="utf-8",
        )

        for title, df, group in sections:
            slug = self.slugify(title)
            highlight_starters = "active depth chart" in title.lower()
            linked_df = self.link_player_names(df, player_links.get(group, {})) if group else df
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
                self.html_shell(title, body, active_nav),
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
