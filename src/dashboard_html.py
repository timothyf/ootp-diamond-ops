from __future__ import annotations

from html import escape
import re

import pandas as pd

from src.dashboard_utils import slugify


def _format_cell_value(value: object, allow_html: bool) -> str:
    if pd.isna(value):
        return ""
    text = str(value)
    return text if allow_html else escape(text)


def _ordinal(value: object) -> str | None:
    if value is None or pd.isna(value):
        return None
    try:
        number = int(float(value))
    except (TypeError, ValueError):
        return None
    if 10 <= number % 100 <= 20:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(number % 10, "th")
    return f"{number}{suffix}"


def _format_games_back(value: object) -> str | None:
    if value is None or pd.isna(value):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number == 0:
        return "0"
    if number.is_integer():
        return str(int(number))
    return f"{number:.1f}"


def _team_logo_text(team_name: str) -> str:
    words = [part for part in str(team_name).replace("-", " ").split() if part]
    lowered = [word.lower() for word in words]
    if "tigers" in lowered:
        return "DET"
    if "mud" in lowered or "hens" in lowered:
        return "TOL"
    if words:
        primary = words[0][:3].upper()
        return primary if primary else "TM"
    return "TM"


def _team_logo_src(team_name: str) -> str | None:
    lowered = str(team_name).strip().lower()
    if "tiger" in lowered or "detroit" in lowered:
        return "../src/images/detroit-logo.png"
    if "toledo" in lowered or "mud hens" in lowered or "mud" in lowered or "hens" in lowered:
        return "../src/images/toledo-logo.png"
    return None


def _render_team_header_summary(summary: dict[str, object] | None, fallback_name: str) -> str:
    team_name = fallback_name
    record_text = "Record unavailable"
    position_text = "Position unavailable"
    gb_text = "GB unavailable"

    if summary:
        team_name = str(summary.get("team_name") or fallback_name)
        wins = summary.get("wins")
        losses = summary.get("losses")
        position = _ordinal(summary.get("position"))
        games_back = _format_games_back(summary.get("gb"))

        if wins is not None and losses is not None and not pd.isna(wins) and not pd.isna(losses):
            record_text = f"{int(float(wins))}-{int(float(losses))}"
        if position:
            position_text = position
        if games_back is not None:
            gb_text = games_back

    logo_src = _team_logo_src(team_name)
    logo_html = (
        f'<img class="hero-team-logo" src="{escape(logo_src)}" alt="{escape(team_name)} logo">'
        if logo_src
        else f'<span class="hero-team-logo hero-team-logo-fallback" aria-hidden="true">{escape(_team_logo_text(team_name))}</span>'
    )

    return (
        '<div class="hero-team-summary">'
        '<div class="hero-team-heading">'
        f"{logo_html}"
        f'<span class="hero-team-name">{escape(team_name)}</span>'
        "</div>"
        '<div class="hero-team-stats">'
        f'<span class="hero-team-stat"><strong>{escape(record_text)}</strong><small>Record</small></span>'
        f'<span class="hero-team-stat"><strong>{escape(position_text)}</strong><small>Position</small></span>'
        f'<span class="hero-team-stat"><strong>{escape(gb_text)}</strong><small>GB</small></span>'
        "</div>"
        "</div>"
    )


def html_table(
    df: pd.DataFrame,
    allow_html: bool = False,
    sortable: bool = True,
    highlight_starters: bool = False,
    column_modes: dict[str, list[str]] | None = None,
    column_labels: dict[str, str] | None = None,
    default_mode: str | None = None,
) -> str:
    if df.empty:
        return '<p class="empty-state">No rows</p>'

    column_modes = column_modes or {}
    column_labels = column_labels or {}
    mode_lookup = {column: mode for mode, columns in column_modes.items() for column in columns}
    table_mode = default_mode or (next(iter(column_modes.keys())) if column_modes else "")

    toggle_html = ""
    if column_modes:
        buttons = []
        for mode in column_modes:
            label = re.sub(r"[_-]+", " ", mode).title()
            active_class = " is-active" if mode == table_mode else ""
            buttons.append(
                f'<button type="button" class="table-toggle{active_class}" data-mode="{escape(mode)}">{escape(label)}</button>'
            )
        toggle_html = f'<div class="table-toggle-group">{"".join(buttons)}</div>'

    headers = []
    for column in df.columns:
        mode = mode_lookup.get(column, "shared")
        label = column_labels.get(column, "position" if column == "primary_position" else column)
        headers.append(
            f'<th data-column-mode="{escape(mode)}">{escape(str(label))}</th>'
        )

    rows = []
    for _, row in df.iterrows():
        cells = []
        for column in df.columns:
            mode = mode_lookup.get(column, "shared")
            cells.append(
                f'<td data-column-mode="{escape(mode)}">{_format_cell_value(row[column], allow_html)}</td>'
            )
        rows.append(f"<tr>{''.join(cells)}</tr>")

    return (
        f'{toggle_html}<table class="data-table" data-sortable="{"true" if sortable else "false"}" '
        f'data-highlight-starters="{"true" if highlight_starters else "false"}" '
        f'data-default-mode="{escape(table_mode)}"><thead><tr>{"".join(headers)}</tr></thead>'
        f'<tbody>{"".join(rows)}</tbody></table>'
    )


