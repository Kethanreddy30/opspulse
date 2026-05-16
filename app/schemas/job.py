from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from enum import Enum


class JobStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    RETRYING = "RETRYING"
    DEAD_LETTER = "DEAD_LETTER"


class JobCreate(BaseModel):
    name: str
    payload: Optional[dict] = {}


class JobResponse(BaseModel):
    id: str
    name: str
    status: JobStatus
    payload: Optional[dict] = None
    result: Optional[dict] = None
    retry_count: int
    max_retries: int
    error_msg: Optional[str] = None
    request_id: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}