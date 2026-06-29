#!/usr/bin/env bash
# Deploy the Sadot CRM on aiserver. Idempotent; safe to re-run.
# Run by GitHub Actions (.github/workflows/deploy.yml) after pushing to main,
# or manually:  bash deploy/deploy.sh
#
# Assumes (verified on aiserver): docker works without sudo, sudo is passwordless,
# repo checked out at /home/aiserver/projects/sadot, secrets in .env + backend/.env
# (gitignored, NOT touched by this script).
set -euo pipefail

REPO_DIR="${SADOT_DIR:-/home/aiserver/projects/sadot}"
COMPOSE="docker compose -f docker-compose.yml -f docker-compose.prod.yml"
cd "$REPO_DIR"

# Poll a URL until it answers 2xx, up to (tries*2) seconds. Non-zero on timeout.
wait_for() {
  local name="$1" url="$2" tries="${3:-30}" i
  for ((i = 1; i <= tries; i++)); do
    if curl -fsS -o /dev/null "$url"; then
      echo "ready: $name ($url) after ~$(((i - 1) * 2))s"
      return 0
    fi
    sleep 2
  done
  echo "TIMEOUT: $name not ready after $((tries * 2))s ($url)"
  return 1
}

echo "== [1/6] sync code to origin/main =="
git fetch --prune origin
git reset --hard origin/main
git --no-pager log --oneline -1

echo "== [2/6] build + (re)start containers =="
$COMPOSE up -d --build

echo "== [3/6] wait for backend readiness =="
# The backend runs DB init + seed on startup. Wait until /health answers so the
# alembic step and the final health checks don't race container startup
# (connection-refused / 502 was the recurring false-alarm deploy failure).
if ! wait_for "backend" "http://127.0.0.1:8001/health" 45; then
  echo "!! backend did not become ready -- recent logs:"
  $COMPOSE logs --tail 50 backend || true
  exit 1
fi

echo "== [4/6] database migrations (alembic) =="
# The app's lifespan runs SQLModel create_all on startup, so the schema already
# exists. If alembic has no version stamped, stamp head first -- otherwise
# `upgrade head` re-runs the initial migration and fails with DuplicateTable.
# Then apply any newer migrations. (Backend is confirmed ready above, so
# create_all has finished and the exec calls are safe.)
alembic_current="$($COMPOSE exec -T backend alembic current 2>/dev/null | grep -oE '[0-9a-f]{12}' | head -1 || true)"
if [ -z "$alembic_current" ]; then
  echo "alembic: no version stamped -> stamping head to match existing schema"
  $COMPOSE exec -T backend alembic stamp head || echo "WARN: alembic stamp failed -- continuing"
fi
if $COMPOSE exec -T backend alembic upgrade head; then
  echo "alembic: at head"
else
  echo "WARN: alembic upgrade failed -- continuing"
fi

echo "== [5/6] sync nginx vhost + static mockups =="
sudo cp deploy/nginx-sadot.conf /etc/nginx/sites-available/sadot
sudo mkdir -p /var/www/sadot-mockups
sudo cp mockups/index.html /var/www/sadot-mockups/index.html
sudo chmod 644 /var/www/sadot-mockups/index.html
sudo nginx -t
sudo systemctl reload nginx

echo "== [6/6] health checks =="
fail=0
# Frontend can take a moment longer than the backend to start serving.
wait_for "frontend" "http://127.0.0.1:3001/crm" 30 || fail=1
curl -fsS  -o /dev/null -w "backend  127.0.0.1:8001/health -> %{http_code}\n" http://127.0.0.1:8001/health || fail=1
curl -fsSk -o /dev/null -w "https /api/v1/public/dogs -> %{http_code}\n" --resolve sadot.lavit.io:443:127.0.0.1 https://sadot.lavit.io/api/v1/public/dogs || fail=1
curl -fsSk -o /dev/null -w "https /crm (frontend)     -> %{http_code}\n" --resolve sadot.lavit.io:443:127.0.0.1 https://sadot.lavit.io/crm || fail=1
curl -fsSk -o /dev/null -w "https /mockups/           -> %{http_code}\n" --resolve sadot.lavit.io:443:127.0.0.1 https://sadot.lavit.io/mockups/ || fail=1
# WordPress at / lives in the separate basadot-wp compose project; warn (don't fail) if it's down:
curl -fsSk -o /dev/null -w "https / (WordPress)       -> %{http_code}\n" --resolve sadot.lavit.io:443:127.0.0.1 https://sadot.lavit.io/ || echo "WARN: WordPress (/) not responding -- check basadot-wp containers"

if [ "$fail" -ne 0 ]; then
  echo "!! one or more health checks failed"; exit 1
fi
echo "== deploy OK =="
