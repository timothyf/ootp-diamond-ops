#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PYTHON_BIN="$PROJECT_ROOT/.venv/bin/python"

if [[ ! -x "$PYTHON_BIN" ]]; then
  echo "Error: Python environment not found at $PYTHON_BIN" >&2
  echo "Create a virtual environment and install dependencies before running tests." >&2
  exit 1
fi

cd "$PROJECT_ROOT"
"$PYTHON_BIN" -m unittest discover -s tests -p 'test_*.py'
