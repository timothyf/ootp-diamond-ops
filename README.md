# OOTP DiamondOps

<img src="src/images/diamondops-logo.png" alt="DiamondOps logo" width="220">

OOTP DiamondOps generates a baseball operations site for an MLB club and its AAA affiliate from OOTP exports. It combines current performance, OOTP ratings, roster status, and organizational depth into linked HTML reports, CSV tables, and a Markdown summary for front-office review.

<p align="center">
  <img src="docs/images/ootp-diamond-ops_dashboard.png" alt="Dashboard screenshot" width="48%">
  <img src="docs/images/ootp-diamond-ops_detroit_team.png" alt="Team page screenshot" width="48%">
</p>
<p align="center">
  <em>Dashboard overview and team hub pages.</em>
</p>

## What It Produces

One run currently generates:

- A status-oriented `dashboard.html` landing page
- MLB and AAA team hub pages
- Merged hitter and pitcher boards with in-page `Current` / `Stats` toggles
- MLB active depth chart
- `Recommended lineup vs RHP`
- `Recommended lineup vs LHP`
- `Platoon diagnostics`
- `Recommended rotation`
- `Spot Starter / Replacement Candidates` on the rotation page
- `Bullpen roles`
- `Team needs`
- `Recommended transactions`, grouped by move type
- `Scoring Breakdown`
- Linked player detail pages
- Team dashboard CSVs
- A consolidated Markdown report

When a season has been completed, DiamondOps also generates:

- `season_summary.html`

That season summary page stays visible during the following offseason and disappears once the new season has started.

All generated outputs are written to `output/`.

## Current Site Structure

### Dashboard

The landing dashboard is now a quick status board rather than a set of page summaries. It is designed to answer “how is the organization doing right now?” at a glance.

It currently includes:

- Organization status cards:
  - high-priority needs
  - MLB injuries
  - call-up pressure
  - outside-help pressure
  - AAA watchlist size
- MLB leader tables:
  - top MLB hitters
  - top MLB pitchers
- Pressure-point tables:
  - current needs
  - current injured MLB players
- AAA watch tables:
  - top AAA hitters
  - top AAA pitchers

### Team Hubs

Both the MLB and AAA team pages are organized consistently into:

- `Position players`
- `Pitching`
- `Planning & decisions`

These hub pages act as the main navigation layer into the full report set.

### Shared HTML Shell

All HTML pages share a common site shell with:

- a branded hero/header
- DiamondOps logo
- OOTP date
- MLB and AAA records, division position, and GB
- MLB and AAA team logos in the header
- shared top navigation
- consistent page width across reports

## Key Reports

### Hitter and Pitcher Boards

The MLB and AAA hitter/pitcher pages use merged tables with a `Current` / `Stats` toggle instead of separate pages.

- `Current` emphasizes current-value columns and roster context
- `Stats` emphasizes raw statistical production
- column formatting includes baseball-specific cleanup such as MLB-style innings pitched notation

### Team Needs

The `Team needs` page identifies likely acquisition targets by analyzing:

- current MLB quality
- AAA cover
- age risk
- handedness balance
- bullpen/rotation depth

It is intended to answer where the organization most needs outside help.

### Recommended Transactions

The transactions page is no longer limited to call-ups. It can now recommend:

- `CALL UP`
- `SEND DOWN`
- `DFA / BENCH`
- `ACQUIRE`

The page renders separate tables by transaction family so it is easier to scan.

### Recommended Lineups

Both lineup pages use the same selection pipeline:

- lock in the best healthy regulars at premium defensive spots
- optimize `1B`, `LF`, `RF`, and `DH` for the opposing pitcher handedness
- set batting order from role-based lineup scores

### Rotation and Bullpen

Pitching planning pages include:

- recommended MLB rotation
- spot-starter / replacement-starter candidates
- bullpen role recommendations

### Scoring Breakdown

The scoring page explains how hitter and pitcher scores are built from:

- stats
- ratings
- smaller context bonuses

It includes both formula-share and empirical-share views.

### Season Summary

When historical season data is available for both clubs, the season summary page shows:

- season year
- MLB and AAA final records
- division finish
- games back
- postseason result
- best hitter
- best pitcher
- best rookie

