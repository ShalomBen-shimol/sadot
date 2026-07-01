#!/usr/bin/env bash
# Capture full-page PNG screenshots of live pages, using the Playwright Docker
# image (run on a host with Docker, e.g. aiserver). No login / no data writes.
#
# Usage (on aiserver):
#   cd /home/aiserver/projects/sadot/e2e
#   ./screenshot.sh
#
# Custom targets (name|url pairs, comma-separated):
#   E2E_SHOTS="home|https://sadot.lavit.io/,new-adopt|https://sadot.lavit.io/crm/adopt" ./screenshot.sh
#
# Output: e2e/screenshots/<name>-<desktop|mobile>.png
# Then commit them (git add e2e/screenshots && git commit && git push) or copy
# them off the server so they can be reviewed.
set -euo pipefail
cd "$(dirname "$0")"

mkdir -p screenshots

docker build -t sadot-e2e .
docker run --rm \
  -e E2E_SHOTS="${E2E_SHOTS:-}" \
  -e CI=1 \
  -v "$PWD/screenshots:/e2e/screenshots" \
  sadot-e2e screenshots.spec.ts

echo "Screenshots written to e2e/screenshots/"
ls -1 screenshots/ || true
