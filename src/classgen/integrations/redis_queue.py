"""Redis-backed job queue for ClassGen batch operations.

Handles batch lesson generation job tracking.
Uses in-memory queue for local dev, Redis for production.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field

from dotenv import load_dotenv

load_dotenv()

_redis_url = os.environ.get("REDIS_URL", "")
_redis = None

if _redis_url:
    try:
        import redis
        _redis = redis.from_url(_redis_url)
        _redis.ping()
        print(f"Redis connected: {_redis_url}")
    except Exception as e:
        print(f"Redis not available ({e}). Using in-memory queue.")
        _redis = None

# In-memory fallback queue
_mem_queue: list[dict] = []
_mem_results: dict[str, dict] = {}


@dataclass
class BatchJob:
    job_id: str
    teacher_phone: str
    topics: list[dict] = field(default_factory=list)  # [{class_level, subject, topic}]
    status: str = "pending"  # pending, running, completed, failed
    completed: int = 0
    total: int = 0
    results: list[dict] = field(default_factory=list)


def create_batch_job(job_id: str, teacher_phone: str, topics: list[dict]) -> BatchJob:
    """Create a batch generation job."""
    job = BatchJob(
        job_id=job_id,
        teacher_phone=teacher_phone,
        topics=topics,
        total=len(topics),
    )
    job_data = {
        "job_id": job_id,
        "teacher_phone": teacher_phone,
        "topics": topics,
        "status": "pending",
        "completed": 0,
        "total": len(topics),
        "results": [],
    }
    if _redis:
        _redis.set(f"batch:{job_id}", json.dumps(job_data), ex=3600)
    else:
        _mem_results[job_id] = job_data
    return job


def get_batch_job(job_id: str) -> dict | None:
    """Get batch job status."""
    if _redis:
        data = _redis.get(f"batch:{job_id}")
        return json.loads(data) if data else None
    return _mem_results.get(job_id)


def update_batch_job(job_id: str, completed: int, status: str = "running",
                     result: dict | None = None):
    """Update batch job progress."""
    job = get_batch_job(job_id)
    if not job:
        return
    job["completed"] = completed
    job["status"] = status
    if result:
        job["results"].append(result)
    if _redis:
        _redis.set(f"batch:{job_id}", json.dumps(job), ex=3600)
    else:
        _mem_results[job_id] = job
