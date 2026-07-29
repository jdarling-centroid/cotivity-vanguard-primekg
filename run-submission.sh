#!/usr/bin/env bash
#
# Build and validate a complete Cotiviti submission package.
#
# Normal usage:
#   ./run-submission.sh --track a --version 8
#
# Optional overrides:
#   --vendor-id ID
#   --source DIR
#   --out DIR

set -euo pipefail

track=""
version=""
vendor_id="centroid"
source_run=""
output_dir=""
passthrough=()
repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)

usage() {
  cat <<'EOF'
Usage: ./run-submission.sh --track a|b --version NUMBER [options]

Required:
  --track a|b       Submission track
  --version VALUE   Numeric submission version, or a safe label for test runs

Optional:
  --vendor-id ID    Vendor ID (default: centroid)
  --source DIR      Validated source run
  --out DIR         Output directory
  -h, --help        Show this help

Example:
  ./run-submission.sh --track a --version 8
  ./run-submission.sh --track a --version 8-q83-a --question 83
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
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
    --vendor-id)
      [[ $# -ge 2 ]] || { echo "--vendor-id requires a value" >&2; exit 64; }
      vendor_id=$2
      shift 2
      ;;
    --source)
      [[ $# -ge 2 ]] || { echo "--source requires a value" >&2; exit 64; }
      source_run=$2
      shift 2
      ;;
    --out)
      [[ $# -ge 2 ]] || { echo "--out requires a value" >&2; exit 64; }
      output_dir=$2
      shift 2
      ;;
    -h|--help)
      usage
      echo
      echo "Track A runner options passed through by this wrapper:"
      PYTHONPATH="$repo_root/src${PYTHONPATH:+:$PYTHONPATH}" \
        "$repo_root/.venv/bin/python3" \
        "$repo_root/scripts/run-primekg-questions.py" --help
      exit 0
      ;;
    *)
      passthrough+=("$1")
      shift
      ;;
  esac
done

if [[ "$track" != "a" && "$track" != "b" ]]; then
  echo "--track must be a or b" >&2
  exit 64
fi

if [[ ! "$version" =~ ^[A-Za-z0-9][A-Za-z0-9._-]*$ ]]; then
  echo "--version must contain only letters, numbers, dots, underscores, or hyphens" >&2
  exit 64
fi

if [[ ! "$vendor_id" =~ ^[a-z0-9][a-z0-9_-]*$ ]]; then
  echo "Invalid vendor ID: $vendor_id" >&2
  exit 64
fi

cd "$repo_root"

if [[ "$track" == "a" ]]; then
  if [[ ${#passthrough[@]} -gt 0 ]]; then
    output_dir=${output_dir:-.tmp/track-a-${version}}
    artifact_version=1
    if [[ "$version" =~ ^([1-9][0-9]*) ]]; then
      artifact_version=${BASH_REMATCH[1]}
    fi
    export PYTHONPATH="$repo_root/src${PYTHONPATH:+:$PYTHONPATH}"
    export VPK_RUN_LABEL="$version"
    exec "$repo_root/.venv/bin/python3" scripts/run-primekg-questions.py \
      --planner agent \
      --agent-provider oci \
      --model-id xai.grok-4.3 \
      --backend pgq \
      --vendor-id "$vendor_id" \
      --version "$artifact_version" \
      --out "$output_dir" \
      "${passthrough[@]}"
  fi
  if [[ ! "$version" =~ ^[1-9][0-9]*$ ]]; then
    echo "A full RFP submission requires a numeric --version; use a label with --question/--questions for test runs." >&2
    exit 64
  fi
  output_dir=${output_dir:-submission/track-a-v${version}}
  if [[ -z "$source_run" ]]; then
    source_run=".tmp/track-a-v${version}-measured-source"
    if [[ -e "$source_run" ]]; then
      echo "Refusing to overwrite existing measured source run: $source_run" >&2
      exit 73
    fi
    export PYTHONPATH="$repo_root/src${PYTHONPATH:+:$PYTHONPATH}"
    "$repo_root/.venv/bin/python3" scripts/run-primekg-questions.py \
      --planner agent \
      --agent-provider oci \
      --model-id xai.grok-4.3 \
      --backend pgq \
      --vendor-id "$vendor_id" \
      --version "$version" \
      --out "$source_run"
    "$repo_root/.venv/bin/python3" scripts/validate-track-a.py \
      "$source_run" --verify-db
  fi
  exec scripts/prepare-track-a-submission.sh \
    "$source_run" "$output_dir" "$vendor_id" "$version"
fi

echo "Track B packaging is not yet RFP-complete; refusing to create a package." >&2
exit 69
