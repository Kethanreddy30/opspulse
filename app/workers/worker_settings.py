from arq.connections import RedisSettings
from app.core.config import get_settings
from app.workers.tasks import process_job

def get_redis_settings() -> RedisSettings:
    settings = get_settings()
    url = settings.redis_url.replace("rediss://", "")
    userinfo, hostport = url.split("@")
    password = userinfo.split(":")[1]
    host, port = hostport.split(":")
    return RedisSettings(
        host=host,
        port=int(port),
        password=password,
        ssl=True,
        conn_timeout=30,
        conn_retries=5,
        conn_retry_delay=2,
    )

class WorkerSettings:
    functions = [process_job]
    redis_settings = get_redis_settings()
    max_jobs = 10
    job_timeout = 300
    retry_jobs = True
    keep_result = 300