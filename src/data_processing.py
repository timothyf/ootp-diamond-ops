from __future__ import annotations

from pathlib import Path

import pandas as pd


class CsvRepository:
    def __init__(self, data_dir: Path) -> None:
        self.data_dir = data_dir

    def load(self, name: str) -> pd.DataFrame:
        return pd.read_csv(self.data_dir / name, low_memory=False)


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
