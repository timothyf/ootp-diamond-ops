#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PYTHON_BIN="$PROJECT_ROOT/.venv/bin/python"

cd "$PROJECT_ROOT"
if [[ -x "$PYTHON_BIN" ]]; then
  "$PYTHON_BIN" scripts/generate.py --source db --db-url 'mysql+pymysql://root:@127.0.0.1:3306/ootp_db'
else
  python scripts/generate.py --source db --db-url 'mysql+pymysql://root:@127.0.0.1:3306/ootp_db'
fi
