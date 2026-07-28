#!/usr/bin/env bash
# Stop the local Oracle container. Pass --purge to also delete the data volume.
set -euo pipefail
cd "$(dirname "$0")"

PURGE="no"
while [[ $# -gt 0 ]]; do
  case "$1" in
    --purge)
      PURGE="yes"
      shift
      ;;
    *)
      echo "unknown argument: $1" >&2
      echo "usage: ./down.sh [--purge]" >&2
      exit 2
      ;;
  esac
done

if [[ "$PURGE" == "yes" ]]; then
  docker compose -f docker/compose.yaml down -v
  echo "Local Oracle stopped and data volume removed."
else
  docker compose -f docker/compose.yaml down
  echo "Local Oracle stopped (data volume preserved)."
fi
