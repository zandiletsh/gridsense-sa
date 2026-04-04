# src/models.py
# API response models for GridSense API Gateway

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List


class LoadSheddingStatus(BaseModel):
    """Current national load shedding status."""
    stage: int = Field(description="Current stage 0-8")
    stage_since: Optional[datetime] = Field(
        default=None,
        description="When this stage started"
    )
    next_stages: List[dict] = Field(
        default=[],
        description="Upcoming stage changes"
    )
    last_updated: datetime = Field(
        description="When this data was last fetched"
    )
    source: str = Field(default="eskomsepush_api")


class HealthResponse(BaseModel):
    """Service health check response."""
    status: str = Field(default="healthy")
    service: str = Field(default="gridsense-api-gateway")
    version: str = Field(default="1.0.0")
    timestamp: datetime


class ErrorResponse(BaseModel):
    """Standard error response."""
    error: str
    message: str
    timestamp: datetime