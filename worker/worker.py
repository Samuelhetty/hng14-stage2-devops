import redis
import time
import os
import signal
import sys
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# Use env vars for Redis host and password instead of localhost
r = redis.Redis(
    host=os.getenv("REDIS_HOST", "redis"),
    port=int(os.getenv("REDIS_PORT", 6379)),
    password=os.getenv("REDIS_PASSWORD"),
    decode_responses=True,
)

# Register SIGTERM handler so the worker finishes its current job
# before shutting down instead of dying mid-job
shutdown = False


def handle_sigterm(signum, frame):
    global shutdown
    logger.info("SIGTERM received — finishing current job then exiting")
    shutdown = True


signal.signal(signal.SIGTERM, handle_sigterm)
signal.signal(signal.SIGINT, handle_sigterm)


def process_job(job_id: str):
    logger.info(f"Processing job {job_id}")
    time.sleep(2)  # simulate work
    r.hset(f"job:{job_id}", "status", "completed")
    logger.info(f"Completed job {job_id}")


while not shutdown:
    try:
        # queue name kept as "jobs" — must match api/main.py lpush key
        job = r.brpop("jobs", timeout=5)
    except redis.exceptions.ConnectionError as e:
        logger.error(f"Redis connection error: {e} — retrying in 3s")
        time.sleep(3)
        continue

    if job:
        _, job_id = job
        # Wrap job processing in try/except so one bad job cannot
        # crash the worker and halt all future processing
        try:
            process_job(job_id)
        except Exception as e:
            logger.error(f"Job {job_id} failed: {e}")
            try:
                r.hset(f"job:{job_id}", "status", "failed")
            except Exception:
                pass  # best-effort status update

logger.info("Worker shut down cleanly")
sys.exit(0)
