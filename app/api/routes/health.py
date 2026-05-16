from fastapi import APIRouter
from app.core.config import get_settings
from app.db.database import get_supabase
import httpx

router = APIRouter()


@router.get("/health")
def health():
    settings = get_settings()
    checks = {
        "database": "unknown",
        "redis": "unknown",
    }

    # Check Supabase
    try:
        supabase = get_supabase()
        supabase.table("jobs").select("id").limit(1).execute()
        checks["database"] = "ok"
    except Exception as e:
        checks["database"] = f"error: {str(e)[:80]}"

    # Check Upstash Redis via REST API
    try:
        response = httpx.get(
            f"{settings.upstash_redis_rest_url}/ping",
            headers={
                "Authorization": f"Bearer {settings.upstash_redis_rest_token}"
            },
            timeout=3.0,
        )
        checks["redis"] = "ok" if response.status_code == 200 else f"error: {response.status_code}"
    except Exception as e:
        checks["redis"] = f"error: {str(e)[:80]}"

    status = "ok" if all(v == "ok" for v in checks.values()) else "degraded"

    return {
        "status": status,
        "service": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "checks": checks,
    }