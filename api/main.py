from fastapi import FastAPI, HTTPException
import redis
import uuid
import os

app = FastAPI()


def get_redis():
    return redis.Redis(
        host=os.getenv("REDIS_HOST", "redis"),
        port=int(os.getenv("REDIS_PORT", 6379)),
        password=os.getenv("REDIS_PASSWORD"),
        decode_responses=True,
    )


@app.get("/health")
def health():
    # Added health endpoint required by Docker HEALTHCHECK and Compose
    try:
        r = get_redis()
        r.ping()
        return {"status": "ok"}
    except redis.exceptions.ConnectionError:
        raise HTTPException(status_code=503, detail="Redis unavailable")


@app.post("/jobs")
def create_job():
    # Redis now uses env vars (host, port, password)
    r = get_redis()
    job_id = str(uuid.uuid4())
    r.lpush("jobs", job_id)
    r.hset(f"job:{job_id}", "status", "queued")
    return {"job_id": job_id}


@app.get("/jobs/{job_id}")
def get_job(job_id: str):
    r = get_redis()
    status = r.hget(f"job:{job_id}", "status")
    if not status:
        # Return proper 404 instead of 200 with error body
        raise HTTPException(status_code=404, detail="Job not found")
    return {"job_id": job_id, "status": status}
