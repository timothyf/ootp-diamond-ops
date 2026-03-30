# OOTP DiamondOps

OOTP DiamondOps generates a baseball operations dashboard for an MLB club and its AAA affiliate from OOTP exports. It produces scored roster boards, planning pages, transaction guidance, and linked HTML reports for front-office review.

## Current Functionality

From one run, DiamondOps currently produces:

- A landing dashboard with grouped sections for:
  - `Decisions now`
  - `MLB snapshot`
  - `AAA watchlist`
- Team hub pages for the MLB and AAA clubs
- Merged hitter and pitcher tables with an in-page `Current` / `Stats` toggle
- MLB active depth chart
- Recommended lineups vs RHP and vs LHP
- Platoon diagnostics
- Recommended rotation
- Spot starter / replacement starter candidates
- Bullpen role recommendations
- Team needs / acquisition-priority report
- Recommended transactions
- Scoring breakdown page
- Player detail pages linked from report tables
- CSV outputs for the core report tables
- A consolidated Markdown report for quick review

HTML pages include a shared site shell with:

- A branded hero header
- OOTP date
- MLB and AAA team record, division position, and games back
- Team logos in the header status cards
- Shared top navigation across reports

Outputs are written to `output/`.

## Report Structure

The generated HTML site is organized around a few core entry points:

- `dashboard.html`
  - high-level landing page with the most actionable reports first
- MLB team hub
  - grouped into `Position players`, `Pitching`, and `Planning & decisions`
- AAA team hub
  - grouped into the same high-level areas for consistency
- Standalone report pages
  - full tables and descriptions for each recommendation or board

## Data Sources

DiamondOps supports two modes:

- CSV mode
  - reads OOTP-style CSV exports from `src/data/`
- MySQL mode
  - reads from a MySQL database populated from OOTP SQL exports

MySQL mode also supports:

- explicit MLB and AAA team-name overrides
- automatic team detection when overrides are omitted
- DB smoke checks before generation
- header standings lookup for the generated HTML site

## Project Layout

- `scripts/generate.py`
  - main CLI entry point
- `scripts/build.sh`
  - convenience script for local DB-backed generation
- `scripts/import_mysql.sh`
  - MySQL import helper for OOTP SQL dumps
- `scripts/test.sh`
  - runs the unit test suite from the project virtual environment
- `src/`
  - scoring, data processing, lineup planning, transaction logic, and HTML generation
- `src/data/`
  - CSV input files for CSV mode
- `src/images/`
  - shared site and team logo assets
- `sql/`
  - OOTP SQL export files used by the importer
- `output/`
  - generated CSV, HTML, and Markdown reports

## Requirements

- Python 3.10+
- MySQL client (`mysql`) for the import workflow
- Python packages:

```bash
pip install pandas numpy sqlalchemy pymysql tabulate
```

## Usage

### Generate from CSV files

This uses CSVs under `src/data/`.

```bash
python scripts/generate.py --source csv
```

### Generate from MySQL

Pass a SQLAlchemy MySQL URL directly:

```bash
python scripts/generate.py \
  --source db \
  --db-url 'mysql+pymysql://root:YOUR_PASSWORD@127.0.0.1:3306/ootp_db'
```

Or use environment variables:

```bash
export OOTP_DB_URL='mysql+pymysql://root:YOUR_PASSWORD@127.0.0.1:3306/ootp_db'
python scripts/generate.py
```

### Use custom team names in DB mode

Team names must match the full `name + nickname` stored in the database.

```bash
python scripts/generate.py \
  --source db \
  --db-url 'mysql+pymysql://root:YOUR_PASSWORD@127.0.0.1:3306/ootp_db' \
  --mlb-team 'Detroit Tigers' \
  --aaa-team 'Toledo Mud Hens'
```

### Use the local build helper

For the common local DB workflow:

```bash
./scripts/build.sh
```

## Testing

Run the full test suite:

```bash
./scripts/test.sh
```

Equivalent direct command:

```bash
./.venv/bin/python -m unittest discover -s tests -p 'test_*.py'
```

## MySQL Import Workflow

If you export OOTP SQL files into `sql/`, import them with:

```bash
./scripts/import_mysql.sh ootp_db -u root -p
```

Importer behavior:

- drops and recreates the target database
- imports tables in dependency-aware order
- repairs missing parent primary keys before foreign-key import when needed
- applies foreign keys from `sql/foreign_keys.mysql.sql` at the end

## Source Selection Rules

`scripts/generate.py` resolves the data source in this order:

1. explicit `--source`
2. if `--source` is omitted, DB mode is used when `OOTP_DB_URL` is set
3. otherwise CSV mode is used

## Typical Outputs

You should expect files similar to:

- `output/dashboard.html`
- `output/scoring_info.html`
- `output/team_needs.html`
- `output/recommended_lineup_vs_rhp.html`
- `output/recommended_lineup_vs_lhp.html`
- `output/recommended_rotation.html`
- `output/bullpen_roles.html`
- `output/recommended_transactions.html`
- `output/<mlb_team>_team.html`
- `output/<aaa_team>_team.html`
- `output/ootp_gm_dashboard.md`
- team-specific CSV dashboards for hitters and pitchers

## Troubleshooting

- DB smoke-check fails
  - confirm `--db-url` or `OOTP_DB_URL` is correct
  - confirm required tables exist after import
- Team lookup returns no data
  - use full team names exactly as stored in `teams`
- Standings or OOTP date are missing in the hero
  - confirm the DB includes `leagues` and `team_record` data
- FK import errors during SQL load
  - rerun `scripts/import_mysql.sh`; it includes automatic key repair before FK application

## Quick Start

### DB workflow

```bash
./scripts/import_mysql.sh ootp_db -u root -p
./scripts/build.sh
```

### CSV workflow

```bash
python scripts/generate.py --source csv
```
