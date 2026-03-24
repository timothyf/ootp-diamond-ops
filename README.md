# OOTP DiamondOps

OOTP DiamondOps generates a baseball operations dashboard for an MLB club and its AAA affiliate using OOTP export data. It produces lineup and pitching recommendations, promotion candidates, and transaction guidance in both CSV and HTML formats.

## What It Produces

From one run, DiamondOps generates:

- MLB hitter and pitcher value boards
- AAA hitter and pitcher promotion boards
- Recommended lineup vs RHP and vs LHP
- Recommended 5-man rotation
- Recommended bullpen roles
- Platoon diagnostics for corner-position optimization
- Recommended transactions based on promotion pressure and replacement targets
- Consolidated Markdown report for quick GM review

Outputs are written to the `output/` directory.

## Key Features

- Dual data sources:
	- CSV mode: reads OOTP-style CSV exports from `src/data/`
	- DB mode: reads from a MySQL schema generated from OOTP SQL exports
- Team-aware DB queries:
	- Supports custom MLB and AAA team names
	- Includes startup smoke-check for required DB tables
- Repeatable import pipeline:
	- `scripts/import_mysql.sh` recreates and imports a target database
	- Applies foreign keys from `sql/foreign_keys.mysql.sql` at the end
	- Repairs missing parent primary keys before FK import for compatibility with regenerated OOTP exports

## Project Layout

- `scripts/generate.py`: Main dashboard generator CLI
- `scripts/import_mysql.sh`: MySQL import helper for OOTP SQL dumps
- `src/`: Scoring, lineup planning, transaction logic, and report generation
- `src/data/`: CSV input files for CSV mode
- `sql/`: OOTP SQL export files used by the importer
- `output/`: Generated CSV, HTML, and Markdown reports

## Requirements

- Python 3.10+
- MySQL client (`mysql`) for database import workflow
- Python packages:

```bash
pip install pandas numpy sqlalchemy pymysql tabulate
```

## Usage

### 1. Generate dashboard from CSV files

This is the simplest path and uses files under `src/data/`.

```bash
python scripts/generate.py --source csv
```

### 2. Generate dashboard from MySQL

Pass a SQLAlchemy MySQL URL directly:

```bash
python scripts/generate.py \
	--source db \
	--db-url 'mysql+pymysql://root:YOUR_PASSWORD@127.0.0.1:3306/ootp_db'
```

Or use an environment variable:

```bash
export OOTP_DB_URL='mysql+pymysql://root:YOUR_PASSWORD@127.0.0.1:3306/ootp_db'
python scripts/generate.py
```

### 3. Use custom team names in DB mode

Team names must match the full team name in the database (for example: `Detroit Tigers`, `Toledo Mud Hens`).

```bash
python scripts/generate.py \
	--source db \
	--db-url 'mysql+pymysql://root:YOUR_PASSWORD@127.0.0.1:3306/ootp_db' \
	--mlb-team 'Detroit Tigers' \
	--aaa-team 'Toledo Mud Hens'
```

## MySQL Import Workflow

If you export OOTP SQL files into `sql/`, import them with:

```bash
./scripts/import_mysql.sh ootp_db -u root -p
```

Importer behavior:

- Drops and recreates the target database
- Imports tables in dependency-aware order
- Enforces foreign-key centralization outside of `sql/foreign_keys.mysql.sql`
- Adds missing parent primary keys when needed before FK import
- Applies FKs from `sql/foreign_keys.mysql.sql` at the final step

## Source Selection Rules

`scripts/generate.py` resolves data source as follows:

1. Explicit `--source` flag
2. If `--source` is omitted, DB mode is used when `OOTP_DB_URL` is set
3. Otherwise CSV mode is used

## Typical Outputs

You should expect files similar to:

- `output/dashboard.html`
- `output/ootp_gm_dashboard.md`
- `output/recommended_lineup_vs_rhp.csv`
- `output/recommended_lineup_vs_lhp.csv`
- `output/recommended_rotation.csv`
- `output/recommended_bullpen_roles.csv`
- `output/recommended_transactions.csv`
- Team-specific dashboard files for MLB and AAA hitters/pitchers in CSV and HTML

## Troubleshooting

- DB smoke-check fails:
	- Confirm `--db-url` or `OOTP_DB_URL` is correct
	- Confirm required tables exist after import
- Team lookup returns no data:
	- Use full team names exactly as stored in `teams` (`name + nickname`)
- FK import errors during SQL load:
	- Re-run `scripts/import_mysql.sh`; it includes automatic key repair before FK application

## Quick Start (DB)

```bash
./scripts/import_mysql.sh ootp_db -u root -p
python scripts/generate.py --source db --db-url 'mysql+pymysql://root:YOUR_PASSWORD@127.0.0.1:3306/ootp_db'
```
