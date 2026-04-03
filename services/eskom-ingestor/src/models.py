from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class EskomStageEvent(BaseModel):
    event_id: str
    event_type: str = Field(default="eskom.stage.reading")
    timestamp: datetime
    stage: int
    stage_start_timestamp: Optional[datetime] = None
    next_stages: list = []
    source: str = Field(default="eskomsepush_api")
    schema_version: str = Field(default="1.0.0")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class IngestionError(BaseModel):
    event_id: str
    event_type: str = Field(default="ingestion.error")
    timestamp: datetime
    error_type: str
    error_message: str
    source: str
    retry_count: int = Field(default=0)