from __future__ import annotations

from dataclasses import dataclass
from html import escape
from pathlib import Path

import pandas as pd

from src.data_processing import CsvRepository, PlayerDataTransformer
from src.metrics import MetricsCalculator
from src.roster_planning import LineupPlanner
from src.transactions import TransactionEngine


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

        self.mlb_batting_filename = "tigers_batting.csv"
        self.mlb_pitching_filename = "tigers_pitching.csv"
        self.mlb_roster_filename = "tigers_roster.csv"
        self.mlb_team_name = self._team_name_from_filename(self.mlb_batting_filename)

        self.aaa_batting_filename = "toledo_batting.csv"
        self.aaa_pitching_filename = "toledo_pitching.csv"
        self.aaa_roster_filename = "toledo_roster.csv"
        self.aaa_team_name = self._team_name_from_filename(self.aaa_batting_filename)

        self.repository = repository or CsvRepository(self.data_dir)
        self.transformer = transformer or PlayerDataTransformer()
        self.metrics = metrics or MetricsCalculator(self.transformer)
        self.lineup_planner = lineup_planner or LineupPlanner()
        self.transaction_engine = transaction_engine or TransactionEngine()

    @staticmethod
    def md_table(df: pd.DataFrame) -> str:
        if df.empty:
            return "_No rows_"
        return df.to_markdown(index=False)

    @staticmethod
    def html_table(df: pd.DataFrame) -> str:
        if df.empty:
            return '<p class="empty-state">No rows</p>'
        return df.to_html(index=False, classes=["data-table"], border=0)

    @staticmethod
    def _slugify(title: str) -> str:
        return (
            title.lower()
            .replace(" - ", "_")
            .replace(" ", "_")
            .replace("/", "_")
        )

    @staticmethod
    def _team_name_from_filename(filename: str) -> str:
        stem = Path(filename).stem
        base = stem.rsplit("_", 1)[0] if "_" in stem else stem
        name = base.replace("_", " ").replace("-", " ").strip()
        return name.title() if name else "MLB"

    def _html_shell(self, title: str, body: str, active_page: str | None = None) -> str:
        mlb_hitters_slug = self._slugify(f"{self.mlb_team_name} hitters - current value")
        mlb_pitchers_slug = self._slugify(f"{self.mlb_team_name} pitchers - current value")
        aaa_hitters_slug = self._slugify(f"{self.aaa_team_name} hitters - promotion board")
        aaa_pitchers_slug = self._slugify(f"{self.aaa_team_name} pitchers - promotion board")

        nav_items = [
            ("dashboard", "dashboard.html", "Dashboard"),
            (
                mlb_hitters_slug,
                f"{mlb_hitters_slug}.html",
                f"{self.mlb_team_name} Hitters",
            ),
            (
                mlb_pitchers_slug,
                f"{mlb_pitchers_slug}.html",
                f"{self.mlb_team_name} Pitchers",
            ),
            (
                aaa_hitters_slug,
                f"{aaa_hitters_slug}.html",
                f"{self.aaa_team_name} Hitters",
            ),
            (
                aaa_pitchers_slug,
                f"{aaa_pitchers_slug}.html",
                f"{self.aaa_team_name} Pitchers",
            ),
            ("recommended_transactions", "recommended_transactions.html", "Transactions"),
        ]
        nav_links = "".join(
            f'<a class="{"is-active" if key == active_page else ""}" href="{href}">{escape(label)}</a>'
            for key, href, label in nav_items
        )
        nav = f'<nav class="top-nav">{nav_links}</nav>'
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(title)}</title>
  <style>
    :root {{
      --bg: #f4efe4;
      --panel: rgba(255, 250, 240, 0.92);
      --ink: #1f2a2a;
      --muted: #5f6b63;
      --line: #d4c4a8;
      --accent: #0d5c63;
      --accent-soft: #dcefee;
      --highlight: #f0b429;
      --shadow: 0 18px 45px rgba(40, 34, 20, 0.10);
    }}
    * {{
      box-sizing: border-box;
    }}
    body {{
      margin: 0;
      font-family: Georgia, "Times New Roman", serif;
      color: var(--ink);
      background:
        radial-gradient(circle at top left, rgba(240, 180, 41, 0.20), transparent 28%),
        linear-gradient(135deg, #f4efe4 0%, #efe7d7 45%, #e4dccb 100%);
      min-height: 100vh;
    }}
    .page {{
      width: min(1200px, calc(100% - 32px));
      margin: 0 auto;
      padding: 24px 0 48px;
    }}
    .hero {{
      background: linear-gradient(135deg, rgba(13, 92, 99, 0.97), rgba(18, 56, 63, 0.95));
      color: #f9f7f1;
      border-radius: 24px;
      padding: 28px;
      box-shadow: var(--shadow);
    }}
    .hero h1 {{
      margin: 0 0 8px;
      font-size: clamp(2rem, 4vw, 3.3rem);
      letter-spacing: 0.02em;
    }}
    .hero p {{
      margin: 0;
      max-width: 60ch;
      color: rgba(249, 247, 241, 0.84);
      line-height: 1.55;
    }}
    .top-nav {{
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      margin: 20px 0 24px;
    }}
    .top-nav a {{
      display: inline-flex;
      align-items: center;
      min-height: 40px;
      padding: 0 14px;
      border-radius: 999px;
      background: var(--panel);
      color: var(--accent);
      text-decoration: none;
      border: 1px solid rgba(13, 92, 99, 0.14);
      box-shadow: 0 8px 22px rgba(40, 34, 20, 0.06);
      font-size: 0.95rem;
    }}
    .top-nav a:hover {{
      background: var(--accent-soft);
    }}
    .top-nav a.is-active {{
      background: var(--accent);
      color: #f9f7f1;
    }}
    .summary-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      gap: 16px;
      margin: 24px 0;
    }}
    .summary-card, .section-card {{
      background: var(--panel);
      border: 1px solid rgba(31, 42, 42, 0.08);
      border-radius: 20px;
      box-shadow: var(--shadow);
      backdrop-filter: blur(5px);
    }}
    .summary-card {{
      padding: 18px 20px;
    }}
    .summary-card .eyebrow {{
      display: block;
      color: var(--muted);
      font-size: 0.82rem;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      margin-bottom: 8px;
    }}
    .summary-card strong {{
      font-size: 1.9rem;
      color: var(--accent);
    }}
    .section-grid {{
      display: grid;
      gap: 18px;
    }}
    .section-card {{
      padding: 22px;
      overflow: hidden;
    }}
    .section-card h2 {{
      margin: 0 0 8px;
      font-size: 1.55rem;
    }}
    .section-card p {{
      margin: 0 0 18px;
      color: var(--muted);
      line-height: 1.5;
    }}
    .table-wrap {{
      overflow-x: auto;
      border-radius: 16px;
      border: 1px solid rgba(31, 42, 42, 0.08);
      background: rgba(255, 255, 255, 0.72);
    }}
    table.data-table {{
      width: 100%;
      border-collapse: collapse;
      min-width: 720px;
      font-size: 0.95rem;
    }}
    .data-table thead th {{
      position: sticky;
      top: 0;
      background: #f7f4eb;
      color: var(--accent);
      text-transform: uppercase;
      letter-spacing: 0.05em;
      font-size: 0.77rem;
    }}
    .data-table th, .data-table td {{
      padding: 12px 14px;
      border-bottom: 1px solid rgba(31, 42, 42, 0.08);
      text-align: left;
      vertical-align: top;
    }}
    .data-table tbody tr:nth-child(even) {{
      background: rgba(13, 92, 99, 0.03);
    }}
    .section-link {{
      display: inline-block;
      margin-top: 14px;
      color: var(--accent);
      font-weight: bold;
      text-decoration: none;
    }}
    .section-link:hover {{
      color: #073b4c;
    }}
    .empty-state {{
      padding: 14px 16px;
      border-radius: 14px;
      background: rgba(240, 180, 41, 0.12);
      color: #7a5b08;
    }}
    @media (max-width: 720px) {{
      .page {{
        width: min(100% - 20px, 1200px);
      }}
      .hero {{
        padding: 22px;
        border-radius: 20px;
      }}
      .section-card {{
        padding: 18px;
      }}
      table.data-table {{
        min-width: 640px;
      }}
    }}
  </style>
