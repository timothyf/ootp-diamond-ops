from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from src.dashboard_types import CompletedSeasonSummary, CompletedSeasonTeamSummary


class CsvRepository:
    def __init__(self, data_dir: Path) -> None:
        self.data_dir = data_dir

    def load(self, name: str) -> pd.DataFrame:
        return pd.read_csv(self.data_dir / name, low_memory=False)

    def get_export_date(self) -> str | None:
        # CSV exports in this project do not carry an in-file OOTP world date.
        return None

    def get_team_header_summaries(self) -> dict[str, dict[str, object] | None]:
        return {"mlb": None, "aaa": None}

    def get_completed_season_summary(self) -> CompletedSeasonSummary | None:
        return None


class MySqlRepository:
    """Load dashboard input frames from a MySQL database.

    This class provides a minimal query layer that returns the same logical
    datasets currently expected from CSV files in the dashboard flow.
    """

    def __init__(
            self,
            connection_url: str,
            mlb_team_name: str | None = None,
            aaa_team_name: str | None = None,
    ) -> None:
            self.connection_url = connection_url

            try:
                    from sqlalchemy import create_engine
            except ImportError as exc:
                    raise ImportError(
                            "MySqlRepository requires SQLAlchemy. Install with: pip install sqlalchemy pymysql"
                    ) from exc

            self._engine = create_engine(connection_url)

            detected_mlb, detected_aaa = self._infer_default_team_names()
            self.mlb_team_name = mlb_team_name or detected_mlb
            self.aaa_team_name = aaa_team_name or detected_aaa

            self.mlb_file_prefix = self._team_file_prefix(self.mlb_team_name, prefer="last")
            self.aaa_file_prefix = self._team_file_prefix(self.aaa_team_name, prefer="first")
            self._mlb_aliases = self._team_prefix_aliases(self.mlb_team_name, self.mlb_file_prefix)
            self._aaa_aliases = self._team_prefix_aliases(self.aaa_team_name, self.aaa_file_prefix)

    def smoke_check(self) -> None:
        """Verify DB connectivity and that all required tables are present.

        Raises RuntimeError with a descriptive message if any check fails.
        """
        required_tables = [
            "players",
            "teams",
            "players_batting",
            "players_pitching",
            "players_fielding",
            "players_game_batting",
            "players_game_pitching_stats",
            "players_career_batting_stats",
            "players_career_pitching_stats",
            "players_roster_status",
            "team_roster",
        ]
        from sqlalchemy import text

        try:
            with self._engine.connect() as conn:
                rows = conn.execute(text("SHOW TABLES")).fetchall()
        except Exception as exc:
            raise RuntimeError(f"DB connection failed: {exc}") from exc

        existing = {r[0].lower() for r in rows}
        missing = [t for t in required_tables if t.lower() not in existing]
        if missing:
            raise RuntimeError(
                f"DB smoke-check failed — missing tables: {', '.join(missing)}"
            )

    def _read_sql(self, sql: str, params: dict[str, Any]) -> pd.DataFrame:
            from sqlalchemy import text
            return pd.read_sql_query(text(sql), self._engine, params=params)

    @staticmethod
    def _clean_team_name(value: str | None, fallback: str) -> str:
            cleaned = (value or "").strip()
            return cleaned if cleaned else fallback

    @staticmethod
    def _team_file_prefix(team_name: str, prefer: str = "first") -> str:
            parts = [p for p in str(team_name).lower().replace("-", " ").split() if p]
            if not parts:
                return "team"
            return parts[-1] if prefer == "last" else parts[0]

    @staticmethod
    def _team_prefix_aliases(team_name: str, preferred_prefix: str) -> set[str]:
            parts = [p for p in str(team_name).lower().replace("-", " ").split() if p]
            aliases: set[str] = set(parts)
            if parts:
                aliases.add("_".join(parts))
                aliases.add(parts[0])
                aliases.add(parts[-1])
            aliases.add(preferred_prefix)
            return {a for a in aliases if a}

    def _infer_default_team_names(self) -> tuple[str, str]:
            from sqlalchemy import text

            mlb_name = "MLB Team"
            aaa_name = "AAA Team"

            try:
                with self._engine.connect() as conn:
                    mlb_row = conn.execute(
                        text(
                            """
                            SELECT team_id, TRIM(CONCAT(COALESCE(name, ''), ' ', COALESCE(nickname, ''))) AS full_name
                            FROM teams
                            WHERE human_team = 1
                            ORDER BY team_id
                            LIMIT 1
                            """
                        )
                    ).fetchone()

                    if mlb_row is None:
                        mlb_row = conn.execute(
                            text(
                                """
                                SELECT team_id, TRIM(CONCAT(COALESCE(name, ''), ' ', COALESCE(nickname, ''))) AS full_name
                                FROM teams
                                WHERE level = 1
                                ORDER BY team_id
                                LIMIT 1
                                """
                            )
                        ).fetchone()

                    if mlb_row is not None:
                        mlb_team_id = int(mlb_row._mapping["team_id"])
                        mlb_name = self._clean_team_name(mlb_row._mapping["full_name"], mlb_name)

                        aaa_row = conn.execute(
                            text(
                                """
                                SELECT TRIM(CONCAT(COALESCE(name, ''), ' ', COALESCE(nickname, ''))) AS full_name
                                FROM teams
                                WHERE parent_team_id = :parent_team_id
                                ORDER BY CASE WHEN level = 2 THEN 0 ELSE 1 END, level, team_id
                                LIMIT 1
                                """
                            ),
                            {"parent_team_id": mlb_team_id},
                        ).fetchone()

                        if aaa_row is None:
                            aaa_row = conn.execute(
                                text(
                                    """
                                    SELECT TRIM(CONCAT(COALESCE(name, ''), ' ', COALESCE(nickname, ''))) AS full_name
                                    FROM teams
                                    WHERE level = 2
                                    ORDER BY team_id
                                    LIMIT 1
                                    """
                                )
                            ).fetchone()

                        if aaa_row is not None:
                            aaa_name = self._clean_team_name(aaa_row._mapping["full_name"], aaa_name)
            except Exception:
                pass

            return mlb_name, aaa_name

    def _team_name_from_dataset_prefix(self, prefix: str) -> str | None:
            token = prefix.strip().lower()
            if token in self._mlb_aliases:
                return self.mlb_team_name
            if token in self._aaa_aliases:
                return self.aaa_team_name
            return None

    def load(self, name: str) -> pd.DataFrame:
            dataset = Path(name).name.lower()
            if dataset == "player_ratings.csv":
                return self._build_player_ratings()

            suffix_to_builder = {
                "_roster.csv": self._build_roster,
                "_batting.csv": self._build_batting,
                "_pitching.csv": self._build_pitching,
            }
            for suffix, builder in suffix_to_builder.items():
                if dataset.endswith(suffix):
                    prefix = dataset[: -len(suffix)]
                    team_name = self._team_name_from_dataset_prefix(prefix)
                    if team_name is None:
                        raise ValueError(
                            f"Unsupported team dataset '{name}'. Recognized prefixes: "
                            f"{sorted(self._mlb_aliases | self._aaa_aliases)}"
                        )
                    return builder(team_name)

            raise ValueError(f"Unsupported dataset '{name}' for MySqlRepository")

    def get_export_date(self) -> str | None:
        """Return the in-game OOTP date used by the simulation, if available."""
        from sqlalchemy import text

        sql = """
            SELECT MAX(`current_date`) AS ootp_current_date
        FROM leagues
        """
        try:
            with self._engine.connect() as conn:
                row = conn.execute(text(sql)).fetchone()
        except Exception:
            return None

        if row is None:
            return None

        value = row._mapping.get("ootp_current_date") if hasattr(row, "_mapping") else row[0]
        if value is None:
            value = row[0]
        if value is None:
            return None
        if hasattr(value, "strftime"):
            return value.strftime("%Y-%m-%d")
        return str(value)

    def get_team_header_summaries(self) -> dict[str, dict[str, object] | None]:
        return {
            "mlb": self._get_team_header_summary(self.mlb_team_name),
            "aaa": self._get_team_header_summary(self.aaa_team_name),
        }

    @staticmethod
    def _parse_export_year(export_date: str | None) -> int | None:
        text = str(export_date or "").strip()
        if not text:
            return None
        try:
            return int(text[:4])
        except ValueError:
            return None

    def get_completed_season_summary(self) -> CompletedSeasonSummary | None:
        season_year = self._get_latest_completed_season_year()
        if season_year is None:
            return None

        mlb_summary = self._get_completed_season_team_summary(self.mlb_team_name, season_year)
        aaa_summary = self._get_completed_season_team_summary(self.aaa_team_name, season_year)
        if mlb_summary is None or aaa_summary is None:
            return None

        return CompletedSeasonSummary(
            season_year=season_year,
            mlb=mlb_summary,
            aaa=aaa_summary,
        )

    def _get_latest_completed_season_year(self) -> int | None:
        from sqlalchemy import text

        export_year = self._parse_export_year(self.get_export_date())
        if export_year is None:
            return None

        sql = """
            WITH latest_history AS (
                SELECT
                    TRIM(CONCAT(COALESCE(t.name, ''), ' ', COALESCE(t.nickname, ''))) AS full_name,
                    MAX(th.year) AS latest_year
                FROM teams t
                JOIN team_history th ON th.team_id = t.team_id
                WHERE TRIM(CONCAT(COALESCE(t.name, ''), ' ', COALESCE(t.nickname, ''))) IN (:mlb_team_name, :aaa_team_name)
                GROUP BY full_name
            )
            SELECT MIN(latest_year) AS common_year, COUNT(*) AS team_count
            FROM latest_history
        """
        try:
            with self._engine.connect() as conn:
                row = conn.execute(
                    text(sql),
                    {
                        "mlb_team_name": self.mlb_team_name,
                        "aaa_team_name": self.aaa_team_name,
                    },
                ).fetchone()
        except Exception:
            return None

        if row is None:
            return None

        data = row._mapping if hasattr(row, "_mapping") else row
        team_count = data.get("team_count", 0)
        common_year = data.get("common_year")
        if team_count != 2 or common_year is None:
            return None

        season_year = int(common_year)
        current_games = self._get_current_team_games_played()
        if not self._should_show_completed_season_summary(export_year, season_year, current_games):
            return None
        return season_year

    @staticmethod
    def _should_show_completed_season_summary(
        export_year: int | None,
        completed_season_year: int | None,
        current_team_games: dict[str, int | None] | None,
    ) -> bool:
        if export_year is None or completed_season_year is None:
            return False
        if completed_season_year == export_year:
            return True
        if completed_season_year != export_year - 1:
            return False

        current_team_games = current_team_games or {}
        for value in current_team_games.values():
            if value is None:
                continue
            if int(value) > 0:
                return False
        return True

    def _get_current_team_games_played(self) -> dict[str, int | None]:
        from sqlalchemy import text

        sql = """
            SELECT
                TRIM(CONCAT(COALESCE(t.name, ''), ' ', COALESCE(t.nickname, ''))) AS full_name,
                tr.g AS games_played
            FROM teams t
            LEFT JOIN team_record tr ON tr.team_id = t.team_id
            WHERE TRIM(CONCAT(COALESCE(t.name, ''), ' ', COALESCE(t.nickname, ''))) IN (:mlb_team_name, :aaa_team_name)
        """
        try:
            with self._engine.connect() as conn:
                rows = conn.execute(
                    text(sql),
                    {
                        "mlb_team_name": self.mlb_team_name,
                        "aaa_team_name": self.aaa_team_name,
                    },
                ).fetchall()
        except Exception:
            return {}

        games_by_team: dict[str, int | None] = {}
        for row in rows:
            data = row._mapping if hasattr(row, "_mapping") else row
            full_name = str(data.get("full_name") or "").strip()
            games_played = data.get("games_played")
            games_by_team[full_name] = int(games_played) if games_played is not None else None
        return games_by_team

    def _get_completed_season_team_summary(
        self,
        team_name: str,
        season_year: int,
    ) -> CompletedSeasonTeamSummary | None:
        from sqlalchemy import text

        sql = """
            SELECT
                TRIM(CONCAT(COALESCE(t.name, ''), ' ', COALESCE(t.nickname, ''))) AS full_name,
                thr.w AS wins,
                thr.l AS losses,
                COALESCE(th.position_in_division, thr.pos) AS division_position,
                thr.gb AS games_back,
                COALESCE(th.made_playoffs, 0) AS made_playoffs,
                COALESCE(th.won_playoffs, 0) AS won_playoffs,
                TRIM(CONCAT(COALESCE(best_hitter.first_name, ''), ' ', COALESCE(best_hitter.last_name, ''))) AS best_hitter_name,
                TRIM(CONCAT(COALESCE(best_pitcher.first_name, ''), ' ', COALESCE(best_pitcher.last_name, ''))) AS best_pitcher_name,
                TRIM(CONCAT(COALESCE(best_rookie.first_name, ''), ' ', COALESCE(best_rookie.last_name, ''))) AS best_rookie_name
            FROM teams t
            JOIN team_history th
                ON th.team_id = t.team_id
                AND th.year = :season_year
            LEFT JOIN team_history_record thr
                ON thr.team_id = t.team_id
                AND thr.year = th.year
            LEFT JOIN players best_hitter ON best_hitter.player_id = th.best_hitter_id
            LEFT JOIN players best_pitcher ON best_pitcher.player_id = th.best_pitcher_id
            LEFT JOIN players best_rookie ON best_rookie.player_id = th.best_rookie_id
            WHERE TRIM(CONCAT(COALESCE(t.name, ''), ' ', COALESCE(t.nickname, ''))) = :team_name
            ORDER BY t.team_id
            LIMIT 1
        """
        try:
            with self._engine.connect() as conn:
                row = conn.execute(
                    text(sql),
                    {"team_name": team_name, "season_year": season_year},
                ).fetchone()
        except Exception:
            return None

        if row is None:
            return None

        data = row._mapping if hasattr(row, "_mapping") else row

        def _clean_name(value: object) -> str | None:
            text = str(value or "").strip()
            return text if text else None

        return CompletedSeasonTeamSummary(
            team_name=self._clean_team_name(data.get("full_name"), team_name),
            wins=int(data.get("wins")) if data.get("wins") is not None else None,
            losses=int(data.get("losses")) if data.get("losses") is not None else None,
            position=int(data.get("division_position")) if data.get("division_position") is not None else None,
            gb=float(data.get("games_back")) if data.get("games_back") is not None else None,
            made_playoffs=bool(data.get("made_playoffs")),
            won_playoffs=bool(data.get("won_playoffs")),
            best_hitter=_clean_name(data.get("best_hitter_name")),
            best_pitcher=_clean_name(data.get("best_pitcher_name")),
            best_rookie=_clean_name(data.get("best_rookie_name")),
        )

    def _get_team_header_summary(self, team_name: str) -> dict[str, object] | None:
        from sqlalchemy import text

        sql = """
            SELECT
                TRIM(CONCAT(COALESCE(t.name, ''), ' ', COALESCE(t.nickname, ''))) AS full_name,
                tr.w AS wins,
                tr.l AS losses,
                tr.pos AS division_position,
                tr.gb AS games_back
            FROM teams t
            LEFT JOIN team_record tr ON tr.team_id = t.team_id
            WHERE TRIM(CONCAT(COALESCE(t.name, ''), ' ', COALESCE(t.nickname, ''))) = :team_name
            ORDER BY t.team_id
            LIMIT 1
        """
        try:
            with self._engine.connect() as conn:
                row = conn.execute(text(sql), {"team_name": team_name}).fetchone()
        except Exception:
            return None

        if row is None:
            return None

        data = row._mapping if hasattr(row, "_mapping") else row
        wins = data.get("wins")
        losses = data.get("losses")
        position = data.get("division_position")
        games_back = data.get("games_back")

        if wins is None and losses is None and position is None and games_back is None:
            return None

        return {
            "team_name": self._clean_team_name(data.get("full_name"), team_name),
            "wins": wins,
            "losses": losses,
            "position": position,
            "gb": games_back,
        }

    def _build_roster(self, team_name: str) -> pd.DataFrame:
            sql = """
            SELECT
                CASE
                    WHEN p.position = 1 THEN
                        CASE
                            WHEN p.role = 1 THEN 'SP'
                            WHEN p.role = 2 THEN 'RP'
                            WHEN p.role = 3 THEN 'CL'
                            ELSE 'P'
                        END
                    WHEN p.position = 2 THEN 'C'
                    WHEN p.position = 3 THEN '1B'
                    WHEN p.position = 4 THEN '2B'
                    WHEN p.position = 5 THEN '3B'
                    WHEN p.position = 6 THEN 'SS'
                    WHEN p.position = 7 THEN 'LF'
                    WHEN p.position = 8 THEN 'CF'
                    WHEN p.position = 9 THEN 'RF'
                    ELSE ''
                END AS POS,
                p.uniform_number AS `#`,
                TRIM(CONCAT(COALESCE(p.first_name, ''), ' ', COALESCE(p.last_name, ''))) AS Name,
                '' AS Inf,
                p.age AS Age,
                CASE
                    WHEN p.bats = 1 THEN 'Left'
                    WHEN p.bats = 2 THEN 'Right'
                    WHEN p.bats = 3 THEN 'Switch'
                    ELSE ''
                END AS B,
                CASE
                    WHEN p.throws = 1 THEN 'Left'
                    WHEN p.throws = 2 THEN 'Right'
                    ELSE ''
                END AS T,
                CASE WHEN COALESCE(p.injury_is_injured, 0) = 1 THEN 'Injured' ELSE '-' END AS INJ,
                CASE
                    WHEN COALESCE(p.injury_is_injured, 0) = 1 THEN CONCAT('Out ', COALESCE(p.injury_left, 0), ' days')
                    ELSE '-'
                END AS INJ_1,
                CASE
                    WHEN COALESCE(prs.is_on_dl, 0) = 1 OR COALESCE(prs.is_on_dl60, 0) = 1 THEN 'Injured List'
                    WHEN COALESCE(prs.is_active, 0) = 1 THEN 'Active'
                    ELSE 'Reserve'
                END AS Status
            FROM players p
            JOIN teams t ON t.team_id = p.team_id
            LEFT JOIN players_roster_status prs ON prs.player_id = p.player_id AND prs.team_id = p.team_id
            WHERE CONCAT(t.name, ' ', t.nickname) = :team_name
                AND COALESCE(p.retired, 0) = 0
            ORDER BY Name
            """
            return self._read_sql(sql, {"team_name": team_name})

    def _build_batting(self, team_name: str) -> pd.DataFrame:
            sql = """
            WITH latest AS (
                SELECT MAX(year) AS year_val FROM players_game_batting
            ),
            war AS (
                SELECT pcs.player_id, SUM(COALESCE(pcs.war, 0)) AS war_total
                FROM players_career_batting_stats pcs
                JOIN latest l ON pcs.year = l.year_val
                WHERE pcs.split_id = 1
                GROUP BY pcs.player_id
            ),
            ball_data AS (
                SELECT
                    pgb.player_id,
                    COUNT(CASE WHEN pabs.exit_velo > 0 THEN 1 END) AS tracked_bip,
                    ROUND(AVG(CASE WHEN pabs.exit_velo > 0 THEN pabs.exit_velo END), 1) AS avg_exit_velo,
                    ROUND(
                        SUM(CASE WHEN pabs.exit_velo >= 95 THEN 1 ELSE 0 END)
                        / NULLIF(COUNT(CASE WHEN pabs.exit_velo > 0 THEN 1 END), 0),
                        3
                    ) AS hard_hit_rate,
                    ROUND(
                        SUM(CASE WHEN pabs.exit_velo >= 95 AND pabs.launch_angle >= 8 AND pabs.launch_angle <= 32 THEN 1 ELSE 0 END)
                        / NULLIF(COUNT(CASE WHEN pabs.exit_velo > 0 THEN 1 END), 0),
                        3
                    ) AS barrel_rate,
                    ROUND(
                        SUM(CASE WHEN pabs.launch_angle >= 8 AND pabs.launch_angle <= 32 THEN 1 ELSE 0 END)
                        / NULLIF(COUNT(CASE WHEN pabs.exit_velo > 0 THEN 1 END), 0),
                        3
                    ) AS sweet_spot_rate,
                    ROUND(
                        SUM(CASE WHEN pabs.exit_velo < 85 OR pabs.launch_angle < -30 OR pabs.launch_angle > 50 THEN 1 ELSE 0 END)
                        / NULLIF(COUNT(CASE WHEN pabs.exit_velo > 0 THEN 1 END), 0),
                        3
                    ) AS weak_contact_rate
                FROM players_game_batting pgb
                JOIN latest l ON pgb.year = l.year_val
                JOIN teams t2 ON t2.team_id = pgb.team_id
                LEFT JOIN players_at_bat_batting_stats pabs
                    ON pabs.player_id = pgb.player_id
                    AND pabs.game_id = pgb.game_id
                    AND pabs.team_id = pgb.team_id
                    AND pabs.exit_velo > 0
                WHERE CONCAT(t2.name, ' ', t2.nickname) = :team_name
                GROUP BY pgb.player_id
            )
            SELECT
                CASE
                    WHEN p.position = 2 THEN 'C'
                    WHEN p.position = 3 THEN '1B'
                    WHEN p.position = 4 THEN '2B'
                    WHEN p.position = 5 THEN '3B'
                    WHEN p.position = 6 THEN 'SS'
                    WHEN p.position = 7 THEN 'LF'
                    WHEN p.position = 8 THEN 'CF'
                    WHEN p.position = 9 THEN 'RF'
                    ELSE 'DH'
                END AS POS,
                p.uniform_number AS `#`,
                TRIM(CONCAT(COALESCE(p.first_name, ''), ' ', COALESCE(p.last_name, ''))) AS Name,
                '' AS Inf,
                CASE WHEN p.bats = 1 THEN 'L' WHEN p.bats = 2 THEN 'R' WHEN p.bats = 3 THEN 'S' ELSE '' END AS B,
                CASE WHEN p.throws = 1 THEN 'L' WHEN p.throws = 2 THEN 'R' ELSE '' END AS T,
                COUNT(*) AS G,
                SUM(COALESCE(pgb.pa, 0)) AS PA,
                SUM(COALESCE(pgb.ab, 0)) AS AB,
                SUM(COALESCE(pgb.h, 0)) AS H,
                SUM(COALESCE(pgb.d, 0)) AS `2B`,
                SUM(COALESCE(pgb.t, 0)) AS `3B`,
                SUM(COALESCE(pgb.hr, 0)) AS HR,
                SUM(COALESCE(pgb.rbi, 0)) AS RBI,
                SUM(COALESCE(pgb.r, 0)) AS R,
                SUM(COALESCE(pgb.bb, 0)) AS BB,
                SUM(COALESCE(pgb.ibb, 0)) AS IBB,
                SUM(COALESCE(pgb.hp, 0)) AS HP,
                SUM(COALESCE(pgb.k, 0)) AS K,
                SUM(COALESCE(pgb.gdp, 0)) AS GIDP,
                ROUND(SUM(COALESCE(pgb.h, 0)) / NULLIF(SUM(COALESCE(pgb.ab, 0)), 0), 3) AS AVG,
                ROUND(
                    (SUM(COALESCE(pgb.h, 0)) + SUM(COALESCE(pgb.bb, 0)) + SUM(COALESCE(pgb.hp, 0)))
                    / NULLIF(SUM(COALESCE(pgb.ab, 0)) + SUM(COALESCE(pgb.bb, 0)) + SUM(COALESCE(pgb.hp, 0)) + SUM(COALESCE(pgb.sf, 0)), 0),
                    3
                ) AS OBP,
                ROUND(
                    (
                        SUM(COALESCE(pgb.h, 0) - COALESCE(pgb.d, 0) - COALESCE(pgb.t, 0) - COALESCE(pgb.hr, 0))
                        + 2 * SUM(COALESCE(pgb.d, 0))
                        + 3 * SUM(COALESCE(pgb.t, 0))
                        + 4 * SUM(COALESCE(pgb.hr, 0))
                    ) / NULLIF(SUM(COALESCE(pgb.ab, 0)), 0),
                    3
                ) AS SLG,
                ROUND(
                    (
                        (
                            SUM(COALESCE(pgb.h, 0) - COALESCE(pgb.d, 0) - COALESCE(pgb.t, 0) - COALESCE(pgb.hr, 0))
                            + 2 * SUM(COALESCE(pgb.d, 0))
                            + 3 * SUM(COALESCE(pgb.t, 0))
                            + 4 * SUM(COALESCE(pgb.hr, 0))
                        ) / NULLIF(SUM(COALESCE(pgb.ab, 0)), 0)
                    )
                    - (SUM(COALESCE(pgb.h, 0)) / NULLIF(SUM(COALESCE(pgb.ab, 0)), 0)),
                    3
                ) AS ISO,
                ROUND(
                    (
                        (SUM(COALESCE(pgb.h, 0)) + SUM(COALESCE(pgb.bb, 0)) + SUM(COALESCE(pgb.hp, 0)))
                        / NULLIF(SUM(COALESCE(pgb.ab, 0)) + SUM(COALESCE(pgb.bb, 0)) + SUM(COALESCE(pgb.hp, 0)) + SUM(COALESCE(pgb.sf, 0)), 0)
                    )
                    +
                    (
                        (
                            SUM(COALESCE(pgb.h, 0) - COALESCE(pgb.d, 0) - COALESCE(pgb.t, 0) - COALESCE(pgb.hr, 0))
                            + 2 * SUM(COALESCE(pgb.d, 0))
                            + 3 * SUM(COALESCE(pgb.t, 0))
                            + 4 * SUM(COALESCE(pgb.hr, 0))
                        ) / NULLIF(SUM(COALESCE(pgb.ab, 0)), 0)
                    ),
                    3
                ) AS OPS,
                100 AS `OPS+`,
                ROUND(
                    (SUM(COALESCE(pgb.h, 0)) - SUM(COALESCE(pgb.hr, 0)))
                    / NULLIF(SUM(COALESCE(pgb.ab, 0)) - SUM(COALESCE(pgb.k, 0)) - SUM(COALESCE(pgb.hr, 0)) + SUM(COALESCE(pgb.sf, 0)), 0),
                    3
                ) AS BABIP,
                ROUND(COALESCE(w.war_total, 0), 1) AS WAR,
                SUM(COALESCE(pgb.sb, 0)) AS SB,
                SUM(COALESCE(pgb.cs, 0)) AS CS,
                COALESCE(bd.avg_exit_velo, 0) AS avg_exit_velo,
                COALESCE(bd.hard_hit_rate, 0) AS hard_hit_rate,
                COALESCE(bd.barrel_rate, 0) AS barrel_rate,
                COALESCE(bd.sweet_spot_rate, 0) AS sweet_spot_rate,
                COALESCE(bd.weak_contact_rate, 0) AS weak_contact_rate
            FROM players_game_batting pgb
            JOIN latest l ON pgb.year = l.year_val
            JOIN players p ON p.player_id = pgb.player_id
            JOIN teams t ON t.team_id = pgb.team_id
            LEFT JOIN war w ON w.player_id = pgb.player_id
            LEFT JOIN ball_data bd ON bd.player_id = pgb.player_id
            WHERE CONCAT(t.name, ' ', t.nickname) = :team_name
            GROUP BY p.player_id, p.uniform_number, p.first_name, p.last_name, p.position, p.bats, p.throws, w.war_total, bd.avg_exit_velo, bd.hard_hit_rate, bd.barrel_rate, bd.sweet_spot_rate, bd.weak_contact_rate
            ORDER BY PA DESC, Name
            """
            return self._read_sql(sql, {"team_name": team_name})

    def _build_pitching(self, team_name: str) -> pd.DataFrame:
            sql = """
            WITH latest AS (
                SELECT MAX(year) AS year_val FROM players_game_pitching_stats
            ),
            war AS (
                SELECT pcs.player_id, SUM(COALESCE(pcs.war, 0)) AS war_total
                FROM players_career_pitching_stats pcs
                JOIN latest l ON pcs.year = l.year_val
                WHERE pcs.split_id = 1
                GROUP BY pcs.player_id
            )
            SELECT
                CASE
                    WHEN p.position = 1 THEN
                        CASE
                            WHEN p.role = 1 THEN 'SP'
                            WHEN p.role = 2 THEN 'RP'
                            WHEN p.role = 3 THEN 'CL'
                            ELSE 'P'
                        END
                    ELSE 'P'
                END AS POS,
                p.uniform_number AS `#`,
                TRIM(CONCAT(COALESCE(p.first_name, ''), ' ', COALESCE(p.last_name, ''))) AS Name,
                '' AS Inf,
                CASE WHEN p.bats = 1 THEN 'L' WHEN p.bats = 2 THEN 'R' WHEN p.bats = 3 THEN 'S' ELSE '' END AS B,
                CASE WHEN p.throws = 1 THEN 'L' WHEN p.throws = 2 THEN 'R' ELSE '' END AS T,
                SUM(COALESCE(pgp.g, 0)) AS G,
                SUM(COALESCE(pgp.gs, 0)) AS GS,
                SUM(COALESCE(pgp.w, 0)) AS W,
                SUM(COALESCE(pgp.l, 0)) AS L,
                SUM(COALESCE(pgp.s, 0)) AS SV,
                SUM(COALESCE(pgp.hld, 0)) AS HLD,
                ROUND(
                    FLOOR(
                        SUM(
                            COALESCE(
                                pgp.outs,
                                FLOOR(COALESCE(pgp.ip, 0)) * 3
                                + ROUND((COALESCE(pgp.ip, 0) - FLOOR(COALESCE(pgp.ip, 0))) * 10)
                            )
                        ) / 3
                    )
                    + (
                        MOD(
                            SUM(
                                COALESCE(
                                    pgp.outs,
                                    FLOOR(COALESCE(pgp.ip, 0)) * 3
                                    + ROUND((COALESCE(pgp.ip, 0) - FLOOR(COALESCE(pgp.ip, 0))) * 10)
                                )
                            ),
                            3
                        ) / 10
                    ),
                    1
                ) AS IP,
                SUM(COALESCE(pgp.ha, 0)) AS HA,
                SUM(COALESCE(pgp.hra, 0)) AS HR,
                SUM(COALESCE(pgp.r, 0)) AS R,
                SUM(COALESCE(pgp.er, 0)) AS ER,
                SUM(COALESCE(pgp.bb, 0)) AS BB,
                SUM(COALESCE(pgp.k, 0)) AS K,
                SUM(COALESCE(pgp.hp, 0)) AS HP,
                SUM(COALESCE(pgp.gb, 0)) AS GB,
                SUM(COALESCE(pgp.fb, 0)) AS FB,
                ROUND(
                    27 * SUM(COALESCE(pgp.er, 0))
                    / NULLIF(
                        SUM(
                            COALESCE(
                                pgp.outs,
                                FLOOR(COALESCE(pgp.ip, 0)) * 3
                                + ROUND((COALESCE(pgp.ip, 0) - FLOOR(COALESCE(pgp.ip, 0))) * 10)
                            )
                        ),
                        0
                    ),
                    2
                ) AS ERA,
                ROUND(SUM(COALESCE(pgp.ha, 0)) / NULLIF(SUM(COALESCE(pgp.ab, 0)), 0), 3) AS AVG,
                ROUND((SUM(COALESCE(pgp.ha, 0)) - SUM(COALESCE(pgp.hra, 0))) / NULLIF(SUM(COALESCE(pgp.ab, 0)) - SUM(COALESCE(pgp.k, 0)) - SUM(COALESCE(pgp.hra, 0)), 0), 3) AS BABIP,
                ROUND(
                    3 * (SUM(COALESCE(pgp.ha, 0)) + SUM(COALESCE(pgp.bb, 0)))
                    / NULLIF(
                        SUM(
                            COALESCE(
                                pgp.outs,
                                FLOOR(COALESCE(pgp.ip, 0)) * 3
                                + ROUND((COALESCE(pgp.ip, 0) - FLOOR(COALESCE(pgp.ip, 0))) * 10)
                            )
                        ),
                        0
                    ),
                    2
                ) AS WHIP,
                ROUND(
                    27 * SUM(COALESCE(pgp.hra, 0))
                    / NULLIF(
                        SUM(
                            COALESCE(
                                pgp.outs,
                                FLOOR(COALESCE(pgp.ip, 0)) * 3
                                + ROUND((COALESCE(pgp.ip, 0) - FLOOR(COALESCE(pgp.ip, 0))) * 10)
                            )
                        ),
                        0
                    ),
                    1
                ) AS `HR/9`,
                ROUND(
                    27 * SUM(COALESCE(pgp.bb, 0))
                    / NULLIF(
                        SUM(
                            COALESCE(
                                pgp.outs,
                                FLOOR(COALESCE(pgp.ip, 0)) * 3
                                + ROUND((COALESCE(pgp.ip, 0) - FLOOR(COALESCE(pgp.ip, 0))) * 10)
                            )
                        ),
                        0
                    ),
                    1
                ) AS `BB/9`,
                ROUND(
                    27 * SUM(COALESCE(pgp.k, 0))
                    / NULLIF(
                        SUM(
                            COALESCE(
                                pgp.outs,
                                FLOOR(COALESCE(pgp.ip, 0)) * 3
                                + ROUND((COALESCE(pgp.ip, 0) - FLOOR(COALESCE(pgp.ip, 0))) * 10)
                            )
                        ),
                        0
                    ),
                    1
                ) AS `K/9`,
                ROUND(SUM(COALESCE(pgp.k, 0)) / NULLIF(SUM(COALESCE(pgp.bb, 0)), 0), 1) AS `K/BB`,
                100 AS `ERA+`,
                ROUND(
                    ((13 * SUM(COALESCE(pgp.hra, 0))) + (3 * SUM(COALESCE(pgp.bb, 0))) - (2 * SUM(COALESCE(pgp.k, 0))))
                    * 3
                    / NULLIF(
                        SUM(
                            COALESCE(
                                pgp.outs,
                                FLOOR(COALESCE(pgp.ip, 0)) * 3
                                + ROUND((COALESCE(pgp.ip, 0) - FLOOR(COALESCE(pgp.ip, 0))) * 10)
                            )
                        ),
                        0
                    )
                    + 3.20,
                    2
                ) AS FIP,
                ROUND(COALESCE(w.war_total, 0), 1) AS WAR
            FROM players_game_pitching_stats pgp
            JOIN latest l ON pgp.year = l.year_val
            JOIN players p ON p.player_id = pgp.player_id
            JOIN teams t ON t.team_id = pgp.team_id
            LEFT JOIN war w ON w.player_id = pgp.player_id
            WHERE CONCAT(t.name, ' ', t.nickname) = :team_name
            GROUP BY p.player_id, p.uniform_number, p.first_name, p.last_name, p.position, p.role, p.bats, p.throws, w.war_total
            ORDER BY IP DESC, Name
            """
            return self._read_sql(sql, {"team_name": team_name})

    def _build_player_ratings(self) -> pd.DataFrame:
            sql = """
            SELECT
                CASE
                    WHEN p.position = 1 THEN
                        CASE
                            WHEN p.role = 1 THEN 'SP'
                            WHEN p.role = 2 THEN 'RP'
                            WHEN p.role = 3 THEN 'CL'
                            ELSE 'P'
                        END
                    WHEN p.position = 2 THEN 'C'
                    WHEN p.position = 3 THEN '1B'
                    WHEN p.position = 4 THEN '2B'
                    WHEN p.position = 5 THEN '3B'
                    WHEN p.position = 6 THEN 'SS'
                    WHEN p.position = 7 THEN 'LF'
                    WHEN p.position = 8 THEN 'CF'
                    WHEN p.position = 9 THEN 'RF'
                    ELSE ''
                END AS POS,
                p.uniform_number AS `#`,
                TRIM(CONCAT(COALESCE(p.first_name, ''), ' ', COALESCE(p.last_name, ''))) AS Name,
                p.first_name AS `First Name`,
                p.last_name AS `Last Name`,
                '' AS Inf,
                t.nickname AS TM,
                org.nickname AS ORG,
                p.date_of_birth AS DOB,
                p.age AS Age,
                '' AS NAT,
                CASE WHEN p.bats = 1 THEN 'Left' WHEN p.bats = 2 THEN 'Right' WHEN p.bats = 3 THEN 'Switch' ELSE '' END AS B,
                CASE WHEN p.throws = 1 THEN 'Left' WHEN p.throws = 2 THEN 'Right' ELSE '' END AS T,
                '' AS OVR,
                '' AS POT,
                CASE WHEN COALESCE(p.injury_is_injured, 0) = 1 THEN 'Injured' ELSE '-' END AS INJ,
                CASE
                    WHEN COALESCE(p.injury_is_injured, 0) = 1 THEN CONCAT('Out ', COALESCE(p.injury_left, 0), ' days')
                    ELSE '-'
                END AS INJ_1,
                '-' AS `Left`,
                '-' AS SLR,
                0 AS YL,
                0 AS MLY,
                'Average' AS SctAcc,
                CASE
                    WHEN p.position = 1 THEN COALESCE(pp.pitching_ratings_overall_stuff, 0)
                    ELSE COALESCE(pb.batting_ratings_overall_contact, 0)
                END AS `CON/STU`,
                CASE
                    WHEN p.position = 1 THEN COALESCE(pp.pitching_ratings_overall_stuff, 0)
                    ELSE COALESCE(pb.batting_ratings_overall_strikeouts, 0)
                END AS `AVK/STU`,
                CASE
                    WHEN p.position = 1 THEN COALESCE(pp.pitching_ratings_overall_pbabip, 0)
                    ELSE COALESCE(pb.batting_ratings_overall_gap, 0)
                END AS `BA/PBA`,
                CASE
                    WHEN p.position = 1 THEN COALESCE(pp.pitching_ratings_overall_movement, 0)
                    ELSE COALESCE(pb.batting_ratings_overall_power, 0)
                END AS `POW/MOV`,
                CASE
                    WHEN p.position = 1 THEN COALESCE(pp.pitching_ratings_overall_hra, 0)
                    ELSE COALESCE(pb.batting_ratings_overall_power, 0)
                END AS `POW/HRA`,
                CASE
                    WHEN p.position = 1 THEN COALESCE(pp.pitching_ratings_overall_control, 0)
                    ELSE COALESCE(pb.batting_ratings_overall_eye, 0)
                END AS `EYE/CON`,
                CASE
                    WHEN p.position = 1 THEN COALESCE(pp.pitching_ratings_misc_stamina, 0)
                    ELSE COALESCE(pf.fielding_ratings_infield_range, 0)
                END AS `FLD/STA`,
                CASE
                    WHEN p.position = 1 THEN COALESCE(pp.pitching_ratings_talent_stuff, 0)
                    ELSE COALESCE(pb.batting_ratings_talent_contact, 0)
                END AS `CON/STU P`,
                CASE
                    WHEN p.position = 1 THEN COALESCE(pp.pitching_ratings_talent_movement, 0)
                    ELSE COALESCE(pb.batting_ratings_talent_power, 0)
                END AS `POW/MOV P`,
                CASE
                    WHEN p.position = 1 THEN COALESCE(pp.pitching_ratings_talent_control, 0)
                    ELSE COALESCE(pb.batting_ratings_talent_eye, 0)
                END AS `EYE/CON P`,
                COALESCE(pb.batting_ratings_vsl_contact, 0) AS vsl_contact,
                COALESCE(pb.batting_ratings_vsl_power, 0) AS vsl_power,
                COALESCE(pb.batting_ratings_vsl_eye, 0) AS vsl_eye,
                COALESCE(pb.batting_ratings_vsr_contact, 0) AS vsr_contact,
                COALESCE(pb.batting_ratings_vsr_power, 0) AS vsr_power,
                COALESCE(pb.batting_ratings_vsr_eye, 0) AS vsr_eye,
                COALESCE(pb.running_ratings_speed, 0) AS running_speed,
                COALESCE(pb.running_ratings_baserunning, 0) AS running_baserunning,
                COALESCE(pb.running_ratings_stealing_rate, 0) AS running_stealing_rate,
                COALESCE(pf.fielding_ratings_catcher_ability, 0) AS field_c_ability,
                COALESCE(pf.fielding_ratings_catcher_arm, 0) AS field_c_arm,
                COALESCE(pf.fielding_ratings_catcher_framing, 0) AS field_c_framing,
                COALESCE(pf.fielding_ratings_infield_range, 0) AS field_if_range,
                COALESCE(pf.fielding_ratings_infield_arm, 0) AS field_if_arm,
                COALESCE(pf.fielding_ratings_infield_error, 0) AS field_if_error,
                COALESCE(pf.fielding_ratings_outfield_range, 0) AS field_of_range,
                COALESCE(pf.fielding_ratings_outfield_arm, 0) AS field_of_arm,
                COALESCE(pf.fielding_ratings_outfield_error, 0) AS field_of_error,
                COALESCE(pp.pitching_ratings_misc_ground_fly, 0) AS pitch_ground_fly,
                COALESCE(pp.pitching_ratings_vsl_stuff, 0) AS pitch_vsl_stuff,
                COALESCE(pp.pitching_ratings_vsl_movement, 0) AS pitch_vsl_movement,
                COALESCE(pp.pitching_ratings_vsl_control, 0) AS pitch_vsl_control,
                COALESCE(pp.pitching_ratings_vsr_stuff, 0) AS pitch_vsr_stuff,
                COALESCE(pp.pitching_ratings_vsr_movement, 0) AS pitch_vsr_movement,
                COALESCE(pp.pitching_ratings_vsr_control, 0) AS pitch_vsr_control,
                COALESCE(pp.pitching_ratings_misc_stamina, 0) AS pitch_stamina,
                p.historical_id AS HistID
            FROM players p
            JOIN teams t ON t.team_id = p.team_id
            LEFT JOIN teams org ON org.team_id = p.organization_id
            LEFT JOIN players_batting pb ON pb.player_id = p.player_id AND pb.team_id = p.team_id
            LEFT JOIN players_pitching pp ON pp.player_id = p.player_id AND pp.team_id = p.team_id
            LEFT JOIN players_fielding pf ON pf.player_id = p.player_id AND pf.team_id = p.team_id
            WHERE COALESCE(p.retired, 0) = 0
            """
            return self._read_sql(sql, {})


