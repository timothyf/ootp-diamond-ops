from __future__ import annotations

from html import escape
from pathlib import Path
from typing import Callable

import pandas as pd


class PlayerDetailPageWriter:
    def __init__(
        self,
        out_dir: Path,
        html_table: Callable[..., str],
        html_shell: Callable[[str, str], str],
        player_detail_filename: Callable[[str, str], str],
        normalize_key: Callable[[pd.Series], pd.Series],
    ) -> None:
        self.out_dir = out_dir
        self.html_table = html_table
        self.html_shell = html_shell
        self.player_detail_filename = player_detail_filename
        self.normalize_key = normalize_key

    @staticmethod
    def score_narrative(row: pd.Series, group: str) -> str:  # noqa: C901
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

        else:
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
    def component_rows(
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

    def write_player_detail_pages(self, group_frames: dict[str, pd.DataFrame]) -> dict[str, dict[str, str]]:
        hitter_fields = [
            ("Overall Score", "overall_hitter_score", "computed"),
            ("Projection Score", "projection_hitter_score", "computed"),
            ("Baseline Offset", "score_baseline_offset", "added to both scores"),
            ("Offense Score", "offense_score", "feeds regressed offense"),
            ("Regressed Offense", "offense_score_regressed", "0.52 overall / 0.26 projection"),
            ("Current Ratings (Centered)", "ratings_hitter_now_component", "(rating-50)/5; 0.22 overall / 0.27 projection"),
            ("Future Ratings (Centered)", "ratings_hitter_future_component", "(rating-50)/5; 0.34 projection"),
            ("Discipline Component", "discipline_component", "0.80 overall / 0.90 projection"),
            ("Platoon Skill Component", "platoon_skill_component", "0.60 overall / 0.70 projection"),
            ("Defensive Component", "defensive_component", "0.50 overall / 0.35 projection"),
            ("Contact Quality Component", "contact_quality_component", "0.08 overall / 0.04 projection"),
            ("Running Component", "running_component", "0.25 overall / 0.20 projection"),
            ("Scarcity Bonus", "scarcity_bonus", "0.40 overall"),
            ("Age Bonus", "age_bonus", "0.50 projection"),
            ("Select Score vs RHP", "select_score_rhp", "selection logic only"),
            ("Select Score vs LHP", "select_score_lhp", "selection logic only"),
        ]
        pitcher_fields = [
            ("Current Score", "score", "computed"),
            ("Projection Score", "projection_pitcher_score", "computed"),
            ("Baseline Offset", "score_baseline_offset", "added to both scores"),
            ("Results Score", "results_pitcher_score", "feeds regressed results"),
            ("Regressed Results", "results_pitcher_score_regressed", "0.58 score / 0.26 projection"),
            ("Current Ratings (Centered)", "ratings_pitcher_now_component", "(rating-50)/5; 0.30 score / 0.24 projection"),
            ("Future Ratings (Centered)", "ratings_pitcher_future_component", "(rating-50)/5; 0.34 projection"),
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
            keyed["player_lookup"] = self.normalize_key(keyed["player_name"])

            for _, row in keyed.iterrows():
                player_name = str(row["player_name"])
                lookup = str(row["player_lookup"])
                filename = self.player_detail_filename(group, player_name)
                components = self.component_rows(row, fields, include_weight=True)

                summary_fields = [
                    ("Position", "primary_position"),
                    ("Age", "age_val"),
                    ("Bats", "bats"),
                    ("Throws", "throws"),
                    ("Injury", "injury_text"),
                ]
                summary = self.component_rows(row, summary_fields)

                narrative_html = self.score_narrative(row, group)
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
                    self.html_shell(f"{player_name} component breakdown", body),
                    encoding="utf-8",
                )
                link_maps[group][lookup] = filename
        return link_maps
