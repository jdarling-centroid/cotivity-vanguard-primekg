#!/usr/bin/env bash

set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
run_path=""
track=""
version=""
input_cost="1.25"
output_cost="2.50"

usage() {
  cat <<'EOF'
Usage:
  ./run-report.sh --path DIRECTORY [options]
  ./run-report.sh --track a|b --version VALUE [options]

Required:
  --path DIRECTORY  Track A or Track B run/submission directory
  or:
  --track a|b       Submission track
  --version VALUE   Submission version or test-run label

Optional:
  --input-cost-per-million USD
                     Input-token cost per million (default: 1.25)
  --output-cost-per-million USD
                     Output-token cost per million (default: 2.50)
  -h, --help        Show this help

Example:
  ./run-report.sh --track b --version 9
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
    --track)
      [[ $# -ge 2 ]] || { echo "--track requires a value" >&2; exit 64; }
      track=$(printf '%s' "$2" | tr '[:upper:]' '[:lower:]')
      shift 2
      ;;
    --version)
      [[ $# -ge 2 ]] || { echo "--version requires a value" >&2; exit 64; }
      version=$2
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

if [[ -n "$run_path" && ( -n "$track" || -n "$version" ) ]]; then
  echo "use either --path or --track with --version, not both" >&2
  exit 64
fi

if [[ -z "$run_path" ]]; then
  if [[ "$track" != "a" && "$track" != "b" ]]; then
    echo "--track must be a or b" >&2
    usage >&2
    exit 64
  fi
  if [[ ! "$version" =~ ^[A-Za-z0-9][A-Za-z0-9._-]*$ ]]; then
    echo "--version must contain only letters, numbers, dots, underscores, or hyphens" >&2
    usage >&2
    exit 64
  fi
  run_path="submission/track-${track}-v${version}"
fi

if [[ -z "$run_path" ]]; then
  echo "provide --path or --track with --version" >&2
  usage >&2
  exit 64
fi

arguments=("$repo_root/scripts/run-report.py" "$run_path")
arguments+=("--input-cost-per-million" "$input_cost")
arguments+=("--output-cost-per-million" "$output_cost")

export PYTHONPATH="$repo_root/src${PYTHONPATH:+:$PYTHONPATH}"
exec "$repo_root/.venv/bin/python3" "${arguments[@]}"
