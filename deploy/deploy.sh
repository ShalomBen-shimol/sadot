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

echo "== [1/6] sync code to origin/main =="
git fetch --prune origin
git reset --hard origin/main
git --no-pager log --oneline -1

echo "== [2/6] build + (re)start containers =="
$COMPOSE up -d --build

echo "== [3/6] database migrations (alembic) =="
if $COMPOSE exec -T backend alembic upgrade head; then
  echo "migrations applied"
else
  echo "WARN: alembic upgrade failed or not applicable -- continuing"
fi

echo "== [4/6] sync nginx vhost + static mockups =="
sudo cp deploy/nginx-sadot.conf /etc/nginx/sites-available/sadot
sudo mkdir -p /var/www/sadot-mockups
sudo cp mockups/index.html /var/www/sadot-mockups/index.html
sudo chmod 644 /var/www/sadot-mockups/index.html

echo "== [5/6] validate + reload nginx =="
sudo nginx -t
sudo systemctl reload nginx

echo "== [6/6] health checks =="
sleep 3
fail=0
curl -fsS -o /dev/null -w "backend  127.0.0.1:8001/health -> %{http_code}\n" http://127.0.0.1:8001/health || fail=1
curl -fsS -o /dev/null -w "frontend 127.0.0.1:3001/       -> %{http_code}\n" http://127.0.0.1:3001/ || fail=1
curl -fsSk -o /dev/null -w "https /            -> %{http_code}\n" --resolve sadot.lavit.io:443:127.0.0.1 https://sadot.lavit.io/ || fail=1
curl -fsSk -o /dev/null -w "https /mockups/    -> %{http_code}\n" --resolve sadot.lavit.io:443:127.0.0.1 https://sadot.lavit.io/mockups/ || fail=1
curl -fsSk -o /dev/null -w "https /api/v1/public/dogs -> %{http_code}\n" --resolve sadot.lavit.io:443:127.0.0.1 https://sadot.lavit.io/api/v1/public/dogs || fail=1

if [ "$fail" -ne 0 ]; then
  echo "!! one or more health checks failed"; exit 1
fi
echo "== deploy OK =="
