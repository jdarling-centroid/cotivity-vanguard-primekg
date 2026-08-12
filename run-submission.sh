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
planner_fallback=true
track_b_shared_entity_fallback=true
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
  --deterministic-planner-fallback
                     Use deterministic classifier after agent retries (default)
  --no-deterministic-planner-fallback
                     Disable the fallback for comparison
  --deterministic-shared-entity-fallback
                     Enable Track B cross-document fallback (default)
  --no-deterministic-shared-entity-fallback
                     Disable Track B cross-document fallback for comparison
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
    --deterministic-planner-fallback)
      planner_fallback=true
      shift
      ;;
    --no-deterministic-planner-fallback)
      planner_fallback=false
      shift
      ;;
    --deterministic-shared-entity-fallback)
      track_b_shared_entity_fallback=true
      shift
      ;;
    --no-deterministic-shared-entity-fallback)
      track_b_shared_entity_fallback=false
      shift
      ;;
    -h|--help)
      usage
      echo
      if [[ "$track" == "b" ]]; then
        echo "Track B runner options passed through by this wrapper:"
        PYTHONPATH="$repo_root/src${PYTHONPATH:+:$PYTHONPATH}" \
          "$repo_root/.venv/bin/python3" \
          "$repo_root/scripts/run-track-b-questions.py" --help
      else
        echo "Track A runner options passed through by this wrapper:"
        PYTHONPATH="$repo_root/src${PYTHONPATH:+:$PYTHONPATH}" \
          "$repo_root/.venv/bin/python3" \
          "$repo_root/scripts/run-primekg-questions.py" --help
      fi
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

fallback_argument="--deterministic-planner-fallback"
if [[ "$planner_fallback" == false ]]; then
  fallback_argument="--no-deterministic-planner-fallback"
fi

if [[ "$track" == "a" ]]; then
  if [[ ! "$version" =~ ^[1-9][0-9]*$ ]]; then
    echo "A full RFP submission requires a numeric --version." >&2
    exit 64
  fi
  output_dir=${output_dir:-submission/track-a-v${version}}
  export PYTHONPATH="$repo_root/src${PYTHONPATH:+:$PYTHONPATH}"
  if [[ ! -e "$output_dir" ]]; then
    "$repo_root/.venv/bin/python3" scripts/run-primekg-questions.py \
      --planner agent \
      --agent-provider oci \
      --model-id xai.grok-4.3 \
      --temperature 0 \
      "$fallback_argument" \
      --backend pgq \
      --vendor-id "$vendor_id" \
      --version "$version" \
      --out "$output_dir" \
      "${passthrough[@]+"${passthrough[@]}"}"
    if [[ ${#passthrough[@]} -gt 0 ]]; then
      exit 0
    fi
    "$repo_root/.venv/bin/python3" scripts/validate-track-a.py \
      "$output_dir" --verify-db
  fi
  exec scripts/prepare-track-a-submission.sh \
    "$output_dir" "$output_dir" "$vendor_id" "$version"
fi

if [[ -n "$source_run" ]]; then
  echo "--source is not supported for Track B; Track B runs directly into --out" >&2
  exit 64
fi
if [[ ${#passthrough[@]} -eq 0 && ! "$version" =~ ^[1-9][0-9]*$ ]]; then
  echo "A full Track B submission requires a numeric --version" >&2
  exit 64
fi
output_dir=${output_dir:-submission/track-b-v${version}}
artifact_version=1
if [[ "$version" =~ ^([1-9][0-9]*) ]]; then
  artifact_version=${BASH_REMATCH[1]}
fi
export PYTHONPATH="$repo_root/src${PYTHONPATH:+:$PYTHONPATH}"
track_b_fallback_arguments=()
if [[ "$track_b_shared_entity_fallback" == true ]]; then
  track_b_fallback_arguments+=("--deterministic-shared-entity-fallback")
fi
if [[ ${#passthrough[@]} -gt 0 ]]; then
  "$repo_root/.venv/bin/python3" scripts/run-track-b-questions.py \
    --vendor-id "$vendor_id" \
    --version "$artifact_version" \
    --out "$output_dir" \
    "${track_b_fallback_arguments[@]}" \
    "${passthrough[@]}"
else
  "$repo_root/.venv/bin/python3" scripts/run-track-b-questions.py \
    --vendor-id "$vendor_id" \
    --version "$artifact_version" \
    --out "$output_dir" \
    "${track_b_fallback_arguments[@]}"
fi

validation_args=()
if [[ ${#passthrough[@]} -gt 0 ]]; then
  validation_args+=("--allow-partial")
else
  "$repo_root/.venv/bin/python3" scripts/build-track-b-graph.py \
    --vendor-id "$vendor_id" \
    --version "$artifact_version" \
    --out "$output_dir"
  "$repo_root/.venv/bin/python3" scripts/prepare-track-b-submission.py \
    "$output_dir" \
    --vendor-id "$vendor_id" \
    --version "$artifact_version"
fi
if [[ ${#validation_args[@]} -gt 0 ]]; then
  "$repo_root/.venv/bin/python3" scripts/validate-track-b.py \
    "$output_dir" "${validation_args[@]}"
else
  "$repo_root/.venv/bin/python3" scripts/validate-track-b.py "$output_dir"
fi

echo
echo "Track B artifacts and reviews created:"
echo "  $output_dir"
echo "Report:"
echo "  ./run-report.sh --path $output_dir"
