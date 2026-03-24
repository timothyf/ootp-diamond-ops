from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd


class CsvRepository:
    def __init__(self, data_dir: Path) -> None:
        self.data_dir = data_dir

    def load(self, name: str) -> pd.DataFrame:
        return pd.read_csv(self.data_dir / name, low_memory=False)


class MySqlRepository:
    """Load dashboard input frames from a MySQL database.

    This class provides a minimal query layer that returns the same logical
    datasets currently expected from CSV files in the dashboard flow.
    """

    def __init__(
            self,
            connection_url: str,
            mlb_team_name: str = "Detroit Tigers",
            aaa_team_name: str = "Toledo Mud Hens",
    ) -> None:
            self.connection_url = connection_url
            self.mlb_team_name = mlb_team_name
            self.aaa_team_name = aaa_team_name

            try:
                    from sqlalchemy import create_engine
            except ImportError as exc:
                    raise ImportError(
                            "MySqlRepository requires SQLAlchemy. Install with: pip install sqlalchemy pymysql"
                    ) from exc

            self._engine = create_engine(connection_url)
            self._query_map = {
                    "tigers_roster.csv": lambda: self._build_roster(self.mlb_team_name),
                    "toledo_roster.csv": lambda: self._build_roster(self.aaa_team_name),
                    "tigers_batting.csv": lambda: self._build_batting(self.mlb_team_name),
                    "toledo_batting.csv": lambda: self._build_batting(self.aaa_team_name),
                    "tigers_pitching.csv": lambda: self._build_pitching(self.mlb_team_name),
                    "toledo_pitching.csv": lambda: self._build_pitching(self.aaa_team_name),
                    "player_ratings.csv": self._build_player_ratings,
            }

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

    def load(self, name: str) -> pd.DataFrame:
            builder = self._query_map.get(name)
            if builder is None:
                    raise ValueError(f"Unsupported dataset '{name}' for MySqlRepository")
            return builder()

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
                SUM(COALESCE(pgb.cs, 0)) AS CS
            FROM players_game_batting pgb
            JOIN latest l ON pgb.year = l.year_val
            JOIN players p ON p.player_id = pgb.player_id
            JOIN teams t ON t.team_id = pgb.team_id
            LEFT JOIN war w ON w.player_id = pgb.player_id
            WHERE CONCAT(t.name, ' ', t.nickname) = :team_name
            GROUP BY p.player_id, p.uniform_number, p.first_name, p.last_name, p.position, p.bats, p.throws, w.war_total
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
                ROUND(SUM(COALESCE(pgp.ip, 0)), 1) AS IP,
                SUM(COALESCE(pgp.ha, 0)) AS HA,
                SUM(COALESCE(pgp.hra, 0)) AS HR,
                SUM(COALESCE(pgp.r, 0)) AS R,
                SUM(COALESCE(pgp.er, 0)) AS ER,
                SUM(COALESCE(pgp.bb, 0)) AS BB,
                SUM(COALESCE(pgp.k, 0)) AS K,
                SUM(COALESCE(pgp.hp, 0)) AS HP,
                SUM(COALESCE(pgp.gb, 0)) AS GB,
                SUM(COALESCE(pgp.fb, 0)) AS FB,
                ROUND(9 * SUM(COALESCE(pgp.er, 0)) / NULLIF(SUM(COALESCE(pgp.ip, 0)), 0), 2) AS ERA,
                ROUND(SUM(COALESCE(pgp.ha, 0)) / NULLIF(SUM(COALESCE(pgp.ab, 0)), 0), 3) AS AVG,
                ROUND((SUM(COALESCE(pgp.ha, 0)) - SUM(COALESCE(pgp.hra, 0))) / NULLIF(SUM(COALESCE(pgp.ab, 0)) - SUM(COALESCE(pgp.k, 0)) - SUM(COALESCE(pgp.hra, 0)), 0), 3) AS BABIP,
                ROUND((SUM(COALESCE(pgp.ha, 0)) + SUM(COALESCE(pgp.bb, 0))) / NULLIF(SUM(COALESCE(pgp.ip, 0)), 0), 2) AS WHIP,
                ROUND(9 * SUM(COALESCE(pgp.hra, 0)) / NULLIF(SUM(COALESCE(pgp.ip, 0)), 0), 1) AS `HR/9`,
                ROUND(9 * SUM(COALESCE(pgp.bb, 0)) / NULLIF(SUM(COALESCE(pgp.ip, 0)), 0), 1) AS `BB/9`,
                ROUND(9 * SUM(COALESCE(pgp.k, 0)) / NULLIF(SUM(COALESCE(pgp.ip, 0)), 0), 1) AS `K/9`,
                ROUND(SUM(COALESCE(pgp.k, 0)) / NULLIF(SUM(COALESCE(pgp.bb, 0)), 0), 1) AS `K/BB`,
                100 AS `ERA+`,
                ROUND(
                    ((13 * SUM(COALESCE(pgp.hra, 0))) + (3 * SUM(COALESCE(pgp.bb, 0))) - (2 * SUM(COALESCE(pgp.k, 0))))
                    / NULLIF(SUM(COALESCE(pgp.ip, 0)), 0)
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