class PlayerDataTransformer:
    @staticmethod
    def clean_cols(df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df.columns = (
            df.columns.astype(str)
            .str.lower()
            .str.strip()
            .str.replace("/", "_", regex=False)
            .str.replace(" ", "_", regex=False)
            .str.replace("%", "pct", regex=False)
            .str.replace("+", "_plus", regex=False)
            .str.replace("-", "_", regex=False)
        )
        return df

    @staticmethod
    def get_name_series(df: pd.DataFrame) -> pd.Series:
        for col in ["name", "player", "player_name"]:
            if col in df.columns:
                return df[col].fillna("").astype(str).str.strip()
        if "first_name" in df.columns and "last_name" in df.columns:
            first = df["first_name"].fillna("").astype(str).str.strip()
            last = df["last_name"].fillna("").astype(str).str.strip()
            return (first + " " + last).str.replace(r"\s+", " ", regex=True).str.strip()
        raise ValueError(f"Could not find player name column in columns: {list(df.columns)}")

    @staticmethod
    def normalize_player_name(series: pd.Series) -> pd.Series:
        s = series.fillna("").astype(str).str.lower().str.strip()
        s = s.str.replace(r"[.,'`-]", "", regex=True)
        s = s.str.replace(r"\b(jr|sr|ii|iii|iv)\b", "", regex=True)
        s = s.str.replace(r"\s+", " ", regex=True).str.strip()
        return s

    @classmethod
    def attach_name(cls, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df["player_name"] = cls.get_name_series(df)
        df["player_key"] = cls.normalize_player_name(df["player_name"])
        return df

    @staticmethod
    def first_col(df: pd.DataFrame, aliases: list[str]) -> str | None:
        for col in aliases:
            if col in df.columns:
                return col
        return None

    @classmethod
    def num_alias(cls, df: pd.DataFrame, aliases: list[str]) -> pd.Series:
        col = cls.first_col(df, aliases)
        if col is None:
            return pd.Series(0, index=df.index, dtype="float64")
        return pd.to_numeric(df[col], errors="coerce").fillna(0)

    @staticmethod
    def innings_notation_to_decimal(ip_series: pd.Series) -> pd.Series:
        """Convert MLB innings notation (e.g., 5.1/5.2) to true decimal innings.

        Values that do not match MLB notation are treated as already-decimal.
        """
        ip = pd.to_numeric(ip_series, errors="coerce").fillna(0.0)
        whole = ip.astype(float).floordiv(1)
        frac = ip - whole
        outs = (frac * 10).round()
        is_notation = outs.isin([0, 1, 2]) & ((frac - (outs / 10.0)).abs() < 1e-6)
        notation_decimal = whole + (outs / 3.0)
        return notation_decimal.where(is_notation, ip)

    @staticmethod
    def dedupe(df: pd.DataFrame, keep_col: str | None = None) -> pd.DataFrame:
        df = df.copy()
        if keep_col and keep_col in df.columns:
            df = df.sort_values(keep_col, ascending=False, na_position="last")
        return df.drop_duplicates(subset=["player_key"], keep="first").reset_index(drop=True)

    @staticmethod
    def prep_roster(df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        keep_cols = ["player_name", "player_key"]
        for col in ["pos", "b", "t", "inj", "inj_1", "status", "age"]:
            if col in df.columns:
                keep_cols.append(col)
        df = df[keep_cols].copy()

        df["primary_position"] = df["pos"].astype(str).str.upper() if "pos" in df.columns else ""
        df["bats"] = df["b"].astype(str).str.upper() if "b" in df.columns else ""
        df["throws"] = df["t"].astype(str).str.upper() if "t" in df.columns else ""
        df["age_val"] = pd.to_numeric(df["age"], errors="coerce") if "age" in df.columns else 0

        if "inj_1" in df.columns:
            df["injury_text"] = df["inj_1"].astype(str)
        elif "inj" in df.columns:
            df["injury_text"] = df["inj"].astype(str)
        elif "status" in df.columns:
            df["injury_text"] = df["status"].astype(str)
        else:
            df["injury_text"] = ""

        df["injured_flag"] = df["injury_text"].str.contains(
            "inj|out|day|week|month|torn|strain|surgery|labrum|ucl|hamstring|elbow",
            case=False,
            na=False,
        )

        pos = df["primary_position"].astype(str).str.upper()
        df["is_pitcher"] = pos.str.contains("SP|RP|CL|P", regex=True, na=False)
        df["is_starter_role"] = pos.str.contains("SP", regex=False, na=False)
        df["is_reliever_role"] = pos.str.contains("RP|CL", regex=True, na=False)

        df["is_c"] = pos.str.contains(r"(?:^|[^A-Z])C(?:[^A-Z]|$)", regex=True, na=False)
        df["is_1b"] = pos.str.contains("1B", regex=False, na=False)
        df["is_2b"] = pos.str.contains("2B", regex=False, na=False)
        df["is_3b"] = pos.str.contains("3B", regex=False, na=False)
        df["is_ss"] = pos.str.contains("SS", regex=False, na=False)
        df["is_lf"] = pos.str.contains("LF", regex=False, na=False)
        df["is_cf"] = pos.str.contains("CF", regex=False, na=False)
        df["is_rf"] = pos.str.contains("RF", regex=False, na=False)

        df["is_middle_if"] = df["is_2b"] | df["is_ss"]
        df["is_corner_if"] = df["is_1b"] | df["is_3b"]
        df["is_of"] = df["is_lf"] | df["is_cf"] | df["is_rf"]
        df["is_hitter"] = ~df["is_pitcher"]
        return df

    @staticmethod
    def stat_merge(roster: pd.DataFrame, stats: pd.DataFrame) -> pd.DataFrame:
        stat_cols = [c for c in stats.columns if c not in ["player_name"]]
        return roster.merge(stats[stat_cols], on="player_key", how="left")

    @classmethod
    def prepare_ratings(cls, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df["contact_now"] = cls.num_alias(df, ["con_stu"])
        df["avoid_k_now"] = cls.num_alias(df, ["avk_stu"])
        df["gap_now"] = cls.num_alias(df, ["ba_pba"])
        df["power_now"] = cls.num_alias(df, ["pow_mov"])
        df["eye_now"] = cls.num_alias(df, ["eye_con"])
        df["field_now"] = cls.num_alias(df, ["fld_sta"])

        df["contact_pot"] = cls.num_alias(df, ["con_stu_p"])
        df["avoid_k_pot"] = cls.num_alias(df, ["con_stu_p"])
        df["gap_pot"] = cls.num_alias(df, ["con_stu_p"])
        df["power_pot"] = cls.num_alias(df, ["pow_mov_p"])
        df["eye_pot"] = cls.num_alias(df, ["eye_con_p"])
        df["field_pot"] = cls.num_alias(df, ["eye_con_p"])

        df["stuff_now"] = cls.num_alias(df, ["con_stu"])
        df["movement_now"] = cls.num_alias(df, ["pow_mov"])
        df["control_now"] = cls.num_alias(df, ["eye_con"])
        df["stamina_now"] = cls.num_alias(df, ["fld_sta"])

        df["stuff_pot"] = cls.num_alias(df, ["con_stu_p"])
        df["movement_pot"] = cls.num_alias(df, ["pow_mov_p"])
        df["control_pot"] = cls.num_alias(df, ["eye_con_p"])
        df["stamina_pot"] = cls.num_alias(df, ["eye_con_p"])

        df["vsl_contact"] = cls.num_alias(df, ["vsl_contact", "batting_ratings_vsl_contact"])
        df["vsl_power"] = cls.num_alias(df, ["vsl_power", "batting_ratings_vsl_power"])
        df["vsl_eye"] = cls.num_alias(df, ["vsl_eye", "batting_ratings_vsl_eye"])
        df["vsr_contact"] = cls.num_alias(df, ["vsr_contact", "batting_ratings_vsr_contact"])
        df["vsr_power"] = cls.num_alias(df, ["vsr_power", "batting_ratings_vsr_power"])
        df["vsr_eye"] = cls.num_alias(df, ["vsr_eye", "batting_ratings_vsr_eye"])

        df["running_speed"] = cls.num_alias(df, ["running_speed", "running_ratings_speed"])
        df["running_baserunning"] = cls.num_alias(df, ["running_baserunning", "running_ratings_baserunning"])
        df["running_stealing_rate"] = cls.num_alias(df, ["running_stealing_rate", "running_ratings_stealing_rate"])

        df["field_c_ability"] = cls.num_alias(df, ["field_c_ability", "fielding_ratings_catcher_ability"])
        df["field_c_arm"] = cls.num_alias(df, ["field_c_arm", "fielding_ratings_catcher_arm"])
        df["field_c_framing"] = cls.num_alias(df, ["field_c_framing", "fielding_ratings_catcher_framing"])
        df["field_if_range"] = cls.num_alias(df, ["field_if_range", "fielding_ratings_infield_range"])
        df["field_if_arm"] = cls.num_alias(df, ["field_if_arm", "fielding_ratings_infield_arm"])
        df["field_if_error"] = cls.num_alias(df, ["field_if_error", "fielding_ratings_infield_error"])
        df["field_of_range"] = cls.num_alias(df, ["field_of_range", "fielding_ratings_outfield_range"])
        df["field_of_arm"] = cls.num_alias(df, ["field_of_arm", "fielding_ratings_outfield_arm"])
        df["field_of_error"] = cls.num_alias(df, ["field_of_error", "fielding_ratings_outfield_error"])

        df["pitch_ground_fly"] = cls.num_alias(df, ["pitch_ground_fly", "pitching_ratings_misc_ground_fly"])
        df["pitch_vsl_stuff"] = cls.num_alias(df, ["pitch_vsl_stuff", "pitching_ratings_vsl_stuff"])
        df["pitch_vsl_movement"] = cls.num_alias(df, ["pitch_vsl_movement", "pitching_ratings_vsl_movement"])
        df["pitch_vsl_control"] = cls.num_alias(df, ["pitch_vsl_control", "pitching_ratings_vsl_control"])
        df["pitch_vsr_stuff"] = cls.num_alias(df, ["pitch_vsr_stuff", "pitching_ratings_vsr_stuff"])
        df["pitch_vsr_movement"] = cls.num_alias(df, ["pitch_vsr_movement", "pitching_ratings_vsr_movement"])
        df["pitch_vsr_control"] = cls.num_alias(df, ["pitch_vsr_control", "pitching_ratings_vsr_control"])
        df["pitch_stamina"] = cls.num_alias(df, ["pitch_stamina", "pitching_ratings_misc_stamina"])

        age_series = cls.num_alias(df, ["age"])
        df["age_rating_val"] = age_series if (age_series != 0).any() else 0
        return df

    @staticmethod
    def merge_ratings(team_df: pd.DataFrame, players_df: pd.DataFrame) -> pd.DataFrame:
        cols = [
            "player_key",
            "contact_now",
            "gap_now",
            "power_now",
            "eye_now",
            "avoid_k_now",
            "contact_pot",
            "gap_pot",
            "power_pot",
            "eye_pot",
            "avoid_k_pot",
            "stuff_now",
            "movement_now",
            "control_now",
            "stuff_pot",
            "movement_pot",
            "control_pot",
            "stamina_now",
            "stamina_pot",
            "age_rating_val",
            "vsl_contact",
            "vsl_power",
            "vsl_eye",
            "vsr_contact",
            "vsr_power",
            "vsr_eye",
            "running_speed",
            "running_baserunning",
            "running_stealing_rate",
            "field_c_ability",
            "field_c_arm",
            "field_c_framing",
            "field_if_range",
            "field_if_arm",
            "field_if_error",
            "field_of_range",
            "field_of_arm",
            "field_of_error",
            "pitch_ground_fly",
            "pitch_vsl_stuff",
            "pitch_vsl_movement",
            "pitch_vsl_control",
            "pitch_vsr_stuff",
            "pitch_vsr_movement",
            "pitch_vsr_control",
            "pitch_stamina",
        ]
        cols = [c for c in cols if c in players_df.columns]
        return team_df.merge(players_df[cols], on="player_key", how="left")

    @staticmethod
    def positional_bucket(row: pd.Series) -> str:
        if row["is_c"]:
            return "C"
        if row["is_ss"]:
            return "SS"
        if row["is_2b"]:
            return "2B"
        if row["is_3b"]:
            return "3B"
        if row["is_1b"]:
            return "1B"
        if row["is_cf"]:
            return "CF"
        if row["is_lf"] or row["is_rf"]:
            return "COF"
        return "DH"

    @classmethod
    def add_positional_bucket(cls, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df["pos_bucket"] = df.apply(cls.positional_bucket, axis=1)
        return df
