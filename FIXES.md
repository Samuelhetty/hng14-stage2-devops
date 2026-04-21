# FIXES.md

Here are the bugs found in the starter repository, with file, line number, problem, and fix.

---

## API Service (`api/`)

### FIX-01
- **File:** `api/main.py`
- **Line:** 5
- **Problem:** `redis.Redis(host="localhost", port=6379)` — `localhost` refers to the container itself, not the Redis service. This causes a `ConnectionRefusedError` on startup inside Docker.
- **Fix:** Changed to `redis.Redis(host=os.getenv("REDIS_HOST", "redis"), port=int(os.getenv("REDIS_PORT", 6379)), password=os.getenv("REDIS_PASSWORD"))`

### FIX-02
- **File:** `api/main.py`
- **Line:** 5
- **Problem:** Redis connection is created at module load time with no error handling. If Redis is not yet ready when the container starts, the entire app crashes immediately and never recovers.
- **Fix:** Wrapped Redis client instantiation in a function and added connection retry logic via `redis.exceptions.ConnectionError` catch in each route, plus a `/health` endpoint that tests the connection.

### FIX-03
- **File:** `api/main.py`
- **Line:** 5
- **Problem:** `REDIS_PASSWORD` is defined in `.env` and presumably set on the Redis instance, but it is never passed to the Redis client. Every Redis call would fail authentication.
- **Fix:** Added `password=os.getenv("REDIS_PASSWORD")` to the Redis constructor.

### FIX-04
- **File:** `api/main.py`
- **Line:** 13–14
- **Problem:** When a job ID is not found, the endpoint returns `{"error": "not found"}` with HTTP status **200**. This is incorrect REST behaviour — the frontend cannot distinguish a real job with status `None` from a missing job. The frontend's poll loop also has no guard for an error response, causing it to loop forever.
- **Fix:** Added `from fastapi import HTTPException` and raised `HTTPException(status_code=404, detail="Job not found")` when `status` is `None`.

### FIX-05
- **File:** `api/main.py`
- **Line:** (missing — no `/health` route existed)
- **Problem:** No health endpoint exists. The Docker `HEALTHCHECK` instruction and `depends_on: condition: service_healthy` in Compose both require a route that returns 200 when the service is ready. Without it, every healthcheck fails and dependent containers never start.
- **Fix:** Added `@app.get("/health")` route that pings Redis and returns `{"status": "ok"}`.


### FIX-06
- **File:** `api/.env`
- **Line:** entire file
- **Problem:** A `.env` file containing a real credential (`REDIS_PASSWORD=supersecretpassword123`) is committed to the repository. This is a critical security violation — credentials in git history are permanently exposed.
- **Fix:** Deleted `api/.env`. Added `.env` to `.gitignore`. Created `.env.example` at the repo root with placeholder values. The real `.env` must only exist on the deployment server and in GitHub Secrets, never in the repo.

---

## Worker Service (`worker/`)

### FIX-07
- **File:** `worker/worker.py`
- **Line:** 4
- **Problem:** Same `host="localhost"` bug as FIX-01. The worker cannot reach Redis inside Docker.
- **Fix:** Changed to `host=os.getenv("REDIS_HOST", "redis")`, with password and port from env vars.

### FIX-08
- **File:** `worker/worker.py`
- **Line:** 4
- **Problem:** `REDIS_PASSWORD` not passed to the Redis client — same as FIX-03.
- **Fix:** Added `password=os.getenv("REDIS_PASSWORD")` to the Redis constructor.

### FIX-09
- **File:** `worker/worker.py`
- **Line:** 3 (import present), body (never used)
- **Problem:** `import signal` is at the top, but no signal handlers are ever registered. When Docker stops the container it sends `SIGTERM`. Without a handler, the default action terminates the process immediately, potentially mid-job, leaving that job's status permanently stuck at `"queued"`.
- **Fix:** Registered a `SIGTERM` handler that sets a `shutdown` flag, allowing the current job to finish before the loop exits cleanly.

### FIX-10
- **File:** `worker/worker.py`
- **Line:** 10–13 (`process_job` call in the while loop)
- **Problem:** No `try/except` around `process_job`. If any exception occurs (e.g., Redis write fails mid-job), the entire worker process crashes and stops processing all future jobs.
- **Fix:** Wrapped the `process_job` call in a `try/except Exception` block that logs the error and sets the job status to `"failed"` so the job does not silently disappear.


---

## Frontend Service (`frontend/`)

### FIX-11
- **File:** `frontend/app.js`
- **Line:** 5
- **Problem:** `const API_URL = "http://localhost:8000"` is hardcoded. Inside Docker, `localhost` is the frontend container itself, not the API container. Every proxied request to the API fails with `ECONNREFUSED`.
- **Fix:** Changed to `const API_URL = process.env.API_URL || "http://api:8000"` so it is configurable via environment variable and has a sensible default for Docker Compose.

### FIX-12
- **File:** `frontend/app.js`
- **Line:** (missing — no `/health` route existed)
- **Problem:** No health endpoint. Same consequence as FIX-05 — the Docker healthcheck and Compose `depends_on` have nothing to call.
- **Fix:** Added `app.get('/health', (req, res) => res.json({ status: 'ok' }))`.

### FIX-13
- **File:** `frontend/views/index.html`
- **Line:** 30 (`if (data.status !== 'completed')`)
- **Problem:** If a job ID is not found (API returns 404 / error object), `data.status` is `undefined`. The condition `undefined !== 'completed'` is always `true`, so `pollJob` recurses infinitely, flooding the API with requests and locking up the browser tab.
- **Fix:** Added a guard: `if (data.error || !data.status) { renderJob(id, 'error'); return; }` before the poll continuation check.

---

## Summary Table

| ID | File | Line | Category | Description |
|----|------|------|----------|-------------|
| FIX-01 | api/main.py | 5 | Networking | Redis host hardcoded as `localhost` |
| FIX-02 | api/main.py | 5 | Reliability | No Redis connection error handling at startup |
| FIX-03 | api/main.py | 5 | Security/Auth | REDIS_PASSWORD env var ignored in Redis client |
| FIX-04 | api/main.py | 13 | HTTP correctness | 404 returned as HTTP 200 |
| FIX-05 | api/main.py | — | Ops | Missing `/health` endpoint |
| FIX-06 | api/.env | entire file | Security | Real credentials committed to repository |
| FIX-07 | worker/worker.py | 4 | Networking | Redis host hardcoded as `localhost` |
| FIX-08 | worker/worker.py | 4 | Security/Auth | REDIS_PASSWORD env var ignored in Redis client |
| FIX-09 | worker/worker.py | 3/body | Reliability | SIGTERM handler imported but never registered |
| FIX-10 | worker/worker.py | 10–13 | Reliability | No exception handling — one bad job kills the worker |
| FIX-11 | frontend/app.js | 5 | Networking | API_URL hardcoded as `localhost` |
| FIX-12 | frontend/app.js | — | Ops | Missing `/health` endpoint |
| FIX-13 | frontend/views/index.html | 30 | UX/Reliability | Infinite poll loop when job not found |