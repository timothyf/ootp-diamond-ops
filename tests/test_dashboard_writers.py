from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock

import pandas as pd

from src.dashboard_types import DashboardOutputs
from src.dashboard_types import DashboardSection
from src.dashboard_utils import slugify
from src.dashboard_writers import DashboardOutputWriter


def _sample_outputs() -> DashboardOutputs:
    hitters = pd.DataFrame(
        [{"player_name": "Alice", "score": 1.234, "ip": 0.0}]
    )
    pitchers = pd.DataFrame(
        [{"player_name": "Bob", "score": 2.345, "ip": 6.2}]
    )
    lineup = pd.DataFrame([{"player_name": "Alice", "score": 4.567}])
    rotation = pd.DataFrame([{"player_name": "Bob", "score": 3.456, "ip": 5.1}])
    transactions = pd.DataFrame(
        [
            {"move_type": "CALL UP HITTER", "player_name": "Alice", "score": 0.5, "possible_replace": "Bob", "score_gap": 1.2},
            {"move_type": "SEND DOWN PITCHER", "player_name": "Charlie", "score": 0.2, "possible_replace": "Delta", "score_gap": 0.8},
            {"move_type": "ACQUIRE HITTER", "player_name": "Corner bat / DH", "score": 0.1, "possible_replace": "Echo", "score_gap": 0.5},
        ]
    )
    return DashboardOutputs(
        mlb_hitters_dashboard=hitters.copy(),
        mlb_pitchers_dashboard=pitchers.copy(),
        aaa_hitters_dashboard=hitters.copy(),
        aaa_pitchers_dashboard=pitchers.copy(),
        recommended_lineup_vs_rhp=lineup.copy(),
        recommended_lineup_vs_lhp=lineup.copy(),
        recommended_rotation=rotation.copy(),
        recommended_bullpen_roles=rotation.copy(),
        platoon_diagnostics=lineup.copy(),
        recommended_transactions=transactions.copy(),
    )


