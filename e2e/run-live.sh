#!/usr/bin/env bash
# Run the UI smoke against the LIVE site (https://sadot.lavit.io) from a host
# with Docker (e.g. aiserver). Read-only by default — it logs in and checks the
# 401->login redirect, but does NOT mutate data.
#
# Usage (on aiserver):
#   cd /home/aiserver/projects/sadot/e2e
#   E2E_ADMIN_PASSWORD='<real admin password from backend/.env>' ./run-live.sh
#
# Opt in to the data-mutating save test (leaves a test email if the chosen
# authority had none) with:  E2E_ALLOW_WRITES=1 ... ./run-live.sh
set -euo pipefail
cd "$(dirname "$0")"

: "${E2E_ADMIN_PASSWORD:?set E2E_ADMIN_PASSWORD to the live admin password}"

BASE_URL="${E2E_BASE_URL:-https://sadot.lavit.io}"
ADMIN_EMAIL="${E2E_ADMIN_EMAIL:-admin@sadot.local}"
ALLOW_WRITES="${E2E_ALLOW_WRITES:-0}"
# Read-only smoke unless writes are explicitly enabled.
GREP_ARGS=(--grep "@smoke")
if [ "$ALLOW_WRITES" = "1" ]; then GREP_ARGS=(); fi

docker build -t sadot-e2e .
docker run --rm \
  -e E2E_BASE_URL="$BASE_URL" \
  -e E2E_ADMIN_EMAIL="$ADMIN_EMAIL" \
  -e E2E_ADMIN_PASSWORD="$E2E_ADMIN_PASSWORD" \
  -e E2E_ALLOW_WRITES="$ALLOW_WRITES" \
  -e CI=1 \
  -v "$PWD/playwright-report:/e2e/playwright-report" \
  -v "$PWD/test-results:/e2e/test-results" \
  sadot-e2e "${GREP_ARGS[@]}"

echo "Report written to e2e/playwright-report/ (copy it off the server to view)."
