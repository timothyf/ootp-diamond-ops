from __future__ import annotations

from html import escape
from pathlib import Path
from typing import Callable

import pandas as pd

from src.dashboard_types import CompletedSeasonSummary, CompletedSeasonTeamSummary, DashboardOutputs, DashboardSection


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
        completed_season_summary: CompletedSeasonSummary | None = None,
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
        self.completed_season_summary = completed_season_summary

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

        hitter_spread = 2.0
        hitter_current_formula = self._pct(
            (0.52 + 0.80 + 0.08) * hitter_spread,
            (0.22 + 0.60 + 0.50 + 0.25) * hitter_spread,
            0.40 * hitter_spread,
        )
        hitter_projection_formula = self._pct(
            (0.58 + 0.90 + 0.04) * hitter_spread,
            (0.27 + 0.48 + 0.70 + 0.35 + 0.20) * hitter_spread,
            (0.50 + 0.35) * hitter_spread,
        )

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
            0.35
            + 0.20 * (command_stats / (command_stats + command_ratings))
            + 0.14 * (contact_stats / (contact_stats + contact_ratings))
            + 0.08 * (durability_stats / (durability_stats + durability_ratings))
        )
        pitcher_projection_ratings_weight = (
            0.18
            + 0.40
            + 0.20 * (command_ratings / (command_stats + command_ratings))
            + 0.12 * (contact_ratings / (contact_stats + contact_ratings))
            + 0.08 * (durability_ratings / (durability_stats + durability_ratings))
        )
        pitcher_projection_formula = self._pct(pitcher_projection_stats_weight, pitcher_projection_ratings_weight, 0.45)

        h = hitters
        hitter_current_empirical = self._normalized_share(
            {
                "offense": ("stats", self._series(h, "offense_score_regressed") * 0.52),
                "discipline": ("stats", self._series(h, "discipline_component") * 0.80),
                "contact_quality": ("stats", self._series(h, "contact_quality_component") * 0.08),
                "ratings_now": ("ratings", self._series(h, "ratings_hitter_now_component") * 0.22),
                "platoon": ("ratings", self._series(h, "platoon_skill_component") * 0.60),
                "defense": ("ratings", self._series(h, "defensive_component") * 0.50),
                "running": ("ratings", self._series(h, "running_component") * 0.25),
                "scarcity": ("other", self._series(h, "scarcity_bonus") * 0.40),
            }
        )
        hitter_projection_empirical = self._normalized_share(
            {
                "offense": ("stats", self._series(h, "offense_score_regressed") * 0.58),
                "discipline": ("stats", self._series(h, "discipline_component") * 0.90),
                "contact_quality": ("stats", self._series(h, "contact_quality_component") * 0.04),
                "ratings_now": ("ratings", self._series(h, "ratings_hitter_now_component") * 0.27),
                "ratings_future": ("ratings", self._series(h, "ratings_hitter_future_component") * 0.48),
                "platoon": ("ratings", self._series(h, "platoon_skill_component") * 0.70),
                "defense": ("ratings", self._series(h, "defensive_component") * 0.35),
                "running": ("ratings", self._series(h, "running_component") * 0.20),
                "age": ("other", self._series(h, "age_bonus") * 0.50),
                "scarcity": ("other", self._series(h, "scarcity_bonus") * 0.35),
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
                "ratings_now": ("ratings", self._series(p, "ratings_pitcher_now_component") * 0.30),
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
                "results": ("stats", self._series(p, "results_pitcher_score_regressed") * 0.35),
                "ratings_now": ("ratings", self._series(p, "ratings_pitcher_now_component") * 0.18),
                "ratings_future": ("ratings", self._series(p, "ratings_pitcher_future_component") * 0.40),
                "age": ("other", self._series(p, "age_bonus") * 0.45),
                "command_stat": ("stats", command_stat * 0.18),
                "command_ratings": ("ratings", command_ratings * 0.18),
                "contact_stat": ("stats", contact_stat * 0.12),
                "contact_ratings": ("ratings", contact_ratings * 0.12),
                "durability_stat": ("stats", durability_stat * 0.08),
                "durability_ratings": ("ratings", durability_ratings * 0.08),
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

    @staticmethod
    def _playoff_result_text(summary: CompletedSeasonTeamSummary) -> str:
        if summary.won_playoffs:
            return "Won the league championship."
        if summary.made_playoffs:
            return "Reached the postseason."
        return "Missed the postseason."

    @staticmethod
    def _season_summary_card(label: str, value: str) -> str:
        return (
            '<article class="summary-card">'
            f'<span class="eyebrow">{escape(label)}</span>'
            f"<strong>{escape(value)}</strong>"
            "</article>"
        )

    def _season_team_section(self, summary: CompletedSeasonTeamSummary) -> str:
        record_text = "N/A"
        if summary.wins is not None and summary.losses is not None:
            record_text = f"{summary.wins}-{summary.losses}"

        position_text = "N/A"
        if summary.position is not None:
            suffix = "th"
            if 10 <= summary.position % 100 <= 20:
                suffix = "th"
            else:
                suffix = {1: "st", 2: "nd", 3: "rd"}.get(summary.position % 10, "th")
            position_text = f"{summary.position}{suffix}"

        gb_text = "N/A"
        if summary.gb is not None:
            gb_text = str(int(summary.gb)) if float(summary.gb).is_integer() else f"{float(summary.gb):.1f}"

        top_names = [
            ("Best hitter", summary.best_hitter or "Not available"),
            ("Best pitcher", summary.best_pitcher or "Not available"),
            ("Best rookie", summary.best_rookie or "Not available"),
        ]
        spotlight_rows = "".join(
            f"<tr><th>{escape(label)}</th><td>{escape(value)}</td></tr>"
            for label, value in top_names
        )

        return f"""
        <section class="section-card">
          <h2>{escape(summary.team_name)}</h2>
          <p>{escape(self._playoff_result_text(summary))}</p>
          <section class="summary-grid">
            {self._season_summary_card("Record", record_text)}
            {self._season_summary_card("Position", position_text)}
            {self._season_summary_card("GB", gb_text)}
            {self._season_summary_card("Postseason", "Yes" if summary.made_playoffs else "No")}
          </section>
          <div class="table-wrap">
            <table class="data-table" data-sortable="false" data-highlight-starters="false" data-default-mode="">
              <thead><tr><th>Season spotlight</th><th>Selection</th></tr></thead>
              <tbody>{spotlight_rows}</tbody>
            </table>
          </div>
        </section>
        """

    def _write_season_summary_page(self) -> None:
        season_summary_path = self.out_dir / "season_summary.html"
        if self.completed_season_summary is None:
            if season_summary_path.exists():
                season_summary_path.unlink()
            return

        summary = self.completed_season_summary
        body = f"""
        <section class="dashboard-overview">
          <section class="section-card">
            <h2>{summary.season_year} Season Summary</h2>
            <p>
              This page appears when the OOTP history tables show that the {summary.season_year} season has been
              completed for both the MLB and AAA clubs. It gives a quick end-of-season snapshot of record, finish,
              postseason result, and key award-style standouts for each team.
            </p>
            <div class="section-meta-row">
              <span class="section-meta-pill">{summary.season_year} completed season</span>
              <span class="section-meta-pill">{escape(summary.mlb.team_name)}</span>
              <span class="section-meta-pill">{escape(summary.aaa.team_name)}</span>
            </div>
          </section>
          {self._season_team_section(summary.mlb)}
          {self._season_team_section(summary.aaa)}
        </section>
        """
        season_summary_path.write_text(
            self.html_shell(f"{summary.season_year} Season Summary", body, "season_summary"),
            encoding="utf-8",
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
                        The "Other" bucket includes score baseline offset and context bonuses (for example,
                        scarcity or age).
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
                            Constant offsets have zero empirical variance and therefore do not contribute here.
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
    def _dashboard_bucket(section: DashboardSection) -> str | None:
        title = section.title
        lower_title = title.lower()
        if title in {"Team needs", "Recommended transactions", "Recommended lineup vs RHP", "Recommended rotation"}:
            return "Decisions now"
        if section.group == "mlb_hitters" and "lineup" not in lower_title and "platoon" not in lower_title:
            return "MLB snapshot"
        if section.group == "mlb_pitchers" and "rotation" not in lower_title and "bullpen" not in lower_title:
            return "MLB snapshot"
        if section.group and section.group.startswith("aaa_") and "lineup" not in lower_title:
            return "AAA watchlist"
        return None

    @staticmethod
    def _dashboard_bucket_order(label: str) -> int:
        return {
            "Decisions now": 0,
            "MLB snapshot": 1,
            "AAA watchlist": 2,
        }.get(label, 99)

    @staticmethod
    def _format_snapshot_value(value: object) -> str:
        if pd.isna(value):
            return ""
        if isinstance(value, (int, float)):
            number = float(value)
            return f"{number:.2f}" if not number.is_integer() else str(int(number))
        return str(value)

    def _section_snapshot_text(self, section: DashboardSection) -> str:
        if section.df.empty:
            return "No rows in this report yet."

        first_row = section.df.iloc[0]
        title = section.title
        if title == "Team needs":
            priority = str(first_row.get("priority", "")).strip()
            area = str(first_row.get("area", "")).strip()
            need = str(first_row.get("need", "")).strip()
            return f"Top issue: {priority} priority in {area.lower()} - {need}."
        if title == "Recommended transactions":
            move_type = str(first_row.get("move_type", "Recommended move")).strip()
            player = str(first_row.get("player_name", "")).strip()
            return f"Lead move: {move_type}{f' involving {player}' if player else ''}."
        if "lineup" in title.lower():
            leadoff = str(first_row.get("player_name", "")).strip()
            return f"Starts with {leadoff} at the top of the order." if leadoff else "Review the preferred batting order."
        if title == "Recommended rotation":
            ace = str(first_row.get("player_name", "")).strip()
            return f"Current rotation starts with {ace}." if ace else "Review the current five-man plan."
        if title == "Bullpen roles":
            reliever = str(first_row.get("player_name", "")).strip()
            role = str(first_row.get("role", "")).strip()
            return f"Late innings currently run through {reliever}{f' as {role}' if role else ''}." if reliever else "Review the bullpen pecking order."
        if "depth chart" in title.lower():
            starter = str(first_row.get("player_name", "")).strip()
            position = str(first_row.get("position", "")).strip()
            return f"Current first-choice {position} is {starter}." if starter else "Review the active depth chart."

        player = str(first_row.get("player_name", "")).strip()
        for score_col in ("score", "overall_hitter_score", "projection_hitter_score", "rotation_score", "bullpen_score", "projection_pitcher_score"):
            if score_col in section.df.columns and not pd.isna(first_row.get(score_col)):
                score = self._format_snapshot_value(first_row.get(score_col))
                return f"Top name right now: {player} ({score})." if player else f"Top score in this report: {score}."
        return f"Top name right now: {player}." if player else f"Open {title.lower()} for the full report."

    @staticmethod
    def _overview_group_label(section: DashboardSection) -> str:
        if section.title == "Team needs":
            return "Decisions"
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
    def _section_description(section: DashboardSection) -> str | None:
        lineup_description = (
            "This lineup first locks in the best healthy regulars at the premium defensive spots, "
            "then compares the best first base, left field, right field, and DH combinations for that "
            "pitcher handedness, giving extra credit to hitters whose handedness and split profile fit "
            "the matchup well. After the nine players are chosen, the batting "
            "order is set from role-based scores: the best leadoff candidate goes first, the best "
            "remaining top-of-order fit goes second, the strongest overall middle-of-order bat fills "
            "the three spot, the best cleanup fit hits fourth, and the remaining hitters are ordered "
            "by overall value and offensive profile."
        )
        descriptions = {
            "Recommended lineup vs RHP": lineup_description,
            "Recommended lineup vs LHP": lineup_description,
            "Team needs": (
                "This page highlights the club's most urgent acquisition needs by comparing the current MLB roster "
                "with AAA depth using current scores, projection scores, recent production, age, and handedness. "
                "Each row points to a roster area where external help could most meaningfully improve the organization."
            ),
            "Recommended rotation": (
                "This rotation ranks pitchers by overall staff value, then gives extra credit to "
                "starters who have built real innings, made starts, and shown the stamina to turn "
                "a lineup over multiple times. The final order favors the best true starters first, "
                "with swingman depth filling in after the core rotation arms."
            ),
            "Bullpen roles": (
                "These bullpen roles start from each pitcher's overall staff value, then add relief-"
                "specific credit for saves, holds, and a true reliever profile. The highest-rated "
                "late-inning relievers rise to the top, while the remaining arms are slotted beneath "
                "them based on overall bullpen fit."
            ),
            "Recommended transactions": (
                "This page groups the most actionable roster moves by transaction family so you can quickly scan "
                "promotions, corresponding MLB exits, and cases where the organization likely needs outside help."
            ),
        }
        return descriptions.get(section.title)

    def _rotation_candidate_table(self, frames: dict[str, pd.DataFrame], player_links: dict[str, dict[str, str]]) -> str:
        frame = frames.get("mlb_pitchers", pd.DataFrame()) if isinstance(frames, dict) else pd.DataFrame()
        if frame.empty:
            return ""

        pool = frame.loc[frame["is_pitcher"] & ~frame["injured_flag"] & (frame["ip_val"] > 0)].copy()
        if pool.empty:
            return ""

        chosen_names = set()
        rotation_frame = frames.get("_recommended_rotation", pd.DataFrame()) if isinstance(frames, dict) else pd.DataFrame()
        if isinstance(rotation_frame, pd.DataFrame) and not rotation_frame.empty and "player_name" in rotation_frame.columns:
            chosen_names = {
                str(name)
                for name in rotation_frame["player_name"].tolist()
                if str(name).strip() and str(name).strip() != "OPEN / BULK ROLE"
            }

        candidates = pool.loc[
            ~pool["player_name"].isin(chosen_names)
            & (pool["true_starter_flag"] | pool["swingman_flag"] | ((pool["gs_val"] >= 1) & (pool["stamina_now"] >= 50)))
        ].copy()
        if candidates.empty:
            return ""

        candidates["candidate_type"] = candidates["true_starter_flag"].map({True: "Starter depth", False: "Swingman / spot start"})
        candidates = (
            candidates.sort_values(
                ["true_starter_flag", "rotation_score", "ip_val", "gs_val"],
                ascending=[False, False, False, False],
            )[
                ["candidate_type", "player_name", "ip_val", "gs_val", "stamina_now", "era_val", "fip_val", "rotation_score"]
            ]
            .rename(
                columns={
                    "ip_val": "ip",
                    "gs_val": "gs",
                    "stamina_now": "stamina",
                    "era_val": "era",
                    "fip_val": "fip",
                }
            )
            .head(6)
            .reset_index(drop=True)
        )
        candidates = self.format_ip_columns(self.round_score_columns(candidates))
        linked_candidates = self.link_player_names(candidates, player_links.get("mlb_pitchers", {}))
        return f"""
        <section class="section-card">
          <h2>Spot Starter / Replacement Candidates</h2>
          <p>Best healthy MLB options outside the current five-man rotation if you need a spot start or replacement starter.</p>
          <div class="table-wrap">
            {self.html_table(linked_candidates, allow_html=True)}
          </div>
        </section>
        """

    @staticmethod
    def _overview_preview_columns(section: DashboardSection) -> list[str] | None:
        preview_columns = {
            "Team needs": ["priority", "area", "need", "internal_options"],
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

    @staticmethod
    def _team_hub_bucket(section: DashboardSection, prefix: str) -> str | None:
        lower_title = section.title.lower()
        if prefix == "mlb_":
            if section.title in {"Team needs", "Recommended transactions", "Recommended lineup vs RHP", "Recommended lineup vs LHP", "Platoon diagnostics"}:
                return "Planning & decisions"
            if section.group == "mlb_hitters" and "lineup" not in lower_title and "platoon" not in lower_title:
                return "Position players"
            if section.group == "mlb_pitchers":
                return "Pitching"
            return None

        if prefix == "aaa_":
            if section.group == "aaa_hitters":
                return "Position players"
            if section.group == "aaa_pitchers":
                return "Pitching"
            if section.title in {"Team needs", "Recommended transactions"}:
                return "Planning & decisions"
        return None

    def _team_hub_intro(self, team_name: str, prefix: str, grouped_sections: dict[str, list[DashboardSection]]) -> str:
        club_type = "MLB" if prefix == "mlb_" else "AAA"
        return (
            f"This {club_type} hub keeps {team_name}'s reports organized by roster area so you can move from "
            f"summary to player boards to planning pages without jumping across unrelated reports."
        )

    @staticmethod
    def _transaction_category(move_type: object) -> str:
        text = str(move_type or "").strip().upper()
        if text.startswith("CALL UP"):
            return "Call Ups"
        if text.startswith("SEND DOWN"):
            return "Send Downs"
        if text.startswith("DFA / BENCH"):
            return "DFA / Bench"
        if text.startswith("ACQUIRE"):
            return "External Acquisitions"
        return "Other"

    def _recommended_transactions_tables(self, df: pd.DataFrame) -> str:
        if df.empty:
            return '<section class="section-card"><h2>Recommended transactions</h2><p>No rows in this report.</p></section>'

        if "move_type" not in df.columns:
            return f"""
            <section class="section-card">
              <h2>Recommended transactions</h2>
              <div class="table-wrap">
                {self.html_table(df, allow_html=True)}
              </div>
            </section>
            """

        ordered_categories = ["Call Ups", "Send Downs", "DFA / Bench", "External Acquisitions", "Other"]
        categorized = df.copy()
        categorized["_category"] = categorized["move_type"].map(self._transaction_category)

        sections: list[str] = []
        for category in ordered_categories:
            group_df = categorized.loc[categorized["_category"] == category].drop(columns=["_category"], errors="ignore")
            if group_df.empty:
                continue
            sections.append(
                f"""
                <section class="section-card">
                  <h2>{escape(category)}</h2>
                  <p>{len(group_df)} recommendation(s) in this category.</p>
                  <div class="table-wrap">
                    {self.html_table(group_df, allow_html=True)}
                  </div>
                </section>
                """
            )
        return "".join(sections)

    @staticmethod
    def _present_columns(df: pd.DataFrame, columns: list[str]) -> list[str]:
        return [column for column in columns if column in df.columns]

    @staticmethod
    def _count_matching(df: pd.DataFrame, column: str, predicate: Callable[[pd.Series], pd.Series]) -> int:
        if df.empty or column not in df.columns:
            return 0
        series = df[column].fillna("")
        try:
            return int(predicate(series).sum())
        except Exception:
            return 0

    @staticmethod
    def _count_injured(df: pd.DataFrame) -> int:
        if df.empty or "injured_flag" not in df.columns:
            return 0
        return int(pd.to_numeric(df["injured_flag"], errors="coerce").fillna(0).astype(bool).sum())

    @staticmethod
    def _bool_series(df: pd.DataFrame, column: str) -> pd.Series:
        if df.empty:
            return pd.Series(dtype=bool)
        if column not in df.columns:
            return pd.Series(False, index=df.index, dtype=bool)
        return pd.to_numeric(df[column], errors="coerce").fillna(0).astype(bool)

    def _typed_player_pool(self, df: pd.DataFrame, player_type: str) -> pd.DataFrame:
        if df.empty:
            return df
        if player_type == "hitter" and "is_hitter" in df.columns:
            return df.loc[self._bool_series(df, "is_hitter")].copy()
        if player_type == "pitcher" and "is_pitcher" in df.columns:
            return df.loc[self._bool_series(df, "is_pitcher")].copy()
        return df.copy()

    @staticmethod
    def _summary_card_html(label: str, value: str, detail: str) -> str:
        return (
            '<article class="summary-card">'
            f'<span class="eyebrow">{escape(label)}</span>'
            f'<strong>{escape(value)}</strong>'
            f'<p style="margin:8px 0 0;color:var(--muted);font-size:0.92rem;line-height:1.45;">{escape(detail)}</p>'
            "</article>"
        )

    def _dashboard_summary_cards(self, team_needs_df: pd.DataFrame, transactions_df: pd.DataFrame, frames: dict[str, pd.DataFrame]) -> str:
        high_priority_needs = 0
        if not team_needs_df.empty and "priority" in team_needs_df.columns:
            high_priority_needs = int(team_needs_df["priority"].fillna("").astype(str).str.upper().eq("HIGH").sum())

        mlb_hitters = frames.get("mlb_hitters", pd.DataFrame()) if isinstance(frames, dict) else pd.DataFrame()
        mlb_pitchers = frames.get("mlb_pitchers", pd.DataFrame()) if isinstance(frames, dict) else pd.DataFrame()
        aaa_hitters = frames.get("aaa_hitters", pd.DataFrame()) if isinstance(frames, dict) else pd.DataFrame()
        aaa_pitchers = frames.get("aaa_pitchers", pd.DataFrame()) if isinstance(frames, dict) else pd.DataFrame()

        total_mlb_injuries = self._count_injured(mlb_hitters) + self._count_injured(mlb_pitchers)
        call_ups = self._count_matching(
            transactions_df,
            "move_type",
            lambda series: series.astype(str).str.upper().str.startswith("CALL UP"),
        )
        external_targets = self._count_matching(
            transactions_df,
            "move_type",
            lambda series: series.astype(str).str.upper().str.startswith("ACQUIRE"),
        )

        promotion_pool = 0
        if not aaa_hitters.empty and "projection_hitter_score" in aaa_hitters.columns:
            promotion_pool += int(pd.to_numeric(aaa_hitters["projection_hitter_score"], errors="coerce").fillna(0).ge(10.5).sum())
        if not aaa_pitchers.empty and "projection_pitcher_score" in aaa_pitchers.columns:
            promotion_pool += int(pd.to_numeric(aaa_pitchers["projection_pitcher_score"], errors="coerce").fillna(0).ge(9.5).sum())

        cards = [
            self._summary_card_html(
                "High-priority needs",
                str(high_priority_needs),
                "Roster areas currently flagged as the most urgent improvement targets.",
            ),
            self._summary_card_html(
                "MLB injuries",
                str(total_mlb_injuries),
                "Current injured players on the MLB roster across hitters and pitchers.",
            ),
            self._summary_card_html(
                "Call-up pressure",
                str(call_ups),
                "Promotion recommendations currently strong enough to show up on the transaction page.",
            ),
            self._summary_card_html(
                "Outside help",
                str(external_targets),
                "Need areas where the organization likely does not have enough internal coverage.",
            ),
            self._summary_card_html(
                "AAA watchlist",
                str(promotion_pool),
                "AAA players with stronger promotion-level projection scores right now.",
            ),
        ]
        return "".join(cards)

    def _prepare_dashboard_table(
        self,
        df: pd.DataFrame,
        columns: list[str],
        sort_by: str | None = None,
        ascending: bool = False,
        head: int = 5,
        rename: dict[str, str] | None = None,
    ) -> pd.DataFrame:
        if df.empty:
            return pd.DataFrame()

        working = df.copy()
        if sort_by and sort_by in working.columns:
            working = working.sort_values(sort_by, ascending=ascending, na_position="last")
        selected_columns = self._present_columns(working, columns)
        if selected_columns:
            working = working[selected_columns]
        working = working.head(head).reset_index(drop=True)
        if rename:
            working = working.rename(columns={key: value for key, value in rename.items() if key in working.columns})
        return self.format_ip_columns(self.round_score_columns(working))

    def _render_dashboard_table_section(
        self,
        title: str,
        description: str,
        df: pd.DataFrame,
        group: str | None = None,
        player_links: dict[str, dict[str, str]] | None = None,
    ) -> str:
        linked_df = df
        if group and player_links:
            linked_df = self.link_player_names(df, player_links.get(group, {}))
        return f"""
        <section class="section-card section-card-compact">
          <h2>{escape(title)}</h2>
          <p>{escape(description)}</p>
          <div class="table-wrap">
            {self.html_table(linked_df, allow_html=True, sortable=False)}
          </div>
        </section>
        """

    @staticmethod
    def _top_player_name(df: pd.DataFrame, score_col: str) -> str:
        if df.empty or score_col not in df.columns or "player_name" not in df.columns:
            return "N/A"
        ranked = df.sort_values(score_col, ascending=False, na_position="last")
        if ranked.empty:
            return "N/A"
        name = str(ranked.iloc[0].get("player_name", "")).strip()
        return name or "N/A"

    def _team_hub_summary_cards(
        self,
        prefix: str,
        frames: dict[str, pd.DataFrame],
        grouped_sections: dict[str, list[DashboardSection]],
    ) -> str:
        hitters_key = "mlb_hitters" if prefix == "mlb_" else "aaa_hitters"
        pitchers_key = "mlb_pitchers" if prefix == "mlb_" else "aaa_pitchers"
        hitter_score = "overall_hitter_score" if prefix == "mlb_" else "projection_hitter_score"
        pitcher_score = "score" if prefix == "mlb_" else "projection_pitcher_score"

        hitters = self._typed_player_pool(frames.get(hitters_key, pd.DataFrame()), "hitter")
        pitchers = self._typed_player_pool(frames.get(pitchers_key, pd.DataFrame()), "pitcher")
        healthy_hitters = int((~self._bool_series(hitters, "injured_flag")).sum()) if not hitters.empty else 0
        healthy_pitchers = int((~self._bool_series(pitchers, "injured_flag")).sum()) if not pitchers.empty else 0
        injuries = self._count_injured(hitters) + self._count_injured(pitchers)
        linked_reports = sum(len(items) for items in grouped_sections.values())

        cards = [
            self._summary_card_html("Linked reports", str(linked_reports), "Full boards and planning pages available from this hub."),
            self._summary_card_html("Healthy hitters", str(healthy_hitters), "Position-player pool currently available on this team page."),
            self._summary_card_html("Healthy pitchers", str(healthy_pitchers), "Pitching pool currently available on this team page."),
            self._summary_card_html("Injuries", str(injuries), "Current injured players on this level."),
            self._summary_card_html(
                "Top hitter",
                self._top_player_name(hitters, hitter_score),
                "Highest-ranked bat on the current team board.",
            ),
            self._summary_card_html(
                "Top pitcher",
                self._top_player_name(pitchers, pitcher_score),
                "Highest-ranked arm on the current team board.",
            ),
        ]
        return "".join(cards)

    def _team_hub_data_sections(
        self,
        prefix: str,
        frames: dict[str, pd.DataFrame],
        player_links: dict[str, dict[str, str]],
    ) -> str:
        hitters_key = "mlb_hitters" if prefix == "mlb_" else "aaa_hitters"
        pitchers_key = "mlb_pitchers" if prefix == "mlb_" else "aaa_pitchers"
        hitter_score = "overall_hitter_score" if prefix == "mlb_" else "projection_hitter_score"
        pitcher_score = "score" if prefix == "mlb_" else "projection_pitcher_score"
        hitter_title = "Current lineup core" if prefix == "mlb_" else "Promotion bats to watch"
        pitcher_title = "Current pitching core" if prefix == "mlb_" else "Promotion arms to watch"
        hitter_description = (
            "Best healthy hitters on the current MLB board."
            if prefix == "mlb_"
            else "Best healthy AAA hitters by promotion-oriented projection score."
        )
        pitcher_description = (
            "Best healthy pitchers on the current MLB board."
            if prefix == "mlb_"
            else "Best healthy AAA pitchers by promotion-oriented projection score."
        )

        hitters = self._typed_player_pool(frames.get(hitters_key, pd.DataFrame()), "hitter")
        pitchers = self._typed_player_pool(frames.get(pitchers_key, pd.DataFrame()), "pitcher")
        top_hitters = self._prepare_dashboard_table(
            hitters.loc[~self._bool_series(hitters, "injured_flag")].copy() if not hitters.empty else pd.DataFrame(),
            ["player_name", "primary_position", hitter_score, "ops_val", "war_val", "age_val"],
            sort_by=hitter_score,
            rename={
                "primary_position": "pos",
                hitter_score: "score",
                "ops_val": "ops",
                "war_val": "war",
                "age_val": "age",
            },
        )
        top_pitchers = self._prepare_dashboard_table(
            pitchers.loc[~self._bool_series(pitchers, "injured_flag")].copy() if not pitchers.empty else pd.DataFrame(),
            ["player_name", pitcher_score, "era_val", "fip_val", "ip_val", "age_val"],
            sort_by=pitcher_score,
            rename={
                pitcher_score: "score",
                "era_val": "era",
                "fip_val": "fip",
                "ip_val": "ip",
                "age_val": "age",
            },
        )

        return f"""
        <section class="dashboard-group">
          <div class="dashboard-group-heading">
            <h2>{escape('Team Snapshot')}</h2>
          </div>
          <section class="section-grid section-grid-overview">
            {self._render_dashboard_table_section(hitter_title, hitter_description, top_hitters, hitters_key, player_links)}
            {self._render_dashboard_table_section(pitcher_title, pitcher_description, top_pitchers, pitchers_key, player_links)}
          </section>
        </section>
        """

    def _team_hub_link_card(self, label: str, section: DashboardSection) -> str:
        slug = self.slugify(section.title)
        description = self._section_description(section) or self._section_snapshot_text(section)
        return f"""
        <section class="section-card section-card-compact">
          <header class="section-card-header">
            <div>
              <p class="section-kicker">{escape(label)}</p>
              <h2>{escape(section.title)}</h2>
            </div>
            <a class="section-link section-link-inline" href="{slug}.html">Open</a>
          </header>
          <p>{escape(description)}</p>
          <div class="section-meta-row">
            <span class="section-meta-pill">{len(section.df)} rows</span>
            <span class="section-meta-pill">Linked page</span>
          </div>
        </section>
        """

    def _team_hub_report_buttons(self, grouped_sections: dict[str, list[DashboardSection]]) -> str:
        ordered_labels = ("Position players", "Pitching", "Planning & decisions")
        buttons: list[str] = []
        for label in ordered_labels:
            for section in grouped_sections.get(label, []):
                slug = self.slugify(section.title)
                buttons.append(
                    f'<a class="section-meta-pill" href="{slug}.html">{escape(section.title)}</a>'
                )
        if not buttons:
            return ""
        return f'<div class="section-meta-row">{"".join(buttons)}</div>'

    def _dashboard_body(
        self,
        sections: list[DashboardSection],
        outputs: DashboardOutputs,
        frames: dict[str, pd.DataFrame],
        player_links: dict[str, dict[str, str]],
    ) -> str:
        section_lookup = {section.title: section for section in sections}
        team_needs_df = section_lookup.get("Team needs", DashboardSection("Team needs", pd.DataFrame())).df
        transactions_df = outputs.recommended_transactions if isinstance(outputs.recommended_transactions, pd.DataFrame) else pd.DataFrame()

        mlb_hitters = frames.get("mlb_hitters", pd.DataFrame()) if isinstance(frames, dict) else pd.DataFrame()
        mlb_pitchers = frames.get("mlb_pitchers", pd.DataFrame()) if isinstance(frames, dict) else pd.DataFrame()
        aaa_hitters = frames.get("aaa_hitters", pd.DataFrame()) if isinstance(frames, dict) else pd.DataFrame()
        aaa_pitchers = frames.get("aaa_pitchers", pd.DataFrame()) if isinstance(frames, dict) else pd.DataFrame()

        mlb_hitter_injured = self._bool_series(mlb_hitters, "injured_flag")
        mlb_pitcher_injured = self._bool_series(mlb_pitchers, "injured_flag")
        aaa_hitter_injured = self._bool_series(aaa_hitters, "injured_flag")
        aaa_pitcher_injured = self._bool_series(aaa_pitchers, "injured_flag")

        top_hitters = self._prepare_dashboard_table(
            mlb_hitters.loc[~mlb_hitter_injured].copy() if not mlb_hitters.empty else pd.DataFrame(),
            ["player_name", "primary_position", "overall_hitter_score", "ops_val", "war_val", "pa_val"],
            sort_by="overall_hitter_score",
            rename={
                "primary_position": "pos",
                "overall_hitter_score": "score",
                "ops_val": "ops",
                "war_val": "war",
                "pa_val": "pa",
            },
        )
        top_pitchers = self._prepare_dashboard_table(
            mlb_pitchers.loc[~mlb_pitcher_injured].copy() if not mlb_pitchers.empty else pd.DataFrame(),
            ["player_name", "score", "era_val", "fip_val", "ip_val", "stamina_now"],
            sort_by="score",
            rename={
                "era_val": "era",
                "fip_val": "fip",
                "ip_val": "ip",
                "stamina_now": "stamina",
            },
        )
        needs_table = self._prepare_dashboard_table(
            team_needs_df,
            ["priority", "area", "need", "internal_options"],
            sort_by="priority_value",
            rename={"internal_options": "internal options"},
            head=6,
        )
        injured_players = pd.concat(
            [
                mlb_hitters.loc[mlb_hitter_injured, :] if not mlb_hitters.empty else pd.DataFrame(),
                mlb_pitchers.loc[mlb_pitcher_injured, :] if not mlb_pitchers.empty else pd.DataFrame(),
            ],
            ignore_index=True,
        )
        if not injured_players.empty and "player_name" in injured_players.columns:
            injured_players["unit"] = [
                "Pitching" if bool(value) else "Hitters"
                for value in self._bool_series(injured_players, "is_pitcher")
            ]
        injuries_table = self._prepare_dashboard_table(
            injured_players,
            ["unit", "player_name", "primary_position", "injury_text", "status"],
            rename={"primary_position": "pos", "injury_text": "injury"},
            head=8,
        )
        aaa_hitter_watch = self._prepare_dashboard_table(
            aaa_hitters.loc[~aaa_hitter_injured].copy() if not aaa_hitters.empty else pd.DataFrame(),
            ["player_name", "primary_position", "projection_hitter_score", "ops_val", "age_val", "bats"],
            sort_by="projection_hitter_score",
            rename={
                "primary_position": "pos",
                "projection_hitter_score": "proj score",
                "ops_val": "ops",
                "age_val": "age",
            },
        )
        aaa_pitcher_watch = self._prepare_dashboard_table(
            aaa_pitchers.loc[~aaa_pitcher_injured].copy() if not aaa_pitchers.empty else pd.DataFrame(),
            ["player_name", "projection_pitcher_score", "era_val", "fip_val", "ip_val", "age_val", "throws"],
            sort_by="projection_pitcher_score",
            rename={
                "projection_pitcher_score": "proj score",
                "era_val": "era",
                "fip_val": "fip",
                "ip_val": "ip",
                "age_val": "age",
            },
        )

        return f"""
        <section class="dashboard-overview">
          <section class="section-card">
            <h2>Organization Status</h2>
            <p>
              This dashboard is meant to be a quick scan of club health, current pressure points, MLB performance leaders,
              and AAA options pushing for a bigger role.
            </p>
            <section class="summary-grid">
              {self._dashboard_summary_cards(team_needs_df, transactions_df, frames)}
            </section>
          </section>
          <section class="dashboard-group">
            <div class="dashboard-group-heading">
              <h2>MLB Leaders</h2>
            </div>
            <section class="section-grid section-grid-overview">
              {self._render_dashboard_table_section(
                  "Top MLB hitters",
                  "Best current healthy MLB bats by overall hitter score, with current production context.",
                  top_hitters,
                  "mlb_hitters",
                  player_links,
              )}
              {self._render_dashboard_table_section(
                  "Top MLB pitchers",
                  "Best current healthy MLB arms by current pitcher score, with run-prevention context.",
                  top_pitchers,
                  "mlb_pitchers",
                  player_links,
              )}
            </section>
          </section>
          <section class="dashboard-group">
            <div class="dashboard-group-heading">
              <h2>Pressure Points</h2>
            </div>
            <section class="section-grid section-grid-overview">
              {self._render_dashboard_table_section(
                  "Current needs",
                  "Most pressing roster areas based on MLB quality, AAA cover, age risk, and handedness balance.",
                  needs_table,
              )}
              {self._render_dashboard_table_section(
                  "Availability",
                  "Current injured MLB players and the roster areas they are affecting right now.",
                  injuries_table,
              )}
            </section>
          </section>
          <section class="dashboard-group">
            <div class="dashboard-group-heading">
              <h2>AAA Watch</h2>
            </div>
            <section class="section-grid section-grid-overview">
              {self._render_dashboard_table_section(
                  "Top AAA hitters",
                  "Best healthy AAA bats by projection score as near-term promotion candidates.",
                  aaa_hitter_watch,
                  "aaa_hitters",
                  player_links,
              )}
              {self._render_dashboard_table_section(
                  "Top AAA pitchers",
                  "Best healthy AAA arms by projection score as call-up or depth candidates.",
                  aaa_pitcher_watch,
                  "aaa_pitchers",
                  player_links,
              )}
            </section>
          </section>
        </section>
        """

    def _write_html_outputs(self, outputs: DashboardOutputs, frames: dict[str, pd.DataFrame]) -> None:
        sections = self.output_sections(outputs)
        player_links = self.write_player_detail_pages(frames) if isinstance(frames, dict) else {}
        if isinstance(frames, dict):
            frames = dict(frames)
            frames["_recommended_rotation"] = outputs.recommended_rotation.copy()
        mlb_home_slug = self.slugify(f"{self.mlb_team_name} team")
        aaa_home_slug = self.slugify(f"{self.aaa_team_name} team")
        dashboard_body = self._dashboard_body(sections, outputs, frames, player_links)
        (self.out_dir / "dashboard.html").write_text(
            self.html_shell("OOTP DiamondOps", dashboard_body, "dashboard"),
            encoding="utf-8",
        )
        self._write_season_summary_page()
        self._write_scoring_info_page(frames)

        def team_hub_body(team_name: str, prefix: str, intro: str) -> str:
            grouped_sections: dict[str, list[DashboardSection]] = {
                "Position players": [],
                "Pitching": [],
                "Planning & decisions": [],
            }
            for section in sections:
                bucket = self._team_hub_bucket(section, prefix)
                if bucket is not None:
                    grouped_sections.setdefault(bucket, []).append(section)

            report_buttons = self._team_hub_report_buttons(grouped_sections) or '<p class="empty-state">No team pages available.</p>'

            return f"""
                <section class="dashboard-overview">
                  <section class="section-card">
                    <h2>{escape(team_name)} Team Hub</h2>
                    <p>{escape(intro)}</p>
                    <p>{escape(self._team_hub_intro(team_name, prefix, grouped_sections))}</p>
                    {report_buttons}
                    <section class="summary-grid">
                      {self._team_hub_summary_cards(prefix, frames, grouped_sections)}
                    </section>
                  </section>
                  {self._team_hub_data_sections(prefix, frames, player_links)}
                </section>
            """

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
            if section.title == "Team needs":
                active_nav = "team_needs"
            elif section.title == "Recommended transactions":
                active_nav = "recommended_transactions"
            elif section.group and section.group.startswith("mlb_"):
                active_nav = mlb_home_slug
            elif section.group and section.group.startswith("aaa_"):
                active_nav = aaa_home_slug
            else:
                active_nav = "dashboard"
            description = self._section_description(section)
            extra_body = ""
            if section.title == "Recommended rotation":
                extra_body = self._rotation_candidate_table(frames, player_links)
            if section.title == "Recommended transactions":
                body = f"""
                <section class="section-card">
                  <h2>{escape(section.title)}</h2>
                  <p>{escape(description) if description else f"{len(section.df)} rows in this report."}</p>
                </section>
                {self._recommended_transactions_tables(linked_df)}
                """
            else:
                body = f"""
                <section class="section-card">
                  <h2>{escape(section.title)}</h2>
                  <p>{escape(description) if description else f"{len(section.df)} rows in this report."}</p>
                  <div class="table-wrap">
                                    {self.html_table(linked_df, allow_html=True, highlight_starters=section.highlight_starters, column_modes=section.column_modes, column_labels=section.column_labels, default_mode=section.default_mode)}
                  </div>
                </section>
                {extra_body}
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