class DashboardWriterTests(unittest.TestCase):
    def _build_writer(self, out_dir: Path, round_mock: Mock, ip_mock: Mock) -> DashboardOutputWriter:
        def html_table(
            df: pd.DataFrame,
            allow_html: bool = False,
            sortable: bool = True,
            highlight_starters: bool = False,
            column_modes: dict[str, list[str]] | None = None,
            column_labels: dict[str, str] | None = None,
            default_mode: str | None = None,
        ) -> str:
            names = ",".join(df["player_name"].astype(str).tolist()) if "player_name" in df.columns else ""
            toggle = f" mode={default_mode}" if column_modes else ""
            return f"<table data-highlight='{highlight_starters}'{toggle}>{names}</table>"

        def html_shell(title: str, body: str, active_page: str | None = None) -> str:
            return f"<html><title>{title}</title><body data-page='{active_page}'>{body}</body></html>"

        def output_sections(outputs: DashboardOutputs):
            return [
                DashboardSection(
                    title="Detroit hitters",
                    df=outputs.mlb_hitters_dashboard,
                    group="mlb_hitters",
                    column_modes={"current": ["score"]},
                    column_labels={"score": "score"},
                    default_mode="current",
                ),
                DashboardSection(title="Toledo hitters", df=outputs.aaa_hitters_dashboard, group="aaa_hitters"),
                DashboardSection(
                    title="Detroit active depth chart",
                    df=pd.DataFrame([{"position": "C", "rank": 1, "player_name": "Alice"}]),
                    group="mlb_hitters",
                    highlight_starters=True,
                ),
                DashboardSection(
                    title="Team needs",
                    df=pd.DataFrame(
                        [
                            {
                                "priority": "High",
                                "area": "Rotation",
                                "need": "Add starter depth",
                                "internal_options": "Charlie, Delta",
                            }
                        ]
                    ),
                    group="mlb_team",
                ),
                DashboardSection(title="Recommended lineup vs RHP", df=outputs.recommended_lineup_vs_rhp, group="mlb_hitters"),
                DashboardSection(title="Recommended lineup vs LHP", df=outputs.recommended_lineup_vs_lhp, group="mlb_hitters"),
                DashboardSection(title="Recommended rotation", df=outputs.recommended_rotation, group="mlb_pitchers"),
                DashboardSection(title="Bullpen roles", df=outputs.recommended_bullpen_roles, group="mlb_pitchers"),
                DashboardSection(title="Recommended transactions", df=outputs.recommended_transactions, group=None),
            ]

        def link_player_names(df: pd.DataFrame, links: dict[str, str]) -> pd.DataFrame:
            if "player_name" not in df.columns:
                return df
            linked = df.copy()
            linked["player_name"] = [links.get(str(name).lower(), str(name)) for name in linked["player_name"]]
            return linked

        return DashboardOutputWriter(
            out_dir=out_dir,
            mlb_team_name="Detroit",
            aaa_team_name="Toledo",
            slugify=slugify,
            md_table=lambda df: f"rows={len(df)}",
            html_table=html_table,
            html_shell=html_shell,
            output_sections=output_sections,
            write_player_detail_pages=lambda frames: {
                "mlb_hitters": {"alice": "alice.html"},
                "aaa_hitters": {"alice": "alice.html"},
            },
            link_player_names=link_player_names,
            round_score_columns=round_mock,
            format_ip_columns=ip_mock,
        )

    def test_write_outputs_writes_files_and_applies_formatters(self) -> None:
        outputs = _sample_outputs()
        with tempfile.TemporaryDirectory() as temp_dir:
            out_dir = Path(temp_dir)
            round_mock = Mock(side_effect=lambda df: df.copy())
            ip_mock = Mock(side_effect=lambda df: df.copy())
            writer = self._build_writer(out_dir, round_mock, ip_mock)

            frames = {
                "mlb_hitters": pd.DataFrame([{"player_name": "Alice"}]),
                "mlb_pitchers": pd.DataFrame(
                    [
                        {
                            "player_name": "Bob",
                            "is_pitcher": True,
                            "injured_flag": False,
                            "ip_val": 50.0,
                            "gs_val": 10,
                            "stamina_now": 60,
                            "era_val": 3.2,
                            "fip_val": 3.4,
                            "rotation_score": 12.5,
                            "true_starter_flag": True,
                            "swingman_flag": False,
                        },
                        {
                            "player_name": "Charlie",
                            "is_pitcher": True,
                            "injured_flag": False,
                            "ip_val": 28.0,
                            "gs_val": 4,
                            "stamina_now": 58,
                            "era_val": 3.8,
                            "fip_val": 3.9,
                            "rotation_score": 10.4,
                            "true_starter_flag": True,
                            "swingman_flag": False,
                        },
                        {
                            "player_name": "Delta",
                            "is_pitcher": True,
                            "injured_flag": False,
                            "ip_val": 24.0,
                            "gs_val": 2,
                            "stamina_now": 55,
                            "era_val": 4.1,
                            "fip_val": 4.0,
                            "rotation_score": 9.8,
                            "true_starter_flag": False,
                            "swingman_flag": True,
                        },
                    ]
                ),
            }

            writer.write_outputs(outputs, frames=frames)

            self.assertEqual(round_mock.call_count, 11)
            self.assertEqual(ip_mock.call_count, 11)
            self.assertTrue((out_dir / "detroit_hitters_dashboard.csv").exists())
            self.assertTrue((out_dir / "ootp_gm_dashboard.md").exists())
            markdown = (out_dir / "ootp_gm_dashboard.md").read_text(encoding="utf-8")
            self.assertIn("## Recommended lineup vs RHP", markdown)
            self.assertIn("rows=1", markdown)

    def test_write_outputs_generates_dashboard_team_and_section_pages(self) -> None:
        outputs = _sample_outputs()
        with tempfile.TemporaryDirectory() as temp_dir:
            out_dir = Path(temp_dir)
            writer = self._build_writer(
                out_dir,
                Mock(side_effect=lambda df: df.copy()),
                Mock(side_effect=lambda df: df.copy()),
            )

            frames = {
                "mlb_hitters": pd.DataFrame([{"player_name": "Alice"}]),
                "mlb_pitchers": pd.DataFrame(
                    [
                        {
                            "player_name": "Bob",
                            "is_pitcher": True,
                            "injured_flag": False,
                            "ip_val": 50.0,
                            "gs_val": 10,
                            "stamina_now": 60,
                            "era_val": 3.2,
                            "fip_val": 3.4,
                            "rotation_score": 12.5,
                            "true_starter_flag": True,
                            "swingman_flag": False,
                        },
                        {
                            "player_name": "Charlie",
                            "is_pitcher": True,
                            "injured_flag": False,
                            "ip_val": 28.0,
                            "gs_val": 4,
                            "stamina_now": 58,
                            "era_val": 3.8,
                            "fip_val": 3.9,
                            "rotation_score": 10.4,
                            "true_starter_flag": True,
                            "swingman_flag": False,
                        },
                        {
                            "player_name": "Delta",
                            "is_pitcher": True,
                            "injured_flag": False,
                            "ip_val": 24.0,
                            "gs_val": 2,
                            "stamina_now": 55,
                            "era_val": 4.1,
                            "fip_val": 4.0,
                            "rotation_score": 9.8,
                            "true_starter_flag": False,
                            "swingman_flag": True,
                        },
                    ]
                ),
            }

            writer.write_outputs(outputs, frames=frames)

            dashboard_html = (out_dir / "dashboard.html").read_text(encoding="utf-8")
            team_html = (out_dir / "detroit_team.html").read_text(encoding="utf-8")
            depth_chart_html = (out_dir / "detroit_active_depth_chart.html").read_text(encoding="utf-8")
            needs_html = (out_dir / "team_needs.html").read_text(encoding="utf-8")
            lineup_html = (out_dir / "recommended_lineup_vs_rhp.html").read_text(encoding="utf-8")
            rotation_html = (out_dir / "recommended_rotation.html").read_text(encoding="utf-8")
            bullpen_html = (out_dir / "bullpen_roles.html").read_text(encoding="utf-8")
            transactions_html = (out_dir / "recommended_transactions.html").read_text(encoding="utf-8")
            scoring_html = (out_dir / "scoring_info.html").read_text(encoding="utf-8")

            self.assertIn("Detroit hitters", dashboard_html)
            self.assertIn("Front Office Briefing", dashboard_html)
            self.assertIn("Decisions now", dashboard_html)
            self.assertIn("MLB snapshot", dashboard_html)
            self.assertNotIn("mode=current", dashboard_html)
            self.assertIn("Detroit Team", team_html)
            self.assertIn("Position players", team_html)
            self.assertIn("Pitching", team_html)
            self.assertIn("Planning &amp; decisions", team_html)
            self.assertIn("data-highlight='True'", depth_chart_html)
            self.assertIn("data-page='team_needs'", needs_html)
            self.assertIn("highlights the club", needs_html)
            self.assertIn("locks in the best healthy regulars", lineup_html)
            self.assertIn("gives extra credit to starters", rotation_html)
            self.assertIn("Spot Starter / Replacement Candidates", rotation_html)
            self.assertIn("Charlie", rotation_html)
            self.assertIn("Delta", rotation_html)
            self.assertIn("add relief-specific credit for saves, holds", bullpen_html)
            self.assertIn("Call Ups", transactions_html)
            self.assertIn("Send Downs", transactions_html)
            self.assertIn("External Acquisitions", transactions_html)
            self.assertIn("Score Breakdown Guide", scoring_html)
            self.assertIn("Formula Weight Shares", scoring_html)
            self.assertIn("Empirical Normalized Shares", scoring_html)
            self.assertIn("Hitters analyzed", scoring_html)


if __name__ == "__main__":
    unittest.main()