def build_html_shell(
    title: str,
    body: str,
    mlb_team_name: str,
    aaa_team_name: str,
    ootp_export_date: str | None,
    team_header_summaries: dict[str, dict[str, object] | None] | None = None,
    active_page: str | None = None,
    show_season_summary: bool = False,
) -> str:
    mlb_home_slug = slugify(f"{mlb_team_name} team")
    aaa_home_slug = slugify(f"{aaa_team_name} team")
    team_header_summaries = team_header_summaries or {"mlb": None, "aaa": None}
    logo_src = "../src/images/diamondops-logo.png"

    nav_items = [
        ("dashboard", "dashboard.html", "Dashboard"),
        (
            mlb_home_slug,
            f"{mlb_home_slug}.html",
            f"{mlb_team_name}",
        ),
        (
            aaa_home_slug,
            f"{aaa_home_slug}.html",
            f"{aaa_team_name}",
        ),
        ("team_needs", "team_needs.html", "Team Needs"),
    ]
    if show_season_summary:
        nav_items.append(("season_summary", "season_summary.html", "Season Summary"))
    nav_items.extend(
        [
        ("scoring_info", "scoring_info.html", "Scoring"),
        ("recommended_transactions", "recommended_transactions.html", "Transactions"),
        ]
    )
    nav_links = "".join(
        f'<a class="{"is-active" if key == active_page else ""}" href="{href}">{escape(label)}</a>'
        for key, href, label in nav_items
    )
    nav = f'<nav class="top-nav">{nav_links}</nav>'
    hero_team_summaries = (
        '<aside class="hero-status-panel">'
        f'<p class="hero-date">OOTP Date: {escape(ootp_export_date or "Unknown")}</p>'
        '<div class="hero-team-summaries">'
        f'{_render_team_header_summary(team_header_summaries.get("mlb"), mlb_team_name)}'
        f'{_render_team_header_summary(team_header_summaries.get("aaa"), aaa_team_name)}'
        "</div>"
        "</aside>"
    )
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
      width: min(1280px, calc(100% - 32px));
      margin: 0 auto;
      padding: 24px 0 48px;
    }}
    .hero {{
      background:
        radial-gradient(circle at 14% 28%, rgba(81, 177, 170, 0.16), transparent 24%),
        radial-gradient(circle at 78% 14%, rgba(155, 235, 255, 0.10), transparent 20%),
        linear-gradient(135deg, #0d6268 0%, #134f58 48%, #123b45 100%);
      color: #f9f7f1;
      border-radius: 32px;
      padding: 30px 34px;
      min-height: 0;
      display: grid;
      grid-template-columns: minmax(320px, 0.98fr) minmax(600px, 1.12fr);
      gap: 28px;
      align-items: center;
      box-shadow:
        0 28px 54px rgba(40, 34, 20, 0.14),
        inset 0 1px 0 rgba(255, 255, 255, 0.08);
      position: relative;
      overflow: hidden;
    }}

    .hero-brand {{
      display: flex;
      align-items: center;
      justify-content: flex-start;
      min-width: 0;
    }}
    .hero-logo {{
      width: min(340px, 28vw);
      height: auto;
      flex: 0 0 auto;
      display: block;
      filter: drop-shadow(0 18px 28px rgba(0, 0, 0, 0.24));
    }}
    .hero-copy {{
      min-width: 0;
      max-width: 340px;
    }}
    .hero h1 {{
      margin: 0;
      font-size: clamp(2rem, 3.2vw, 3rem);
      letter-spacing: 0.02em;
    }}
    .hero-status-panel {{
      justify-self: stretch;
      width: min(100%, 100%);
      max-width: 880px;
      padding: 4px 2px 8px;
    }}
    .hero-date {{
      margin: 0 0 20px;
      text-align: center;
      font-size: clamp(1.1rem, 1.9vw, 1.9rem);
      font-weight: 500;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      color: rgba(248, 244, 233, 0.95);
      text-shadow: 0 2px 14px rgba(0, 0, 0, 0.26);
    }}
    .hero-team-summaries {{
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 22px;
    }}
    .hero-team-summary {{
      padding: 20px 22px;
      border-radius: 28px;
      background:
        linear-gradient(180deg, rgba(255, 255, 255, 0.06), rgba(255, 255, 255, 0.03)),
        rgba(17, 72, 80, 0);
      border: 2px solid rgba(158, 231, 255, 0.7);
      color: rgba(249, 247, 241, 0.94);
      box-shadow:
        0 0 0 1px rgba(184, 239, 255, 0.18),
        0 0 22px rgba(126, 213, 245, 0.28),
        inset 0 0 28px rgba(193, 241, 255, 0.05);
    }}
    .hero-team-heading {{
      display: flex;
      align-items: center;
      gap: 12px;
      margin-bottom: 16px;
      min-width: 0;
    }}
    .hero-team-logo {{
      width: 52px;
      height: 52px;
      object-fit: contain;
      display: block;
      flex: 0 0 auto;
      filter: drop-shadow(0 6px 10px rgba(0, 0, 0, 0.2));
    }}
    .hero-team-logo-fallback {{
      display: inline-flex;
      align-items: center;
      justify-content: center;
      border-radius: 999px;
      background: linear-gradient(135deg, rgba(240, 180, 41, 0.9), rgba(198, 120, 27, 0.92));
      color: #13272b;
      font-size: 0.72rem;
      font-weight: 800;
      letter-spacing: 0.08em;
      box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.45);
    }}
    .hero-team-name {{
      display: block;
      font-weight: 700;
      letter-spacing: 0.02em;
      font-size: clamp(0.9rem, 1.1vw, 1.15rem);
      line-height: 1.1;
      color: #f7f4ea;
      text-shadow: 0 2px 10px rgba(0, 0, 0, 0.18);
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }}
    .hero-team-stats {{
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 14px;
    }}
    .hero-team-stat {{
      display: grid;
      gap: 4px;
      align-items: end;
      justify-items: center;
      min-height: 80px;
      padding: 10px 12px 14px;
      border-radius: 20px;
      background: rgba(14, 55, 63, 0.42);
      border: 1px solid rgba(168, 226, 245, 0.22);
      box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.06);
    }}
    .hero-team-stat strong {{
      font-size: clamp(1.02rem, 1.2vw, 1.25rem);
      line-height: 1.05;
      color: #f9f7f1;
      text-shadow: 0 2px 12px rgba(0, 0, 0, 0.18);
      white-space: nowrap;
    }}
    .hero-team-stat small {{
      font-size: 0.7rem;
      font-family: "Trebuchet MS", "Avenir Next", "Segoe UI", sans-serif;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      color: rgba(239, 236, 227, 0.78);
      text-align: center;
      font-weight: 700;
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
    .dashboard-overview {{
      display: grid;
      gap: 22px;
    }}
    .dashboard-group {{
      display: grid;
      gap: 12px;
    }}
    .dashboard-group-heading {{
      display: flex;
      align-items: center;
      justify-content: space-between;
    }}
    .dashboard-group-heading h2 {{
      margin: 0;
      font-size: 1.05rem;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      color: var(--muted);
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
      font-size: 0.7rem;
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
    .section-grid-overview {{
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 16px;
      align-items: start;
    }}
    .section-card {{
      padding: 22px;
      overflow: hidden;
    }}
    .section-card-compact {{
      padding: 16px 16px 14px;
      border-radius: 18px;
      box-shadow: 0 12px 28px rgba(40, 34, 20, 0.08);
    }}
    .section-card-header {{
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      gap: 12px;
      margin-bottom: 10px;
    }}
    .section-kicker {{
      margin: 0 0 4px;
      color: var(--muted);
      font-size: 0.72rem;
      text-transform: uppercase;
      letter-spacing: 0.08em;
    }}
    .section-card h2 {{
      margin: 0 0 8px;
      font-size: 1.55rem;
    }}
    .section-card-compact h2 {{
      margin: 0;
      font-size: 1.15rem;
      line-height: 1.25;
    }}
    .section-card p {{
      margin: 0 0 18px;
      color: var(--muted);
      line-height: 1.5;
    }}
    .section-meta-row {{
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin: 0 0 10px;
    }}
    .section-meta-pill {{
      display: inline-flex;
      align-items: center;
      min-height: 26px;
      padding: 0 10px;
      border-radius: 999px;
      background: rgba(13, 92, 99, 0.08);
      color: var(--accent);
      font-size: 0.8rem;
      font-weight: 600;
      letter-spacing: 0.02em;
    }}
    .table-wrap {{
      overflow-x: auto;
      border-radius: 16px;
      border: 1px solid rgba(31, 42, 42, 0.08);
      background: rgba(255, 255, 255, 0.72);
    }}
    .table-toggle-group {{
      display: inline-flex;
      gap: 8px;
      margin: 0 0 12px;
      padding: 4px;
      border-radius: 999px;
      background: rgba(13, 92, 99, 0.08);
    }}
    .table-toggle {{
      border: 0;
      border-radius: 999px;
      padding: 8px 14px;
      background: transparent;
      color: var(--muted);
      cursor: pointer;
      font: inherit;
    }}
    .table-toggle.is-active {{
      background: var(--link);
      color: #f9f7f1;
    }}
    .is-column-hidden {{
      display: none;
    }}
    table.data-table {{
      width: 100%;
      border-collapse: collapse;
      min-width: 720px;
      font-size: 0.95rem;
    }}
    .section-card-compact .table-wrap {{
      border-radius: 14px;
    }}
    .section-card-compact .table-toggle-group {{
      gap: 6px;
      margin-bottom: 8px;
      padding: 3px;
    }}
    .section-card-compact .table-toggle {{
      padding: 6px 10px;
      font-size: 0.7rem;
    }}
    .section-card-compact table.data-table {{
      min-width: 460px;
      font-size: 0.86rem;
    }}
    .data-table thead th {{
      position: sticky;
      top: 0;
      background: #f7f4eb;
      color: var(--ink);
      text-transform: uppercase;
      letter-spacing: 0.05em;
      font-size: 0.77rem;
            cursor: pointer;
            user-select: none;
    }}
        .data-table thead th.sort-asc::after {{
            content: " ▲";
            font-size: 0.7rem;
        }}
        .data-table thead th.sort-desc::after {{
            content: " ▼";
            font-size: 0.7rem;
        }}
    .data-table th, .data-table td {{
      padding: 12px 14px;
      border-bottom: 1px solid rgba(31, 42, 42, 0.08);
      text-align: left;
      vertical-align: top;
    }}
    .section-card-compact .data-table th,
    .section-card-compact .data-table td {{
      padding: 8px 10px;
    }}
    .data-table tbody tr:nth-child(even) {{
      background: rgba(13, 92, 99, 0.03);
    }}
        .data-table tbody tr.starter-row td {{
            background: rgba(240, 180, 41, 0.18);
            font-weight: 600;
        }}
        .data-table tbody tr.starter-row td:first-child {{
            box-shadow: inset 4px 0 0 var(--highlight);
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
    .section-link-inline,
    .section-link-inline:visited {{
      margin-top: 0;
      white-space: nowrap;
      font-size: 0.88rem;
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
        width: min(100% - 20px, 1280px);
      }}
      .hero {{
        grid-template-columns: 1fr;
        gap: 22px;
        padding: 22px;
        border-radius: 24px;
      }}
      .hero-brand {{
        justify-content: flex-start;
      }}
      .hero-logo {{
        width: min(250px, 68vw);
      }}
      .hero-copy {{
        max-width: none;
      }}
      .hero-status-panel {{
        justify-self: stretch;
        width: 100%;
        max-width: none;
      }}
      .hero-team-stats {{
        grid-template-columns: repeat(3, minmax(0, 1fr));
      }}
      .hero-team-summaries {{
        grid-template-columns: 1fr;
      }}
      .hero-team-summary {{
        padding: 18px;
      }}
      .hero-team-logo {{
        width: 44px;
        height: 44px;
      }}
      .hero-team-name {{
        font-size: 0.92rem;
      }}
      .hero-team-stat {{
        min-height: 100px;
        padding: 8px 10px 12px;
      }}
      .hero-team-stat small {{
        font-size: 0.76rem;
      }}
    .section-card {{
        padding: 18px;
      }}
      .section-grid-overview {{
        grid-template-columns: 1fr;
      }}
      table.data-table {{
        min-width: 640px;
      }}
      .section-card-compact table.data-table {{
        min-width: 420px;
      }}
    }}
  </style>
</head>
<body>
  <main class="page page-{escape(active_page or 'default')}">
    <section class="hero">
      <div class="hero-brand">
        <img class="hero-logo" src="{escape(logo_src)}" alt="DiamondOps logo">
      </div>
      {hero_team_summaries}
    </section>
    {nav}
    {body}
  </main>
</body>
<script>
(() => {{
    const applyColumnMode = (table, mode) => {{
        const cells = table.querySelectorAll('[data-column-mode]');
        cells.forEach((cell) => {{
            const cellMode = (cell.dataset.columnMode || 'shared').toLowerCase();
            const shouldShow = cellMode === 'shared' || !mode || cellMode === mode.toLowerCase();
            cell.classList.toggle('is-column-hidden', !shouldShow);
        }});
        table.dataset.activeMode = mode || '';
    }};

    const tables = document.querySelectorAll('table.data-table');

    const parseValue = (raw) => {{
        const text = (raw || '').trim();
        if (!text) return {{ type: 'text', value: '' }};

        const compact = text.replace(/,/g, '').replace(/%/g, '');
        const num = Number(compact);
        if (Number.isFinite(num) && /^[-+]?\\d*\\.?\\d+$/.test(compact)) {{
            return {{ type: 'number', value: num }};
        }}
        return {{ type: 'text', value: text.toLowerCase() }};
    }};

    tables.forEach((table) => {{
        const toggleGroup = table.previousElementSibling && table.previousElementSibling.classList.contains('table-toggle-group')
            ? table.previousElementSibling
            : null;
        if (toggleGroup) {{
            const defaultMode = table.dataset.defaultMode || '';
            applyColumnMode(table, defaultMode);
            Array.from(toggleGroup.querySelectorAll('.table-toggle')).forEach((button) => {{
                if ((button.dataset.mode || '') === defaultMode) {{
                    button.classList.add('is-active');
                }}
                button.addEventListener('click', () => {{
                    Array.from(toggleGroup.querySelectorAll('.table-toggle')).forEach((item) => item.classList.remove('is-active'));
                    button.classList.add('is-active');
                    applyColumnMode(table, button.dataset.mode || '');
                }});
            }});
        }}

        if ((table.dataset.highlightStarters || 'false').toLowerCase() === 'true') {{
            const tbody = table.tBodies && table.tBodies[0];
            if (tbody) {{
                Array.from(tbody.rows).forEach((row) => {{
                    const rankCell = row.cells[1] ? row.cells[1].innerText.trim() : '';
                    if (rankCell === '1') {{
                        row.classList.add('starter-row');
                    }}
                }});
            }}
        }}

        if ((table.dataset.sortable || 'true').toLowerCase() !== 'true') return;
        const thead = table.tHead;
        const tbody = table.tBodies && table.tBodies[0];
        if (!thead || !tbody || !thead.rows.length) return;

        const headers = Array.from(thead.rows[0].cells);
        const state = {{ index: -1, dir: 'asc' }};

        headers.forEach((th, index) => {{
            th.addEventListener('click', () => {{
                const rows = Array.from(tbody.rows);
                const dir = state.index === index && state.dir === 'asc' ? 'desc' : 'asc';
                state.index = index;
                state.dir = dir;

                headers.forEach((h) => h.classList.remove('sort-asc', 'sort-desc'));
                th.classList.add(dir === 'asc' ? 'sort-asc' : 'sort-desc');

                rows.sort((a, b) => {{
                    const aCell = a.cells[index] ? a.cells[index].innerText : '';
                    const bCell = b.cells[index] ? b.cells[index].innerText : '';
                    const av = parseValue(aCell);
                    const bv = parseValue(bCell);

                    let result = 0;
                    if (av.type === 'number' && bv.type === 'number') {{
                        result = av.value - bv.value;
                    }} else {{
                        result = av.value.localeCompare(bv.value, undefined, {{ numeric: true, sensitivity: 'base' }});
                    }}
                    return dir === 'asc' ? result : -result;
                }});

                rows.forEach((row) => tbody.appendChild(row));
            }});
        }});
    }});
}})();
</script>
</html>
"""
