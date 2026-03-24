from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.dashboard import DashboardGenerator
from src.data_processing import MySqlRepository


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="OOTP Diamond Ops — GM dashboard generator",
    )
    parser.add_argument(
        "--source",
        choices=["csv", "db"],
        default=None,
        help=(
            "Data source: 'csv' (default) reads local CSV files; "
            "'db' connects to a MySQL database. "
            "When omitted, falls back to the OOTP_DB_URL env var if set."
        ),
    )
    parser.add_argument(
        "--db-url",
        default=None,
        metavar="URL",
        help=(
            "SQLAlchemy connection URL for the OOTP MySQL database, e.g. "
            "'mysql+pymysql://user:pass@host:3306/ootp_db'. "
            "Required when --source db is given. "
            "Overrides the OOTP_DB_URL env var."
        ),
    )
    parser.add_argument(
        "--mlb-team",
        default=None,
        metavar="NAME",
        help="MLB team name as stored in the DB (default: 'Detroit Tigers'). Overrides OOTP_MLB_TEAM_NAME.",
    )
    parser.add_argument(
        "--aaa-team",
        default=None,
        metavar="NAME",
        help="AAA team name as stored in the DB (default: 'Toledo Mud Hens'). Overrides OOTP_AAA_TEAM_NAME.",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()

    # Resolve source: explicit flag > env var
    db_url = (
        args.db_url
        or os.getenv("OOTP_DB_URL", "").strip()
    )
    use_db = args.source == "db" or (args.source is None and bool(db_url))

    if args.source == "csv":
        use_db = False

    mlb_team_name = (
        args.mlb_team
        or os.getenv("OOTP_MLB_TEAM_NAME", "").strip()
        or "Detroit Tigers"
    )
    aaa_team_name = (
        args.aaa_team
        or os.getenv("OOTP_AAA_TEAM_NAME", "").strip()
        or "Toledo Mud Hens"
    )

    repository = None
    if use_db:
        if not db_url:
            print(
                "Error: --source db requires a DB URL. "
                "Pass --db-url URL or set OOTP_DB_URL.",
                file=sys.stderr,
            )
            sys.exit(1)
        repository = MySqlRepository(
            connection_url=db_url,
            mlb_team_name=mlb_team_name,
            aaa_team_name=aaa_team_name,
        )
        print(f"Data source: MySQL ({mlb_team_name} / {aaa_team_name})")
        print("Running DB smoke-check…", end=" ", flush=True)
        repository.smoke_check()
        print("OK")

    generator = DashboardGenerator(
        data_dir=SRC_DIR / "data",
        out_dir=PROJECT_ROOT / "output",
        repository=repository,
    )
    generator.run()
    print("Done. Full dashboard outputs generated.")
    print(f"Saved files to: {generator.out_dir.resolve()}")


if __name__ == "__main__":
    main()
