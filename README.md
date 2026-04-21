# HNG14 Stage 2 DevOps — Job Processing System

A containerised, CI/CD-enabled job processing system consisting of:

| Service  | Tech | Role |
|----------|------|------|
| `frontend` | Node.js / Express | Job submission UI + API proxy |
| `api` | Python / FastAPI | Job creation and status endpoints |
| `worker` | Python | Picks jobs from Redis queue and processes them |
| `redis` | Redis 7 | Internal message queue (not exposed to host) |

---

## Prerequisites

| Tool | Minimum version |
|------|----------------|
| Git | any recent |
| Docker | 24.x |
| Docker Compose | v2.x (`docker compose`, not `docker-compose`) |
| curl + jq | for smoke-testing (optional) |

No cloud account is required. Everything runs locally.

---

## Bring the Stack Up (Clean Machine)

```bash
# 1. Clone your fork
git clone https://github.com/Samuelhetty/hng14-stage2-devops.git
cd hng14-stage2-devops

# 2. Create your local .env (never commit this file)
cp .env.example .env
# Edit .env and set a strong REDIS_PASSWORD before continuing

# 3. Build and start all services
docker compose up -d --build

# 4. Confirm everything is healthy
docker compose ps
```

---

## What a Successful Startup Looks Like

```
NAME                STATUS
redis               Up X seconds (healthy)
api                 Up X seconds (healthy)
worker              Up X seconds (healthy)
frontend            Up X seconds (healthy)
```

All four services must show `(healthy)`. If any shows `(starting)` for more than
60 seconds, check logs:

```bash
docker compose logs redis
docker compose logs api
```

---

## Verify the System End-to-End

```bash
# API health
curl http://localhost:8000/health
# → {"status":"ok"}

# Frontend health
curl http://localhost:3000/health
# → {"status":"ok"}

# Submit a job via the API
JOB_ID=$(curl -s -X POST http://localhost:8000/jobs | jq -r '.job_id')
echo "Job submitted: $JOB_ID"

# Poll status (worker takes ~2 seconds to process)
curl http://localhost:8000/jobs/$JOB_ID
# → {"job_id":"...","status":"queued"}
sleep 4
curl http://localhost:8000/jobs/$JOB_ID
# → {"job_id":"...","status":"completed"}
```

You can also open http://localhost:3000 in your browser and click **Submit New Job**.

---

## Environment Variables

All configuration comes from `.env` (never committed — see `.env.example`):

| Variable | Used by | Description |
|----------|---------|-------------|
| `REDIS_HOST` | api, worker | Redis service hostname (default: `redis`) |
| `REDIS_PORT` | api, worker | Redis port (default: `6379`) |
| `REDIS_PASSWORD` | redis, api, worker | Redis auth password — **must be set** |
| `APP_ENV` | api | Runtime environment (`production`) |
| `API_URL` | frontend | How the frontend container reaches the API |

---

## Tear Down

```bash
# Stop and remove containers + volumes
docker compose down -v
```

---

## CI/CD Pipeline

Implemented in `.github/workflows/cd.yml`. Stages run in strict order;
any failure blocks all subsequent stages:

```
lint → test → build → security-scan → integration-test → deploy
```

| Stage | What it does |
|-------|-------------|
| **lint** | flake8 (Python), eslint (JS), hadolint (Dockerfiles) |
| **test** | pytest with Redis mocked via fakeredis; uploads coverage XML as artifact |
| **build** | Builds all 3 images, tags with git SHA + `latest`, pushes to in-job registry |
| **security-scan** | Trivy scan of all images; fails on CRITICAL findings; uploads SARIF artifact |
| **integration-test** | Full stack inside the runner; submits a real job; polls until `completed` |
| **deploy** | Runs on `main` pushes only; rolling update with 60s health-check window |

### GitHub Secrets required for deploy stage

| Secret | Value |
|--------|-------|
| `DEPLOY_HOST` | IP or hostname of your server |
| `DEPLOY_USER` | SSH username |
| `SSH_KEY` | Private SSH key (the public key must be in `~/.ssh/authorized_keys` on server) |

---

## Bugs Fixed

See [FIXES.md](FIXES.md) for the full list of 13 bugs found and corrected.

---

## Project Structure

```
.
├── .env.example               # Placeholder env vars
├── .gitignore
├── docker-compose.yml
├── README.md
├── FIXES.md
├── api/
│   ├── Dockerfile             # Multi-stage, non-root, healthcheck
│   ├── main.py
│   ├── requirements.txt
│   └── tests/
│       ├── test_main.py       # 5 unit tests, Redis mocked
│       └── requirements-test.txt
├── worker/
│   ├── Dockerfile
│   ├── worker.py
│   └── requirements.txt
└── frontend/
    ├── Dockerfile
    ├── app.js
    ├── package.json
    └── views/
        └── index.html
```
