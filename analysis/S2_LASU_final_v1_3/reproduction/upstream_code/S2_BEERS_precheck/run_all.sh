#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd -- "$SCRIPT_DIR/../../.." && pwd)"
TASK_PYTHON="${S2_BEERS_PYTHON:-$PROJECT_DIR/work/formal_v1_env/bin/python}"
export PYTHONDONTWRITEBYTECODE=1
"$TASK_PYTHON" "$SCRIPT_DIR/analyze_beers.py"
"$TASK_PYTHON" "$SCRIPT_DIR/audit_definitions.py"
"$TASK_PYTHON" "$SCRIPT_DIR/analyze_beers.py" --filter-low-generics
"$TASK_PYTHON" "$SCRIPT_DIR/literature_review.py"
"$TASK_PYTHON" "$SCRIPT_DIR/build_report.py"
"$TASK_PYTHON" "$SCRIPT_DIR/validate_bundle.py"
