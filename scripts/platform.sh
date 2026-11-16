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
  research)
    shift
    if [[ "${FCA_ENABLE_DATABRICKS:-0}" != "1" ]]; then
      echo "Set FCA_ENABLE_DATABRICKS=1 to run validated Databricks research." >&2
      exit 2
    fi
    cd "$ROOT/components/autonomous-agent"
    exec "$PYTHON" scripts/run_validated_databricks_agent.py "$@"
    ;;
  combined-report)
    shift
    exec python3 "$ROOT/scripts/combined_report.py" "$@"
    ;;
  forecast)
    shift
    cd "$ROOT"
    exec "$ROOT/.venv-usda/bin/python" forecasting/corn_yield_forecast.py "$@"
    ;;
  *) echo "Usage: $0 {preflight|finance|documents|usda-check|usda-test|usda-analyze|research|combined-report|forecast} [arguments]" >&2; exit 2 ;;
esac
