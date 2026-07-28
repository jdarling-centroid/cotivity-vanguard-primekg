#!/usr/bin/env bash
# Bring up the LOCAL Oracle container. Local-only by design: this script refuses
# anything but `--database local` and never targets a remote/Autonomous schema.
set -euo pipefail
cd "$(dirname "$0")"

DATABASE=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --database)
      DATABASE="${2:-}"
      shift 2
      ;;
    *)
      echo "unknown argument: $1" >&2
      echo "usage: ./up.sh --database local" >&2
      exit 2
      ;;
  esac
done

if [[ "$DATABASE" != "local" ]]; then
  echo "Refusing to start: pass --database local." >&2
  echo "Remote/Autonomous is intentionally unsupported by this script." >&2
  exit 2
fi

if [[ ! -f .env ]]; then
  echo "No .env found; copy .env.example to .env first." >&2
  exit 1
fi

docker compose --env-file .env -f docker/compose.yaml up -d
echo "Local Oracle starting. Watch health with: docker compose -f docker/compose.yaml ps"