## Data Sources

DiamondOps supports two input modes.

### CSV mode

- reads OOTP-style CSV exports from `src/data/`
- does not provide in-game OOTP date or standings header data

### MySQL mode

- reads from a MySQL database populated from OOTP SQL exports
- supports automatic MLB/AAA team detection
- supports explicit team-name overrides
- runs a DB smoke-check before generation
- populates header standings and OOTP date
- enables completed-season detection for the season summary page

## Project Layout

- `scripts/generate.py`
  - main CLI entry point
- `scripts/build.sh`
  - convenience wrapper for the common local build flow
- `scripts/import_mysql.sh`
  - imports OOTP SQL dumps into MySQL
- `scripts/test.sh`
  - runs the project test suite
- `src/`
  - scoring, data processing, report building, transactions, and HTML generation
- `src/data/`
  - CSV inputs for CSV mode
- `src/images/`
  - DiamondOps and team logo assets
- `sql/`
  - SQL import assets
- `output/`
  - generated HTML, CSV, and Markdown outputs

## Requirements

- Python 3.10+
- MySQL client tools for the SQL import workflow
- Python packages:

```bash
pip install pandas numpy sqlalchemy pymysql tabulate
```

## Usage

### Generate from CSV files

```bash
python scripts/generate.py --source csv
```

### Generate from MySQL

Direct URL:

```bash
python scripts/generate.py \
  --source db \
  --db-url 'mysql+pymysql://root:YOUR_PASSWORD@127.0.0.1:3306/ootp_db'
```

Or environment variable:

```bash
export OOTP_DB_URL='mysql+pymysql://root:YOUR_PASSWORD@127.0.0.1:3306/ootp_db'
python scripts/generate.py
```

### Generate with explicit team names

Team names must match the full `name + nickname` stored in OOTP.

```bash
python scripts/generate.py \
  --source db \
  --db-url 'mysql+pymysql://root:YOUR_PASSWORD@127.0.0.1:3306/ootp_db' \
  --mlb-team 'Detroit Tigers' \
  --aaa-team 'Toledo Mud Hens'
```

### Use the local build helper

```bash
./scripts/build.sh
```

## Testing

Run the full suite:

```bash
./scripts/test.sh
```

Equivalent direct command:

```bash
./.venv/bin/python -m unittest discover -s tests -p 'test_*.py'
```

## MySQL Import Workflow

Import OOTP SQL files from `sql/` with:

```bash
./scripts/import_mysql.sh ootp_db -u root -p
```

Importer behavior:

- drops and recreates the target database
- imports tables in dependency-aware order
- repairs missing parent primary keys before applying foreign keys when needed
- applies foreign keys from `sql/foreign_keys.mysql.sql` at the end

## Source Selection Rules

`scripts/generate.py` chooses the source in this order:

1. explicit `--source`
2. DB mode when `OOTP_DB_URL` is set
3. otherwise CSV mode

## Typical Outputs

Typical generated files include:

- `output/dashboard.html`
- `output/<mlb_team>_team.html`
- `output/<aaa_team>_team.html`
- `output/team_needs.html`
- `output/recommended_lineup_vs_rhp.html`
- `output/recommended_lineup_vs_lhp.html`
- `output/platoon_diagnostics.html`
- `output/recommended_rotation.html`
- `output/bullpen_roles.html`
- `output/recommended_transactions.html`
- `output/scoring_info.html`
- `output/season_summary.html` when applicable
- `output/ootp_gm_dashboard.md`
- team-specific hitter and pitcher dashboard CSVs

## Troubleshooting

- DB smoke-check fails
  - confirm `--db-url` or `OOTP_DB_URL`
  - confirm required tables imported successfully
- Team lookup returns no data
  - use full OOTP `name + nickname` values
- OOTP date or standings are missing in the header
  - confirm the DB includes `leagues` and `team_record`
- Season summary does not appear
  - confirm `team_history` and `team_history_record` are populated for both clubs
  - confirm the build is either at completed season end or in the following offseason before games begin
- FK import errors during SQL load
  - rerun `scripts/import_mysql.sh`

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
