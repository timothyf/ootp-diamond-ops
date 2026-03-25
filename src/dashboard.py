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
        if df.empty:
            return "_No rows_"
        return df.to_markdown(index=False)

    @staticmethod
    def html_table(df: pd.DataFrame, allow_html: bool = False) -> str:
        if df.empty:
            return '<p class="empty-state">No rows</p>'
        return df.to_html(index=False, classes=["data-table"], border=0, escape=not allow_html)

    @staticmethod
    def _round_score_columns(df: pd.DataFrame) -> pd.DataFrame:
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

    @staticmethod
    def _format_ip_columns(df: pd.DataFrame) -> pd.DataFrame:
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
        mlb_home_slug = self._slugify(f"{self.mlb_team_name} team")
        aaa_home_slug = self._slugify(f"{self.aaa_team_name} team")
        mlb_hitters_slug = self._slugify(f"{self.mlb_team_name} hitters - current value")
        mlb_pitchers_slug = self._slugify(f"{self.mlb_team_name} pitchers - current value")
        aaa_hitters_slug = self._slugify(f"{self.aaa_team_name} hitters - promotion board")
        aaa_pitchers_slug = self._slugify(f"{self.aaa_team_name} pitchers - promotion board")

        nav_items = [
            ("dashboard", "dashboard.html", "Dashboard"),
            (
                mlb_home_slug,
                f"{mlb_home_slug}.html",
                f"{self.mlb_team_name}",
            ),
            (
                aaa_home_slug,
                f"{aaa_home_slug}.html",
                f"{self.aaa_team_name}",
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
      --link: #2563a8;
      --link-hover: #1a4a80;
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
        .hero-date {{
            margin-top: 10px;
            display: inline-block;
            padding: 6px 12px;
            border-radius: 999px;
            border: 1px solid rgba(249, 247, 241, 0.24);
            background: rgba(249, 247, 241, 0.10);
            color: rgba(249, 247, 241, 0.96);
            font-size: 0.9rem;
            letter-spacing: 0.03em;
        }}
    .top-nav {{
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      margin: 20px 0 24px;
    }}
    .top-nav a,
    .top-nav a:visited {{
      display: inline-flex;
      align-items: center;
      min-height: 40px;
      padding: 0 14px;
      border-radius: 999px;
      background: var(--panel);
      color: var(--link);
      text-decoration: none;
      border: 1px solid rgba(37, 99, 168, 0.18);
      box-shadow: 0 8px 22px rgba(40, 34, 20, 0.06);
      font-size: 0.95rem;
    }}
    .top-nav a:hover {{
      background: #e8f0fb;
      color: var(--link);
      text-decoration: none;
    }}
    .top-nav a.is-active {{
      background: var(--link);
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
      color: var(--ink);
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
    .data-table a,
    .data-table a:visited {{
      color: var(--link);
      text-decoration: none;
    }}
    .data-table a:hover {{
      color: var(--link-hover);
      text-decoration: none;
    }}
    .section-link,
    .section-link:visited {{
      display: inline-block;
      margin-top: 14px;
      color: var(--link);
      font-weight: bold;
      text-decoration: none;
    }}
    .section-link:hover {{
      color: var(--link-hover);
      text-decoration: none;
    }}
    .narrative-card {{
      background: var(--accent-soft);
      border: 1px solid rgba(13, 92, 99, 0.18);
      border-radius: 16px;
      padding: 18px 22px;
      margin-bottom: 18px;
    }}
    .narrative-card h3 {{
      margin: 0 0 10px;
      font-size: 1.05rem;
      color: var(--link);
      text-transform: uppercase;
      letter-spacing: 0.06em;
    }}
    .narrative-intro {{
      margin: 0 0 10px;
      font-size: 1.02rem;
      line-height: 1.55;
      color: var(--ink);
    }}
    .narrative-list {{
      margin: 0;
      padding-left: 1.4em;
      line-height: 1.65;
      color: var(--ink);
    }}
    .narrative-list li {{
      margin-bottom: 5px;
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
      <h3>Baseball Operations Dashboard for OOTP</h3>
            <p class="hero-date">OOTP Date: {escape(self.ootp_export_date or 'Unknown')}</p>
    </section>
    {nav}
    {body}
  </main>
</body>
</html>
"""

    def _output_sections(self, outputs: DashboardOutputs) -> list[tuple[str, pd.DataFrame, str | None]]:
        frames = getattr(self, "_latest_frames", {})
        mlb_hitters_stats = self._build_hitter_standard_stats(frames.get("mlb_hitters", pd.DataFrame()))
        mlb_pitchers_stats = self._build_pitcher_standard_stats(frames.get("mlb_pitchers", pd.DataFrame()))
        aaa_hitters_stats = self._build_hitter_standard_stats(frames.get("aaa_hitters", pd.DataFrame()))
        aaa_pitchers_stats = self._build_pitcher_standard_stats(frames.get("aaa_pitchers", pd.DataFrame()))

        return [
            (f"{self.mlb_team_name} hitters - current value", outputs.mlb_hitters_dashboard, "mlb_hitters"),
            (f"{self.mlb_team_name} pitchers - current value", outputs.mlb_pitchers_dashboard, "mlb_pitchers"),
            (f"{self.aaa_team_name} hitters - promotion board", outputs.aaa_hitters_dashboard, "aaa_hitters"),
            (f"{self.aaa_team_name} pitchers - promotion board", outputs.aaa_pitchers_dashboard, "aaa_pitchers"),
            (f"{self.mlb_team_name} hitting stats", mlb_hitters_stats, "mlb_hitters"),
            (f"{self.mlb_team_name} pitching stats", mlb_pitchers_stats, "mlb_pitchers"),
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
        return (
            series.fillna("")
            .astype(str)
            .str.lower()
            .str.strip()
            .str.replace(r"[.,'`-]", "", regex=True)
            .str.replace(r"\\s+", " ", regex=True)
        )

    def _player_detail_filename(self, group: str, player_name: str) -> str:
        safe_name = self._slugify(player_name).replace("__", "_").strip("_")
        # Replace the 'mlb'/'aaa' prefix with the actual city name for readability.
        file_group = (
            group
            .replace("mlb_", f"{self.mlb_team_name.lower()}_")
            .replace("aaa_", f"{self.aaa_team_name.lower()}_")
        )
        return f"player_{file_group}_{safe_name}.html"

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
        """Return an HTML snippet summarising the major score drivers for a player."""

        def g(col: str, default: float = 0.0) -> float:
            v = row.get(col, default)
            return float(v) if v is not None and str(v) not in ("", "nan", "None") else default

        bullets: list[str] = []
        name = escape(str(row.get("player_name", "This player")))

        if "hitter" in group:
            score = g("overall_hitter_score")
            if score >= 12:
                tier = "<strong>elite</strong>"
            elif score >= 9:
                tier = "<strong>strong</strong>"
            elif score >= 6:
                tier = "<strong>above-average</strong>"
            elif score >= 3:
                tier = "<strong>average</strong>"
            elif score >= 0:
                tier = "<strong>below-average</strong>"
            else:
                tier = "<strong>poor</strong>"
            bullets.append(f"{name} grades as a {tier} hitter with an overall score of {score:.2f}.")

            pa = g("pa_val")
            ops = g("ops_val")
            obp = g("obp_val")
            slg = g("slg_val")
            if pa >= 20 and ops > 0:
                if ops >= 0.900:
                    bullets.append(f"Exceptional offensive production: {ops:.3f} OPS ({obp:.3f} OBP / {slg:.3f} SLG) over {int(pa)} PA &mdash; a major positive.")
                elif ops >= 0.800:
                    bullets.append(f"Solid offense: {ops:.3f} OPS ({obp:.3f} OBP / {slg:.3f} SLG) over {int(pa)} PA.")
                elif ops >= 0.700:
                    bullets.append(f"League-average offense: {ops:.3f} OPS over {int(pa)} PA.")
                else:
                    bullets.append(f"Below-average offense: {ops:.3f} OPS over {int(pa)} PA &mdash; a drag on the score.")
            else:
                offense = g("offense_score_regressed")
                if offense >= 8:
                    bullets.append("Ratings suggest elite offensive ability (no significant in-game PA sample yet).")
                elif offense >= 5:
                    bullets.append("Ratings suggest solid offensive ability (no significant in-game PA sample yet).")
                elif pa == 0:
                    bullets.append("No in-game PA recorded; score is driven entirely by scouting ratings.")

            bbpct = g("bbpct_val")
            kpct = g("kpct_val")
            if pa >= 30:
                if bbpct >= 0.12:
                    bullets.append(f"Elite walk rate ({bbpct*100:.1f}% BB) is a notable boost to the discipline component.")
                elif bbpct >= 0.09:
                    bullets.append(f"Good walk rate ({bbpct*100:.1f}% BB) adds to discipline.")
                if kpct >= 0.28:
                    bullets.append(f"High strikeout rate ({kpct*100:.1f}% K) is a meaningful negative for discipline.")
                elif kpct <= 0.15 and pa >= 50:
                    bullets.append(f"Low strikeout rate ({kpct*100:.1f}% K) provides a positive discipline impact.")

            plat_rhp = g("platoon_skill_rhp")
            plat_lhp = g("platoon_skill_lhp")
            if plat_rhp >= 8:
                bullets.append(f"Strong vs. RHP rating differential (+{plat_rhp:.1f}) boosts the platoon component.")
            elif plat_rhp <= -8:
                bullets.append(f"Weak vs. RHP rating differential ({plat_rhp:.1f}) slightly penalises the platoon component.")
            if plat_lhp >= 8:
                bullets.append(f"Strong vs. LHP rating differential (+{plat_lhp:.1f}) boosts the platoon component.")
            elif plat_lhp <= -8:
                bullets.append(f"Weak vs. LHP rating differential ({plat_lhp:.1f}) slightly penalises the platoon component.")

            def_comp = g("defensive_component")
            if def_comp >= 0.4:
                bullets.append(f"Defense is a positive contributor to overall value (component: +{def_comp:.2f}).")
            elif def_comp <= -0.4:
                bullets.append(f"Below-average defense reduces overall value (component: {def_comp:.2f}).")

            run_comp = g("running_component")
            if run_comp >= 0.35:
                bullets.append(f"Above-average speed and baserunning add value (running component: +{run_comp:.2f}).")
            elif run_comp <= -0.35:
                bullets.append(f"Below-average speed is a small negative (running component: {run_comp:.2f}).")

            age = g("age_val")
            age_bonus = g("age_bonus")
            if age > 0:
                if age <= 23:
                    bullets.append(f"Youth ({int(age)} years old) is a significant upside driver (age bonus: +{age_bonus:.2f}).")
                elif age <= 27:
                    bullets.append(f"Prime age ({int(age)}) provides a moderate projection boost (age bonus: +{age_bonus:.2f}).")
                elif age >= 35:
                    bullets.append(f"Age ({int(age)}) creates a headwind on projection score (age bonus: {age_bonus:.2f}).")

            reliability = g("hitting_reliability")
            if 0 < pa < 50:
                bullets.append(f"Very small sample ({int(pa)} PA) &mdash; performance results are heavily regressed to the median; ratings carry most of the weight.")
            elif reliability < 0.5 and pa > 0:
                bullets.append(f"Limited plate appearances ({int(pa)} PA) mean performance is partially regressed toward the median.")

        else:  # pitcher
            score = g("score")
            if score >= 12:
                tier = "<strong>elite</strong>"
            elif score >= 8:
                tier = "<strong>strong</strong>"
            elif score >= 4:
                tier = "<strong>above-average</strong>"
            elif score >= 0:
                tier = "<strong>average</strong>"
            else:
                tier = "<strong>below-average</strong>"
            pitch_role = str(row.get("pitch_role", "")).lower().strip()
            role_label = "starter" if pitch_role == "starter" else ("reliever" if pitch_role in ("reliever", "rp") else "swingman")
            bullets.append(f"{name} profiles as a {role_label} and grades as {tier} with a score of {score:.2f}.")

            ip = g("ip_val")
            era = g("era_val")
            fip = g("fip_val")
            whip = g("whip_val")
            if ip >= 5:
                if era > 0:
                    if era <= 3.00:
                        bullets.append(f"Outstanding ERA ({era:.2f}) is a major positive driver of the score.")
                    elif era <= 4.00:
                        bullets.append(f"Solid ERA ({era:.2f}) contributes positively to the score.")
                    elif era <= 5.00:
                        bullets.append(f"ERA ({era:.2f}) is above-average &mdash; a mild negative.")
                    else:
                        bullets.append(f"High ERA ({era:.2f}) is a significant drag on the score.")
                if fip > 0:
                    if fip <= 3.00:
                        bullets.append(f"Excellent FIP ({fip:.2f}) signals strong underlying performance independent of defence.")
                    elif fip <= 4.00:
                        bullets.append(f"Solid FIP ({fip:.2f}) supports the ERA narrative.")
                    elif fip >= 5.00:
                        bullets.append(f"Elevated FIP ({fip:.2f}) suggests ERA may be understating true run-prevention risk.")
                if whip > 0:
                    if whip <= 1.10:
                        bullets.append(f"Elite base-runner suppression (WHIP {whip:.2f}) is a positive.")
                    elif whip >= 1.50:
                        bullets.append(f"High WHIP ({whip:.2f}) indicates poor base-runner control.")
            elif ip > 0:
                bullets.append(f"Very limited sample ({ip:.0f} IP) &mdash; raw results carry little weight; ratings and components drive the score.")

            k9 = g("k_9_val")
            bb9 = g("bb_9_val")
            kbb9 = g("k_bb_9_val")
            if ip >= 5:
                if k9 >= 10.0:
                    bullets.append(f"Elite strikeout rate (K/9: {k9:.1f}) is a top positive contributor.")
                elif k9 >= 8.0:
                    bullets.append(f"Strong strikeout rate (K/9: {k9:.1f}) aids the command-dominance component.")
                elif k9 <= 5.0:
                    bullets.append(f"Low strikeout rate (K/9: {k9:.1f}) limits the command-dominance score.")

                if bb9 <= 2.0:
                    bullets.append(f"Outstanding command (BB/9: {bb9:.1f}) significantly boosts the command-dominance component.")
                elif bb9 >= 4.5:
                    bullets.append(f"High walk rate (BB/9: {bb9:.1f}) is a notable negative for command-dominance.")

                if kbb9 >= 4.0:
                    bullets.append(f"Dominant K-BB/9 ({kbb9:.1f}) &mdash; elite command-strikeout profile.")
                elif kbb9 >= 2.5:
                    bullets.append(f"Good K-BB/9 ({kbb9:.1f}) reflects solid command and strikeout balance.")
                elif kbb9 < 0 and ip >= 10:
                    bullets.append(f"Negative K-BB/9 ({kbb9:.1f}) &mdash; walks are outpacing strikeouts, a significant concern.")

            gb_share = g("gb_share_val")
            if gb_share >= 0.55:
                bullets.append(f"Strong ground-ball tendency ({gb_share*100:.0f}% GB rate) helps suppress HR risk and aids contact management.")
            elif 0 < gb_share <= 0.35:
                bullets.append(f"Fly-ball pitcher ({gb_share*100:.0f}% GB rate) &mdash; elevated HR exposure slightly penalises contact management.")

            stuff = g("stuff_now")
            movement = g("movement_now")
            control = g("control_now")
            if stuff > 0 or movement > 0 or control > 0:
                rtg = stuff * 0.45 + movement * 0.25 + control * 0.30
                if rtg >= 55:
                    bullets.append(f"Strong pitch ratings (Stuff {int(stuff)} / Mvt {int(movement)} / Ctl {int(control)}) provide a solid floor for the ratings component.")
                elif rtg >= 45:
                    bullets.append(f"Average pitch ratings (Stuff {int(stuff)} / Mvt {int(movement)} / Ctl {int(control)}).")
                else:
                    bullets.append(f"Below-average pitch ratings (Stuff {int(stuff)} / Mvt {int(movement)} / Ctl {int(control)}) weigh on the ratings component.")

            gs = g("gs_val")
            if gs >= 10:
                bullets.append(f"Durable innings workload ({int(gs)} GS, {ip:.0f} IP) adds to the durability component.")
            elif ip >= 30 and gs == 0:
                bullets.append(f"Reliable reliever ({ip:.0f} IP, 0 GS) &mdash; workload adds to durability.")

            age = g("age_val")
            age_bonus = g("age_bonus")
            if age > 0:
                if age <= 25:
                    bullets.append(f"Young pitcher ({int(age)}) &mdash; projection score benefits from age upside (bonus: +{age_bonus:.2f}).")
                elif age >= 34:
                    bullets.append(f"Age ({int(age)}) slightly suppresses the projection score (age bonus: {age_bonus:.2f}).")

            reliability = g("pitching_reliability")
            if 0 < ip < 10:
                bullets.append(f"Very small sample ({ip:.0f} IP) &mdash; results are heavily regressed toward the median.")
            elif reliability < 0.5 and ip > 0:
                bullets.append(f"Limited innings ({ip:.0f} IP) &mdash; score is partially regressed toward the median.")

        if not bullets:
            return ""

        intro, *rest = bullets
        html = f'<p class="narrative-intro">{intro}</p>'
        if rest:
            html += '<ul class="narrative-list">' + "".join(f"<li>{b}</li>" for b in rest) + "</ul>"
        return html

    @staticmethod
    def _component_rows(
        frame_row: pd.Series,
        fields: list[tuple[str, str] | tuple[str, str, str]],
        include_weight: bool = False,
    ) -> pd.DataFrame:
        rows = []
        for field in fields:
            if len(field) == 3:
                label, col, weight = field
            else:
                label, col = field
                weight = ""
            if col not in frame_row.index:
                continue
            value = frame_row[col]
            if pd.isna(value):
                continue
            numeric_value = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
            if pd.notna(numeric_value):
                if "score" in col.lower():
                    value = f"{float(numeric_value):.2f}"
                else:
                    value = round(float(numeric_value), 4)
            row = {"component": label, "value": value}
            if include_weight:
                row["weight"] = weight
            rows.append(row)
        return pd.DataFrame(rows)

    def _write_player_detail_pages(self, group_frames: dict[str, pd.DataFrame]) -> dict[str, dict[str, str]]:
        hitter_fields = [
            ("Overall Score", "overall_hitter_score", "computed"),
            ("Projection Score", "projection_hitter_score", "computed"),
            ("Offense Score", "offense_score", "feeds regressed offense"),
            ("Regressed Offense", "offense_score_regressed", "0.60 overall / 0.28 projection"),
            ("Current Ratings", "ratings_hitter_now", "0.22 overall / 0.27 projection"),
            ("Future Ratings", "ratings_hitter_future", "0.34 projection"),
            ("Discipline Component", "discipline_component", "0.80 overall / 0.90 projection"),
            ("Platoon Skill Component", "platoon_skill_component", "0.60 overall / 0.70 projection"),
            ("Defensive Component", "defensive_component", "0.50 overall / 0.35 projection"),
            ("Running Component", "running_component", "0.25 overall / 0.20 projection"),
            ("Scarcity Bonus", "scarcity_bonus", "0.40 overall"),
            ("Age Bonus", "age_bonus", "0.50 projection"),
            ("Select Score vs RHP", "select_score_rhp", "selection logic only"),
            ("Select Score vs LHP", "select_score_lhp", "selection logic only"),
        ]
        pitcher_fields = [
            ("Current Score", "score", "computed"),
            ("Projection Score", "projection_pitcher_score", "computed"),
            ("Results Score", "results_pitcher_score", "feeds regressed results"),
            ("Regressed Results", "results_pitcher_score_regressed", "0.58 score / 0.26 projection"),
            ("Current Ratings", "ratings_pitcher_now", "0.30 score / 0.24 projection"),
            ("Future Ratings", "ratings_pitcher_future", "0.34 projection"),
            ("Command Component", "command_dominance_component", "0.20 score / 0.22 projection"),
            ("Contact Management", "contact_management_component", "0.14 score / 0.14 projection"),
            ("Durability", "durability_component", "0.12 score / 0.10 projection"),
            ("Reliability", "pitching_reliability", "regression factor (k=45)"),
            ("Age Bonus", "age_bonus", "0.50 projection"),
            ("K/9", "k_9_val", "input metric"),
            ("BB/9", "bb_9_val", "input metric"),
            ("HR/9", "hr_9_val", "input metric"),
            ("K-BB/9", "k_bb_9_val", "input metric"),
            ("GB Share", "gb_share_val", "input metric"),
        ]

        link_maps: dict[str, dict[str, str]] = {}
        for group, frame in group_frames.items():
            if frame.empty or "player_name" not in frame.columns:
                link_maps[group] = {}
                continue

            fields = hitter_fields if "hitter" in group else pitcher_fields
            link_maps[group] = {}
            keyed = frame.copy()
            keyed["player_lookup"] = self._normalize_key(keyed["player_name"])

            for _, row in keyed.iterrows():
                player_name = str(row["player_name"])
                lookup = str(row["player_lookup"])
                filename = self._player_detail_filename(group, player_name)
                components = self._component_rows(row, fields, include_weight=True)

                summary_fields = [
                    ("Position", "primary_position"),
                    ("Age", "age_val"),
                    ("Bats", "bats"),
                    ("Throws", "throws"),
                    ("Injury", "injury_text"),
                ]
                summary = self._component_rows(row, summary_fields)

                narrative_html = self._score_narrative(row, group)
                narrative_section = (
                    f'<div class="narrative-card"><h3>Score Summary</h3>{narrative_html}</div>'
                    if narrative_html
                    else ""
                )
                body = f"""
                <section class=\"section-card\">
                  <h2>{escape(player_name)} - Score Components</h2>
                  <p>Detailed component breakdown for {escape(group.replace('_', ' '))}.</p>
                  <div class=\"table-wrap\">{self.html_table(summary)}</div>
                </section>
                <section class=\"section-card\">
                  <h2>Score Analysis</h2>
                  {narrative_section}
                  <h3 style=\"margin:18px 0 8px;font-size:1rem;\">Component Values</h3>
                  <div class=\"table-wrap\">{self.html_table(components)}</div>
                  <a class=\"section-link\" href=\"dashboard.html\">Back to dashboard</a>
                </section>
                """
                (self.out_dir / filename).write_text(
                    self._html_shell(f"{player_name} component breakdown", body),
                    encoding="utf-8",
                )
                link_maps[group][lookup] = filename
        return link_maps

    def _write_html_outputs(self, outputs: DashboardOutputs) -> None:
        sections = self._output_sections(outputs)
        frames = getattr(self, "_latest_frames", {})
        player_links = self._write_player_detail_pages(frames) if isinstance(frames, dict) else {}
        mlb_home_slug = self._slugify(f"{self.mlb_team_name} team")
        aaa_home_slug = self._slugify(f"{self.aaa_team_name} team")

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
        for title, df, group in sections:
            slug = self._slugify(title)
            preview = df.head(8)
            linked_preview = self._link_player_names(preview, player_links.get(group, {})) if group else preview
            overview_sections.append(
                f"""
                <section class="section-card">
                  <h2>{escape(title)}</h2>
                  <p>{len(df)} rows available in this section.</p>
                  <div class="table-wrap">
                    {self.html_table(linked_preview, allow_html=True)}
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
                {self.html_table(linked_df, allow_html=True)}
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
            .assign(pa=lambda x: x["pa"].fillna(0).round().astype(int))
            .head(15)
        )

    @staticmethod
    def _build_hitter_standard_stats(df: pd.DataFrame) -> pd.DataFrame:
        if df.empty:
            return pd.DataFrame()

        cols = [
            "player_name",
            "primary_position",
            "g",
            "pa",
            "ab",
            "h",
            "2b",
            "3b",
            "hr",
            "rbi",
            "r",
            "bb",
            "k",
            "sb",
            "cs",
            "avg",
            "obp",
            "slg",
            "ops",
            "war",
            "injury_text",
        ]
        present_cols = [c for c in cols if c in df.columns]
        stats = (
            df.loc[df["is_hitter"] & (df["pa"] > 0)]
            .sort_values(["pa", "ops"], ascending=[False, False])[present_cols]
            .copy()
        )
        int_cols = [c for c in ["g", "pa", "ab", "h", "2b", "3b", "hr", "rbi", "r", "bb", "k", "sb", "cs"] if c in stats.columns]
        for col in int_cols:
            stats[col] = stats[col].fillna(0).round().astype(int)
        return stats

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
            .assign(pa=lambda x: x["pa"].fillna(0).round().astype(int))
            .head(15)
        )

    @staticmethod
    def _build_pitcher_standard_stats(df: pd.DataFrame) -> pd.DataFrame:
        if df.empty:
            return pd.DataFrame()

        cols = [
            "player_name",
            "primary_position",
            "g",
            "gs",
            "w",
            "l",
            "sv",
            "hld",
            "ip",
            "ha",
            "hr",
            "er",
            "bb",
            "k",
            "era",
            "fip",
            "whip",
            "k_9",
            "bb_9",
            "hr_9",
            "war",
            "injury_text",
        ]
        present_cols = [c for c in cols if c in df.columns]
        stats = (
            df.loc[df["is_pitcher"] & (df["ip"] > 0)]
            .sort_values(["ip", "era"], ascending=[False, True])[present_cols]
            .copy()
        )
        int_cols = [c for c in ["g", "gs", "w", "l", "sv", "hld", "ha", "hr", "er", "bb", "k"] if c in stats.columns]
        for col in int_cols:
            stats[col] = stats[col].fillna(0).round().astype(int)
        return stats

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
