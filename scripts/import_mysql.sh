#!/usr/bin/env bash

set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  ./scripts/import_mysql.sh <database_name> [mysql options...]

Examples:
  ./scripts/import_mysql.sh ootp
  ./scripts/import_mysql.sh ootp -u root -p
  ./scripts/import_mysql.sh ootp --host 127.0.0.1 --port 3306 -u root -p

Notes:
  - The first argument is the target database name.
  - Any additional arguments are passed directly to the `mysql` CLI.
  - Passwords are passed via a temporary MySQL defaults file to avoid CLI password warnings.
  - If the target database already exists, it is dropped and recreated.
  - Tables are imported in dependency-aware order.
  - Foreign keys are applied at the very end from `sql/foreign_keys.mysql.sql`.
EOF
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" || $# -lt 1 ]]; then
  usage
  exit 0
fi

if ! command -v mysql >/dev/null 2>&1; then
  echo "Error: mysql client not found in PATH." >&2
  exit 1
fi

DB_NAME="$1"
shift

if [[ ! "$DB_NAME" =~ ^[A-Za-z0-9_]+$ ]]; then
  echo "Error: database name '$DB_NAME' is invalid. Use only letters, numbers, and underscores." >&2
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
MYSQL_DIR="$PROJECT_ROOT/sql"

if [[ ! -d "$MYSQL_DIR" ]]; then
  echo "Error: sql directory not found at $MYSQL_DIR" >&2
  exit 1
fi

MYSQL_ARGS=("$@")

PASSWORD_VALUE=""
NORMALIZED_MYSQL_ARGS=()

for ((i = 0; i < ${#MYSQL_ARGS[@]}; i++)); do
  arg="${MYSQL_ARGS[$i]}"

  case "$arg" in
    -p)
      read -r -s -p "Enter MySQL password: " PASSWORD_VALUE
      echo
      ;;
    --password)
      read -r -s -p "Enter MySQL password: " PASSWORD_VALUE
      echo
      ;;
    -p*)
      PASSWORD_VALUE="${arg:2}"
      ;;
    --password=*)
      PASSWORD_VALUE="${arg#--password=}"
      ;;
    *)
      NORMALIZED_MYSQL_ARGS+=("$arg")
      ;;
  esac
done

MYSQL_CREDENTIALS_FILE=""
MYSQL_CMD=(mysql)

if [[ -n "$PASSWORD_VALUE" ]]; then
  MYSQL_CREDENTIALS_FILE="$(mktemp)"
  chmod 600 "$MYSQL_CREDENTIALS_FILE"
  cat > "$MYSQL_CREDENTIALS_FILE" <<EOF
[client]
password=$PASSWORD_VALUE
EOF
  trap 'rm -f "$MYSQL_CREDENTIALS_FILE"' EXIT
  MYSQL_CMD+=(--defaults-extra-file="$MYSQL_CREDENTIALS_FILE")
fi

MYSQL_CMD+=("${NORMALIZED_MYSQL_ARGS[@]}")

SQL_FILES=(
  "languages.mysql.sql"
  "continents.mysql.sql"
  "nations.mysql.sql"
  "states.mysql.sql"
  "cities.mysql.sql"
  "parks.mysql.sql"
  "human_managers.mysql.sql"
  "leagues.mysql.sql"
  "sub_leagues.mysql.sql"
  "divisions.mysql.sql"
  "players.mysql.sql"
  "coaches.mysql.sql"
  "teams.mysql.sql"
  "games.mysql.sql"
  "games_score.mysql.sql"
  "messages.mysql.sql"
  "trade_history.mysql.sql"
  "team_roster.mysql.sql"
  "team_roster_staff.mysql.sql"
  "team_affiliations.mysql.sql"
  "team_relations.mysql.sql"
  "team_financials.mysql.sql"
  "team_last_financials.mysql.sql"
  "team_record.mysql.sql"
  "team_history.mysql.sql"
  "team_history_record.mysql.sql"
  "team_history_batting_stats.mysql.sql"
  "team_history_pitching_stats.mysql.sql"
  "team_history_fielding_stats_stats.mysql.sql"
  "team_history_financials.mysql.sql"
  "team_batting_stats.mysql.sql"
  "team_pitching_stats.mysql.sql"
  "team_starting_pitching_stats.mysql.sql"
  "team_bullpen_pitching_stats.mysql.sql"
  "team_fielding_stats_stats.mysql.sql"
  "human_manager_history.mysql.sql"
  "human_manager_history_record.mysql.sql"
  "human_manager_history_batting_stats.mysql.sql"
  "human_manager_history_pitching_stats.mysql.sql"
  "human_manager_history_fielding_stats_stats.mysql.sql"
  "human_manager_history_financials.mysql.sql"
  "league_events.mysql.sql"
  "league_playoffs.mysql.sql"
  "league_playoff_fixtures.mysql.sql"
  "league_history.mysql.sql"
  "league_history_all_star.mysql.sql"
  "league_history_batting_stats.mysql.sql"
  "league_history_pitching_stats.mysql.sql"
  "league_history_fielding_stats.mysql.sql"
  "players_batting.mysql.sql"
  "players_pitching.mysql.sql"
  "players_fielding.mysql.sql"
  "players_value.mysql.sql"
  "players_contract.mysql.sql"
  "players_contract_extension.mysql.sql"
  "players_salary_history.mysql.sql"
  "players_awards.mysql.sql"
  "players_league_leader.mysql.sql"
  "players_streak.mysql.sql"
  "players_injury_history.mysql.sql"
  "players_roster_status.mysql.sql"
  "projected_starting_pitchers.mysql.sql"
  "players_game_batting.mysql.sql"
  "players_game_pitching_stats.mysql.sql"
  "players_at_bat_batting_stats.mysql.sql"
  "players_individual_batting_stats.mysql.sql"
  "players_career_batting_stats.mysql.sql"
  "players_career_pitching_stats.mysql.sql"
  "players_career_fielding_stats.mysql.sql"
  "language_data.mysql.sql"
  "foreign_keys.mysql.sql"
)

# Enforce FK centralization: only foreign_keys.mysql.sql may define FK constraints.
FK_CENTRAL_FILE="foreign_keys.mysql.sql"
for file in "${SQL_FILES[@]}"; do
  [[ "$file" == "$FK_CENTRAL_FILE" ]] && continue
  if grep -Eiq '(^|[[:space:],(])FOREIGN[[:space:]]+KEY([[:space:],)`(]|$)|CONSTRAINT[[:space:]]+`[^`]+`[[:space:]]+FOREIGN[[:space:]]+KEY' "$MYSQL_DIR/$file"; then
    echo "Error: foreign key definition found in $file. Move all FK constraints to $FK_CENTRAL_FILE." >&2
    exit 1
  fi
done

for file in "${SQL_FILES[@]}"; do
  if [[ ! -f "$MYSQL_DIR/$file" ]]; then
    echo "Error: expected SQL file not found: $MYSQL_DIR/$file" >&2
    exit 1
  fi
done

echo "Dropping database '$DB_NAME' if it already exists..."
"${MYSQL_CMD[@]}" -e "DROP DATABASE IF EXISTS \`$DB_NAME\`;"

echo "Creating database '$DB_NAME'..."
"${MYSQL_CMD[@]}" -e "CREATE DATABASE \`$DB_NAME\`;"

for file in "${SQL_FILES[@]}"; do
  echo "Importing $file"
  "${MYSQL_CMD[@]}" "$DB_NAME" < "$MYSQL_DIR/$file"
done

echo "Import completed successfully for database '$DB_NAME'."
