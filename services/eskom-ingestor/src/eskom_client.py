import uuid
from datetime import datetime, timezone
from typing import Optional
import requests
import structlog
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)
from models import EskomStageEvent

logger = structlog.get_logger(__name__)

ESKOMSEPUSH_BASE_URL = "https://developer.sepush.co.za/business/2.0"


class EskomSePushClient:

    def __init__(self, api_token: str):
        self.api_token = api_token
        self.session = requests.Session()
        self.session.headers.update({
            "Token": self.api_token,
            "Content-Type": "application/json",
        })
        logger.info("eskom_client_initialized")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type(requests.RequestException),
    )
    def get_current_status(self) -> Optional[EskomStageEvent]:
        try:
            logger.info("fetching_eskom_status")

            response = self.session.get(
                f"{ESKOMSEPUSH_BASE_URL}/status",
                timeout=30
            )
            response.raise_for_status()
            data = response.json()

            status = data.get("status", {})
            eskom_data = status.get("eskom", {})

            stage_str = eskom_data.get("stage", "0")
            stage = int(stage_str.replace("Stage ", "").strip() or 0)

            event = EskomStageEvent(
                event_id=str(uuid.uuid4()),
                timestamp=datetime.now(timezone.utc),
                stage=stage,
                next_stages=eskom_data.get("next_stages", []),
                stage_start_timestamp=self._parse_timestamp(
                    eskom_data.get("stage_start_timestamp")
                ),
            )

            logger.info(
                "eskom_status_fetched",
                stage=stage,
                event_id=event.event_id
            )
            return event

        except requests.RequestException as e:
            logger.error(
                "eskom_api_request_failed",
                error=str(e),
                error_type=type(e).__name__
            )
            raise

        except (KeyError, ValueError) as e:
            logger.error(
                "eskom_response_parse_failed",
                error=str(e),
            )
            return None

    def _parse_timestamp(self, ts_str: Optional[str]) -> Optional[datetime]:
        if not ts_str:
            return None
        try:
            return datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            return None