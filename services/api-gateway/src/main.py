# src/main.py
# GridSense API Gateway — FastAPI application
# Serves real-time and historical load shedding data

import os
from datetime import datetime, timezone
from typing import Optional
import structlog
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from models import LoadSheddingStatus, HealthResponse, ErrorResponse
from kafka_consumer import get_latest_validated_event

load_dotenv()

structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.add_log_level,
        structlog.processors.JSONRenderer(),
    ]
)

logger = structlog.get_logger(__name__)

# ── Configuration ──────────────────────────────────────────────────
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS")
API_VERSION             = os.getenv("API_VERSION", "1.0.0")

# ── FastAPI App ────────────────────────────────────────────────────
app = FastAPI(
    title="GridSense SA API",
    description="National Energy Intelligence Platform API",
    version=API_VERSION,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# Allow cross-origin requests from web/mobile clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request logging middleware ─────────────────────────────────────
@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(
        "request_received",
        method=request.method,
        path=request.url.path,
        client=request.client.host if request.client else "unknown",
    )
    response = await call_next(request)
    logger.info(
        "request_completed",
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
    )
    return response


# ── Endpoints ──────────────────────────────────────────────────────
@app.get("/api/v1/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint — used by Kubernetes liveness probe."""
    return HealthResponse(
        status="healthy",
        service="gridsense-api-gateway",
        version=API_VERSION,
        timestamp=datetime.now(timezone.utc),
    )


@app.get("/api/v1/status", response_model=LoadSheddingStatus)
async def get_current_status():
    """
    Returns the current national load shedding status.
    Data sourced from the validated Kafka topic.
    """
    if not KAFKA_BOOTSTRAP_SERVERS:
        raise HTTPException(
            status_code=503,
            detail="Kafka not configured"
        )

    event = get_latest_validated_event(
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS
    )

    if not event:
        raise HTTPException(
            status_code=503,
            detail="No validated data available yet"
        )

    return LoadSheddingStatus(
        stage=event.get("stage", 0),
        stage_since=event.get("stage_start_timestamp"),
        next_stages=event.get("next_stages", []),
        last_updated=event.get("timestamp", datetime.now(timezone.utc)),
        source=event.get("source", "eskomsepush_api"),
    )


@app.get("/api/v1/status/summary")
async def get_status_summary():
    """
    Returns a simple summary of the current status.
    Designed for quick mobile app polling.
    """
    if not KAFKA_BOOTSTRAP_SERVERS:
        raise HTTPException(status_code=503, detail="Kafka not configured")

    event = get_latest_validated_event(
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS
    )

    if not event:
        raise HTTPException(
            status_code=503,
            detail="No data available"
        )

    stage = event.get("stage", 0)
    return {
        "stage": stage,
        "status": "no_load_shedding" if stage == 0 else f"stage_{stage}",
        "last_updated": event.get("timestamp"),
        "message": (
            "No load shedding currently"
            if stage == 0
            else f"Stage {stage} load shedding in effect"
        ),
    }