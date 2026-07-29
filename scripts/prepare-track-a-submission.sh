#!/usr/bin/env bash
#
# Build a complete RFP-ready Track A submission and fail unless both the
# database-provenance validator and literal RFP package validator pass with
# zero errors and zero warnings.
#
# Usage:
#   scripts/prepare-track-a-submission.sh SOURCE_RUN TARGET_DIR VENDOR_ID VERSION
#
# Example:
#   scripts/prepare-track-a-submission.sh \
#     submission/track-a-v1 submission/track-a-v7-ready centroid 7

set -euo pipefail

if [[ $# -ne 4 ]]; then
  echo "Usage: $0 SOURCE_RUN TARGET_DIR VENDOR_ID VERSION" >&2
  exit 64
fi

source_run=$1
target_dir=$2
vendor_id=$3
version=$4

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$repo_root"

if [[ ! -d "$source_run" ]]; then
  echo "Source run does not exist: $source_run" >&2
  exit 66
fi

if [[ -e "$target_dir" ]]; then
  echo "Refusing to overwrite existing target: $target_dir" >&2
  exit 73
fi

if [[ ! "$vendor_id" =~ ^[a-z0-9][a-z0-9_-]*$ ]]; then
  echo "Invalid vendor ID: $vendor_id" >&2
  exit 64
fi

if [[ ! "$version" =~ ^[1-9][0-9]*$ ]]; then
  echo "Version must be a positive integer: $version" >&2
  exit 64
fi

python_bin="$repo_root/.venv/bin/python3"
if [[ ! -x "$python_bin" ]]; then
  echo "Missing project Python environment: $python_bin" >&2
  exit 69
fi

export PYTHONPATH="$repo_root/src${PYTHONPATH:+:$PYTHONPATH}"

"$python_bin" scripts/prepare-track-a-submission.py \
  "$source_run" "$target_dir" \
  --vendor-id "$vendor_id" \
  --version "$version"

echo
echo "Track A submission is RFP-ready:"
echo "  $target_dir"
echo "Both validators completed with zero errors and zero warnings."
