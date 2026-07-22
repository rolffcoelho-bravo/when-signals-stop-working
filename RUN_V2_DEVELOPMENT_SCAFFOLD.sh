#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"
PYTHON=".venv/bin/python"

if [[ ! -x "$PYTHON" ]]; then
  echo "Repository virtual environment not found: $PYTHON" >&2
  exit 1
fi

printf '\nTECHNICAL SIGNAL VALIDITY FRAMEWORK\n'
printf 'Version 2 Development Implementation Scaffold\n'
printf '=================================================\n\n'

"$PYTHON" scripts/verify_v2_protocol_lock.py
"$PYTHON" scripts/build_v2_development_assets.py
"$PYTHON" scripts/verify_v2_development_scaffold.py
"$PYTHON" -m pytest -q

printf '\nVERSION 2 DEVELOPMENT SCAFFOLD COMPLETED.\n'
printf 'Model fitting performed: False\n'
printf 'Holdout performance accessed: False\n'
