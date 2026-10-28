#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd -- "$SCRIPT_DIR/../../.." && pwd)"
TASK_PYTHON="${S2_BEERS_PYTHON:-$PROJECT_DIR/work/formal_v1_env/bin/python}"
export PYTHONDONTWRITEBYTECODE=1
"$TASK_PYTHON" "$SCRIPT_DIR/analyze_benchmark.py" "$@"
"$TASK_PYTHON" "$SCRIPT_DIR/correct_name_collision.py"
"$TASK_PYTHON" "$SCRIPT_DIR/update_literature.py"
"$TASK_PYTHON" "$SCRIPT_DIR/validate_and_report.py"
