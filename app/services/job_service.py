from app.db.database import get_supabase
from app.schemas.job import JobCreate, JobStatus
from typing import Optional, List

# Valid state transitions — only these are allowed
VALID_TRANSITIONS = {
    JobStatus.PENDING:   [JobStatus.RUNNING],
    JobStatus.RUNNING:   [JobStatus.COMPLETED, JobStatus.FAILED],
    JobStatus.FAILED:    [JobStatus.RETRYING, JobStatus.DEAD_LETTER],
    JobStatus.RETRYING:  [JobStatus.RUNNING],
}


def create_job(job_in: JobCreate, request_id: str) -> dict:
    supabase = get_supabase()
    data = {
        "name": job_in.name,
        "status": JobStatus.PENDING.value,
        "payload": job_in.payload or {},
        "retry_count": 0,
        "max_retries": 3,
        "request_id": request_id,
    }
    response = supabase.table("jobs").insert(data).execute()
    return response.data[0]


def get_job(job_id: str) -> Optional[dict]:
    supabase = get_supabase()
    response = (
        supabase.table("jobs")
        .select("*")
        .eq("id", job_id)
        .execute()
    )
    if response.data:
        return response.data[0]
    return None


def list_jobs(limit: int = 20, offset: int = 0) -> List[dict]:
    supabase = get_supabase()
    response = (
        supabase.table("jobs")
        .select("*")
        .order("created_at", desc=True)
        .range(offset, offset + limit - 1)
        .execute()
    )
    return response.data


def transition_status(
    job_id: str,
    new_status: JobStatus,
    error_msg: str = None
) -> dict:
    supabase = get_supabase()

    # Fetch current job
    response = supabase.table("jobs").select("*").eq("id", job_id).execute()
    if not response.data:
        raise ValueError(f"Job {job_id} not found")

    job = response.data[0]
    current_status = JobStatus(job["status"])

    # Validate transition
    valid_next = VALID_TRANSITIONS.get(current_status, [])
    if new_status not in valid_next:
        raise ValueError(
            f"Invalid transition: {current_status} → {new_status}"
        )

    update_data = {"status": new_status.value}
    if error_msg:
        update_data["error_msg"] = error_msg

    response = (
        supabase.table("jobs")
        .update(update_data)
        .eq("id", job_id)
        .execute()
    )
    return response.data[0]