</head>
<body>
  <main class="page">
    <section class="hero">
      <h1>{escape(title)}</h1>
      <p>Static OOTP front office output generated from the latest roster, stats, ratings, lineup, pitching, and transaction recommendations.</p>
    </section>
    {nav}
    {body}
  </main>
</body>
</html>
"""

    def _output_sections(self, outputs: DashboardOutputs) -> list[tuple[str, pd.DataFrame]]:
        return [
        (f"{self.mlb_team_name} hitters - current value", outputs.mlb_hitters_dashboard),
        (f"{self.mlb_team_name} pitchers - current value", outputs.mlb_pitchers_dashboard),
        (f"{self.aaa_team_name} hitters - promotion board", outputs.aaa_hitters_dashboard),
        (f"{self.aaa_team_name} pitchers - promotion board", outputs.aaa_pitchers_dashboard),
            ("Recommended lineup vs RHP", outputs.recommended_lineup_vs_rhp),
            ("Recommended lineup vs LHP", outputs.recommended_lineup_vs_lhp),
            ("Platoon diagnostics", outputs.platoon_diagnostics),
            ("Recommended rotation", outputs.recommended_rotation),
            ("Bullpen roles", outputs.recommended_bullpen_roles),
            ("Recommended transactions", outputs.recommended_transactions),
        ]

    def _write_html_outputs(self, outputs: DashboardOutputs) -> None:
        sections = self._output_sections(outputs)

        summary_cards = [
            (f"{self.mlb_team_name} hitters", len(outputs.mlb_hitters_dashboard)),
            (f"{self.mlb_team_name} pitchers", len(outputs.mlb_pitchers_dashboard)),
            (f"{self.aaa_team_name} hitters", len(outputs.aaa_hitters_dashboard)),
            (f"{self.aaa_team_name} pitchers", len(outputs.aaa_pitchers_dashboard)),
            ("Transactions", len(outputs.recommended_transactions)),
            ("Platoon notes", len(outputs.platoon_diagnostics)),
        ]
        summary_html = "".join(
            f'<article class="summary-card"><span class="eyebrow">{escape(label)}</span><strong>{value}</strong></article>'
            for label, value in summary_cards
        )

        overview_sections = []
        for title, df in sections:
            slug = self._slugify(title)
            preview = df.head(8)
            overview_sections.append(
                f"""
                <section class="section-card">
                  <h2>{escape(title)}</h2>
                  <p>{len(df)} rows available in this section.</p>
                  <div class="table-wrap">
                    {self.html_table(preview)}
                  </div>
                  <a class="section-link" href="{slug}.html">Open full section</a>
                </section>
                """
            )

        dashboard_body = f"""
        <section class="summary-grid">
          {summary_html}
        </section>
        <section class="section-grid">
          {''.join(overview_sections)}
        </section>
        """
        (self.out_dir / "dashboard.html").write_text(
            self._html_shell("OOTP GM Dashboard", dashboard_body, active_page="dashboard"),
            encoding="utf-8",
        )

        for title, df in sections:
            slug = self._slugify(title)
            body = f"""
            <section class="section-card">
              <h2>{escape(title)}</h2>
              <p>{len(df)} rows in this report.</p>
              <div class="table-wrap">
                {self.html_table(df)}
              </div>
            </section>
            """
            (self.out_dir / f"{slug}.html").write_text(
                self._html_shell(title, body, active_page=slug),
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
            .head(15)
        )

    @staticmethod
    def _build_aaa_hitter_dashboard(df: pd.DataFrame) -> pd.DataFrame:
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
            .head(15)
        )

    @staticmethod
    def _build_pitcher_dashboard(df: pd.DataFrame, score_col: str, include_potential: bool = False) -> pd.DataFrame:
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

    def build_outputs(self) -> DashboardOutputs:
        frames = self._load_team_frames()

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

        report = f"""# OOTP GM Dashboard

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
