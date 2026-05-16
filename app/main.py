import time
import uuid
import json
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from app.core.config import get_settings
from app.core.logging import setup_logging
from app.middleware.correlation import CorrelationIdMiddleware
from app.middleware.error_handler import global_exception_handler
from app.api.routes import health,jobs

setup_logging()
logger = logging.getLogger(__name__)
settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(json.dumps({
        "event": "startup",
        "service": settings.app_name,
        "version": settings.app_version
    }))
    yield
    logger.info(json.dumps({"event": "shutdown"}))

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan
)

app.add_middleware(CorrelationIdMiddleware)
app.add_middleware(CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

app.add_exception_handler(Exception, global_exception_handler)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    request_id = getattr(request.state, "request_id", "unknown")
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": str(exc.errors()),
                "request_id": request_id
            }
        }
    )

@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration = round((time.time() - start) * 1000, 2)
    logger.info(json.dumps({
        "event": "request",
        "method": request.method,
        "path": request.url.path,
        "status": response.status_code,
        "duration_ms": duration,
        "request_id": getattr(request.state, "request_id", "unknown")
    }))
    return response

app.include_router(health.router)
app.include_router(jobs.router)