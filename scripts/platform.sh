#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export FCA_DOC_REPO="${FCA_DOC_REPO:-$HOME/fca-document-intelligence}"
PYTHON="${FCA_AGENT_PYTHON:-$HOME/fca-autonomous-research-agent/.venv/bin/python}"
if [[ ! -x "$PYTHON" ]]; then echo "Agent Python environment not found" >&2; exit 1; fi
case "${1:-}" in
  preflight|finance|documents)
    cmd="$1"; shift
    cd "$ROOT/components/autonomous-agent"
    exec "$PYTHON" -m agent.cli "$cmd" "$@"
    ;;
  usda-check)
    cd "$ROOT/components/usda-data-engineering"
    echo "USDA component directory: $PWD"
    test -f requirements.txt && echo "Requirements: found"
    test -f src/pipeline.py && echo "Spark pipeline: found"
    test -f analyze_usda.py && echo "Analysis script: found"
    ;;
  usda-test)
    shift
    cd "$ROOT/components/usda-data-engineering"
    exec "$ROOT/.venv-usda/bin/python" -m pytest -q "$@"
    ;;
  usda-analyze)
    shift
    cd "$ROOT/components/usda-data-engineering"
    exec "$ROOT/.venv-usda/bin/python" -m src.pipeline --source real --csv data/raw/usda_state_crop_clean.csv "$@"
    ;;
  *) echo "Usage: $0 {preflight|finance|documents|usda-check|usda-test|usda-analyze} [arguments]" >&2; exit 2 ;;
esac
