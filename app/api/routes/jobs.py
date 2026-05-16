from fastapi import APIRouter, HTTPException, Request
from app.schemas.job import JobCreate, JobResponse
from app.services import job_service
from typing import List

router = APIRouter(prefix="/api/v1/jobs", tags=["jobs"])


@router.post("/", response_model=JobResponse, status_code=201)
def create_job(job_in: JobCreate, request: Request):
    request_id = getattr(request.state, "request_id", "unknown")
    try:
        job = job_service.create_job(job_in, request_id)
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