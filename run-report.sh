#!/usr/bin/env bash

set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
run_path=""
input_cost="1.25"
output_cost="2.50"

usage() {
  cat <<'EOF'
Usage: ./run-report.sh --path DIRECTORY [options]

Required:
  --path DIRECTORY  Track A or Track B run/submission directory

Optional:
  --input-cost-per-million USD
                     Input-token cost per million (default: 1.25)
  --output-cost-per-million USD
                     Output-token cost per million (default: 2.50)
  -h, --help        Show this help

Example:
  ./run-report.sh --path submission/track-a-v9-test-1
  ./run-report.sh --path submission/track-a-v9-test-1 \
    --input-cost-per-million 1.25 --output-cost-per-million 2.50
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --path)
      [[ $# -ge 2 ]] || { echo "--path requires a value" >&2; exit 64; }
      run_path=$2
      shift 2
      ;;
    --input-cost-per-million)
      [[ $# -ge 2 ]] || { echo "--input-cost-per-million requires a value" >&2; exit 64; }
      input_cost=$2
      shift 2
      ;;
    --output-cost-per-million)
      [[ $# -ge 2 ]] || { echo "--output-cost-per-million requires a value" >&2; exit 64; }
      output_cost=$2
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "unknown argument: $1" >&2
      usage >&2
      exit 64
      ;;
  esac
done

if [[ -z "$run_path" ]]; then
  echo "--path is required" >&2
  usage >&2
  exit 64
fi

arguments=("$repo_root/scripts/run-report.py" "$run_path")
arguments+=("--input-cost-per-million" "$input_cost")
arguments+=("--output-cost-per-million" "$output_cost")

export PYTHONPATH="$repo_root/src${PYTHONPATH:+:$PYTHONPATH}"
exec "$repo_root/.venv/bin/python3" "${arguments[@]}"
