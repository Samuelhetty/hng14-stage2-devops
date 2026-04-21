"""
Unit tests for api/main.py
Redis is mocked with fakeredis — no real Redis instance required.
Run: pytest api/tests/ --cov=api --cov-report=xml -v
"""
import pytest
from unittest.mock import patch
import fakeredis
from fastapi.testclient import TestClient


# Patch redis.Redis BEFORE importing main so the module-level client is fake
@pytest.fixture(scope="module")
def client():
    fake = fakeredis.FakeRedis(decode_responses=True)
    with patch("redis.Redis", return_value=fake):
        from api.main import app
        yield TestClient(app)


# Test 1: health endpoint returns 200 and ok status
def test_health_ok(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


# Test 2: POST /jobs creates a job and returns a job_id
def test_create_job_returns_job_id(client):
    resp = client.post("/jobs")
    assert resp.status_code == 200
    data = resp.json()
    assert "job_id" in data
    assert len(data["job_id"]) == 36  # UUID4 format


# Test 3: newly created job has status "queued"
def test_created_job_has_queued_status(client):
    create_resp = client.post("/jobs")
    job_id = create_resp.json()["job_id"]

    status_resp = client.get(f"/jobs/{job_id}")
    assert status_resp.status_code == 200
    assert status_resp.json()["status"] == "queued"


# Test 4: GET /jobs/{id} returns 404 for unknown job
def test_get_nonexistent_job_returns_404(client):
    resp = client.get("/jobs/00000000-0000-0000-0000-000000000000")
    assert resp.status_code == 404


# Test 5: multiple jobs get distinct IDs
def test_multiple_jobs_have_unique_ids(client):
    ids = {client.post("/jobs").json()["job_id"] for _ in range(5)}
    assert len(ids) == 5  # all unique
