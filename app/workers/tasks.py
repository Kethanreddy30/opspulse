import asyncio
import json
import logging
from app.db.database import get_supabase
from app.services.job_service import transition_status
from app.schemas.job import JobStatus

logger = logging.getLogger(__name__)
BACKOFF_DELAYS = [0, 30, 120]


async def process_job(ctx: dict, job_id: str, request_id: str):
    logger.info(json.dumps({
        "event": "worker_pickup",
        "job_id": job_id,
        "request_id": request_id
    }))

    supabase = get_supabase()

    # FIX: wrap ALL sync supabase calls in asyncio.to_thread
    response = await asyncio.to_thread(
        lambda: supabase.table("jobs").select("*").eq("id", job_id).execute()
    )
    if not response.data:
        logger.error(json.dumps({"event": "job_not_found", "job_id": job_id}))
        return

    job = response.data[0]

    try:
        await asyncio.to_thread(lambda: transition_status(job_id, JobStatus.RUNNING))
        logger.info(json.dumps({
            "event": "job_running",
            "job_id": job_id,
            "request_id": request_id
        }))
    except ValueError as e:
        logger.error(json.dumps({
            "event": "transition_failed",
            "job_id": job_id,
            "error": str(e)
        }))
        return

    try:
        await asyncio.sleep(2)
        result = {"processed": True, "job_id": job_id}

        await asyncio.to_thread(
            lambda: supabase.table("jobs").update({
                "status": JobStatus.COMPLETED.value,
                "result": result
            }).eq("id", job_id).execute()
        )

        logger.info(json.dumps({
            "event": "job_completed",
            "job_id": job_id,
            "request_id": request_id
        }))

    except Exception as e:
        retry_count = job["retry_count"] + 1

        if retry_count >= job["max_retries"]:
            await asyncio.to_thread(
                lambda: supabase.table("jobs").update({
                    "status": JobStatus.DEAD_LETTER.value,
                    "error_msg": str(e),
                    "retry_count": retry_count
                }).eq("id", job_id).execute()
            )
            logger.error(json.dumps({
                "event": "job_dead_letter",
                "job_id": job_id,
                "request_id": request_id
            }))
        else:
            delay = BACKOFF_DELAYS[min(retry_count, len(BACKOFF_DELAYS) - 1)]
            await asyncio.to_thread(
                lambda: supabase.table("jobs").update({
                    "status": JobStatus.RETRYING.value,
                    "retry_count": retry_count,
                    "error_msg": str(e)
                }).eq("id", job_id).execute()
            )
            await ctx["redis"].enqueue_job(
                "process_job", job_id, request_id,
                _defer_by=delay
            )
            logger.info(json.dumps({
                "event": "job_retrying",
                "job_id": job_id,
                "delay_seconds": delay,
                "attempt": retry_count
            }))