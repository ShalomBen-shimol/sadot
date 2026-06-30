# Sadot E2E — Dockerized Playwright UI tests

Real-browser smoke tests for the CRM admin, run inside the official Playwright
Docker image (Chromium/Firefox/WebKit + OS deps included). Produces an HTML
report with screenshots, video, and step traces so each run is inspectable.

## What's covered (auth + save smoke)

| Test | Tag | Mutates data |
|------|-----|--------------|
| Admin can log in and reach the dashboard | `@smoke` | no |
| Invalid/expired token redirects to login (regression for PR #1) | `@smoke` | no |
| Editing an authority email saves and survives a reload | `@write` | yes |

## Run in CI (every PR)

`.github/workflows/e2e.yml` brings up an ephemeral `db + backend + frontend`
stack via `docker-compose.yml`, waits for readiness, then runs the full suite
(including `@write`, since the DB is throwaway). The `playwright-report`
artifact is uploaded on every run — download it from the workflow run to view.

## Run against the live site (on demand, from aiserver)

The live site has Docker; the local Windows dev box does not. SSH to aiserver and:

```bash
cd /home/aiserver/projects/sadot/e2e
git pull
E2E_ADMIN_PASSWORD='<real admin password from ../backend/.env>' ./run-live.sh
```

Defaults to **read-only** `@smoke` (login + redirect) so it won't touch live
data. To also run the data-mutating save test (may leave a test email if the
first authority had none):

```bash
E2E_ALLOW_WRITES=1 E2E_ADMIN_PASSWORD='...' ./run-live.sh
```

## Run locally (any machine with Docker)

```bash
docker build -t sadot-e2e ./e2e
docker run --rm --network host \
  -e E2E_BASE_URL=http://localhost:3000 \
  -e E2E_ADMIN_EMAIL=admin@sadot.local -e E2E_ADMIN_PASSWORD=admin1234 \
  -v "$PWD/e2e/playwright-report:/e2e/playwright-report" \
  sadot-e2e
```

## Configuration (env vars)

| Var | Default | Purpose |
|-----|---------|---------|
| `E2E_BASE_URL` | `http://localhost:3000` | Site under test (origin; `/crm` is added by tests) |
| `E2E_ADMIN_EMAIL` | `admin@sadot.local` | Admin login |
| `E2E_ADMIN_PASSWORD` | `admin1234` | Admin password (override for live) |
| `E2E_ALLOW_WRITES` | `1` | Set `0` to skip the data-mutating `@write` test |
