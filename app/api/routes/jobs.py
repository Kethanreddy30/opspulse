from fastapi import APIRouter, HTTPException, Request
from arq import create_pool
from arq.connections import RedisSettings
from app.schemas.job import JobCreate, JobResponse
from app.services import job_service
from app.workers.worker_settings import get_redis_settings
from typing import List

router = APIRouter(prefix="/api/v1/jobs", tags=["jobs"])


@router.post("/", response_model=JobResponse, status_code=201)
async def create_job(job_in: JobCreate, request: Request):
    request_id = getattr(request.state, "request_id", "unknown")
    try:
        job = job_service.create_job(job_in, request_id)
        redis = await create_pool(get_redis_settings())
        await redis.enqueue_job("process_job", job["id"], request_id)
        await redis.close()
        return job
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=List[JobResponse])
def list_jobs(limit: int = 20, offset: int = 0):
    return job_service.list_jobs(limit=limit, offset=offset)


@router.get("/{job_id}", response_model=JobResponse)
def get_job(job_id: str):
    job = job_service.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job