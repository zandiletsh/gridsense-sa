# src/validator.py
# Validation rules for GridSense events.
# Each validator returns (is_valid, error_reason)

from datetime import datetime, timezone, timedelta
from typing import Tuple, Optional
import structlog

logger = structlog.get_logger(__name__)

# Maximum age of an event before we consider it stale
MAX_EVENT_AGE_MINUTES = 30

# Valid load shedding stage range
MIN_STAGE = 0
MAX_STAGE = 8


def validate_eskom_event(event: dict) -> Tuple[bool, Optional[str]]:
    """
    Validates a raw Eskom stage event.

    Returns:
        (True, None) if valid
        (False, reason) if invalid
    """

    # Rule 1 — Required fields must exist
    required_fields = [
        "event_id", "event_type", "timestamp",
        "stage", "source", "schema_version"
    ]
    for field in required_fields:
        if field not in event:
            return False, f"missing_required_field:{field}"

    # Rule 2 — Stage must be a valid integer in range 0-8
    try:
        stage = int(event["stage"])
        if not MIN_STAGE <= stage <= MAX_STAGE:
            return False, f"stage_out_of_range:{stage}"
    except (ValueError, TypeError):
        return False, f"stage_not_integer:{event.get('stage')}"

    # Rule 3 — Timestamp must be a valid ISO datetime
    try:
        event_time = datetime.fromisoformat(
            str(event["timestamp"]).replace("Z", "+00:00")
        )
    except (ValueError, TypeError):
        return False, f"invalid_timestamp:{event.get('timestamp')}"

    # Rule 4 — Event must not be stale (older than 30 minutes)
    now = datetime.now(timezone.utc)
    age = now - event_time
    if age > timedelta(minutes=MAX_EVENT_AGE_MINUTES):
        return False, f"event_too_old:{age.total_seconds():.0f}s"

    # Rule 5 — Event must not be from the future
    if event_time > now + timedelta(minutes=5):
        return False, f"event_from_future:{event_time.isoformat()}"

    # Rule 6 — Source must be known
    known_sources = ["eskomsepush_api", "eskom_data_portal", "manual"]
    if event.get("source") not in known_sources:
        return False, f"unknown_source:{event.get('source')}"

    # Rule 7 — event_id must be present and non-empty
    if not event.get("event_id", "").strip():
        return False, "empty_event_id"

    logger.debug(
        "event_validation_passed",
        event_id=event.get("event_id"),
        stage=stage,
    )
    return True, None