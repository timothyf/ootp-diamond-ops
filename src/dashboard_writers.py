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

    def _write_html_outputs(self, outputs: DashboardOutputs, frames: dict[str, pd.DataFrame]) -> None:
        sections = self.output_sections(outputs)
        player_links = self.write_player_detail_pages(frames) if isinstance(frames, dict) else {}
        if isinstance(frames, dict):
            frames = dict(frames)
            frames["_recommended_rotation"] = outputs.recommended_rotation.copy()
        mlb_home_slug = self.slugify(f"{self.mlb_team_name} team")
        aaa_home_slug = self.slugify(f"{self.aaa_team_name} team")

        overview_sections_by_group: dict[str, list[str]] = {}
        for section in sections:
            group_label = self._dashboard_bucket(section)
            if group_label is None:
                continue
            slug = self.slugify(section.title)
            area_label = "Organization"
            if section.group and section.group.startswith("mlb_"):
                area_label = "MLB"
            elif section.group and section.group.startswith("aaa_"):
                area_label = "AAA"

            snapshot = self._section_snapshot_text(section)
            description = self._section_description(section) or snapshot
            overview_sections_by_group.setdefault(group_label, []).append(
                f"""
                <article class="summary-card">
                  <span class="eyebrow">{escape(group_label)}</span>
                  <strong style="font-size:1.2rem;line-height:1.3;">{escape(section.title)}</strong>
                  <p style="margin:10px 0 8px;color:var(--ink);font-size:0.96rem;">{escape(snapshot)}</p>
                  <p style="margin:0 0 12px;color:var(--muted);font-size:0.92rem;line-height:1.55;">{escape(description)}</p>
                  <div class="section-meta-row">
                    <span class="section-meta-pill">{escape(area_label)}</span>
                    <span class="section-meta-pill">{len(section.df)} rows</span>
                  </div>
                  <a class="section-link" href="{slug}.html">Open page</a>
                </article>
                """
            )

        overview_groups = []
        for label in sorted(overview_sections_by_group.keys(), key=self._dashboard_bucket_order):
            cards = overview_sections_by_group.get(label, [])
            if not cards:
                continue
            overview_groups.append(
                f"""
                <section class="dashboard-group">
                  <div class="dashboard-group-heading">
                    <h2>{escape(label)}</h2>
                  </div>
                  <section class="summary-grid">
                    {''.join(cards)}
                  </section>
                </section>
                """
            )

        dashboard_body = f"""
        <section class="dashboard-overview">
          <section class="section-card">
            <h2>Front Office Briefing</h2>
            <p>
              This landing page is now focused on the most actionable decisions first. Start with roster needs,
              transactions, lineup, and rotation recommendations here, then move into the MLB and AAA hubs for the
              supporting player boards and depth context.
            </p>
          </section>
          {''.join(overview_groups)}
        </section>
        """
        (self.out_dir / "dashboard.html").write_text(
            self.html_shell("OOTP DiamondOps", dashboard_body, "dashboard"),
            encoding="utf-8",
        )
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

            group_blocks: list[str] = []
            for label in ("Position players", "Pitching", "Planning & decisions"):
                bucket_sections = grouped_sections.get(label, [])
                if not bucket_sections:
                    continue
                cards: list[str] = []
                for section in bucket_sections:
                    slug = self.slugify(section.title)
                    preview, preview_modes, preview_labels, preview_default_mode = self._build_overview_preview(section)
                    linked_preview = (
                        self.link_player_names(preview, player_links.get(section.group, {})) if section.group else preview
                    )
                    description = self._section_description(section) or self._section_snapshot_text(section)
                    cards.append(
                        f"""
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
                group_blocks.append(
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

            if not group_blocks:
                group_blocks.append('<p class="empty-state">No team pages available.</p>')

            return f"""
                <section class="dashboard-overview">
                  <section class="section-card">
                    <h2>{escape(team_name)} Team Hub</h2>
                    <p>{escape(intro)}</p>
                    <p>{escape(self._team_hub_intro(team_name, prefix, grouped_sections))}</p>
                    <div class="section-meta-row">
                      <span class="section-meta-pill">{sum(len(items) for items in grouped_sections.values())} linked reports</span>
                      <span class="section-meta-pill">{escape('MLB focus' if prefix == 'mlb_' else 'AAA focus')}</span>
                    </div>
                  </section>
                  {''.join(group_blocks)}
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
            if section.group and section.group.startswith("mlb_"):
                active_nav = mlb_home_slug
            elif section.group and section.group.startswith("aaa_"):
                active_nav = aaa_home_slug
            elif section.title == "Recommended transactions":
                active_nav = "recommended_transactions"
            else:
                active_nav = "dashboard"
            description = self._section_description(section)
            extra_body = ""
            if section.title == "Recommended rotation":
                extra_body = self._rotation_candidate_table(frames, player_links)
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
