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
    transactions = pd.DataFrame([{"player_name": "Alice", "score": 0.5}])
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

            writer.write_outputs(outputs, frames={"mlb_hitters": pd.DataFrame([{"player_name": "Alice"}])})

            self.assertEqual(round_mock.call_count, 10)
            self.assertEqual(ip_mock.call_count, 10)
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

            writer.write_outputs(outputs, frames={"mlb_hitters": pd.DataFrame([{"player_name": "Alice"}])})

            dashboard_html = (out_dir / "dashboard.html").read_text(encoding="utf-8")
            team_html = (out_dir / "detroit_team.html").read_text(encoding="utf-8")
            depth_chart_html = (out_dir / "detroit_active_depth_chart.html").read_text(encoding="utf-8")
            scoring_html = (out_dir / "scoring_info.html").read_text(encoding="utf-8")

            self.assertIn("Detroit hitters", dashboard_html)
            self.assertIn("section-card-compact", dashboard_html)
            self.assertNotIn("mode=current", dashboard_html)
            self.assertIn("Detroit Team", team_html)
            self.assertIn("data-highlight='True'", depth_chart_html)
            self.assertIn("Score Breakdown Guide", scoring_html)
            self.assertIn("Formula Weight Shares", scoring_html)
            self.assertIn("Empirical Normalized Shares", scoring_html)
            self.assertIn("Hitters analyzed", scoring_html)


if __name__ == "__main__":
    unittest.main()
