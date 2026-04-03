import os
import time
import signal
import sys
import structlog
from dotenv import load_dotenv
from eskom_client import EskomSePushClient
from kafka_producer import GridSenseProducer

load_dotenv()

structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.add_log_level,
        structlog.processors.JSONRenderer(),
    ]
)

logger = structlog.get_logger(__name__)

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS")
ESKOMSEPUSH_API_TOKEN   = os.getenv("ESKOMSEPUSH_API_TOKEN")
POLL_INTERVAL_SECONDS   = int(os.getenv("POLL_INTERVAL_SECONDS", "300"))
KAFKA_TOPIC             = os.getenv("KAFKA_TOPIC", "eskom.generation.raw")

shutdown_requested = False

def handle_shutdown(signum, frame):
    global shutdown_requested
    logger.info("shutdown_signal_received", signal=signum)
    shutdown_requested = True

signal.signal(signal.SIGTERM, handle_shutdown)
signal.signal(signal.SIGINT, handle_shutdown)


def validate_config():
    missing = []
    if not KAFKA_BOOTSTRAP_SERVERS:
        missing.append("KAFKA_BOOTSTRAP_SERVERS")
    if not ESKOMSEPUSH_API_TOKEN:
        missing.append("ESKOMSEPUSH_API_TOKEN")
    if missing:
        logger.error("missing_required_config", missing=missing)
        sys.exit(1)


def run():
    validate_config()

    logger.info(
        "eskom_ingestor_starting",
        poll_interval=POLL_INTERVAL_SECONDS,
        kafka_topic=KAFKA_TOPIC,
    )

    eskom_client = EskomSePushClient(api_token=ESKOMSEPUSH_API_TOKEN)
    producer = GridSenseProducer(bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS)

    try:
        while not shutdown_requested:
            logger.info("poll_cycle_starting")

            event = eskom_client.get_current_status()

            if event:
                event_dict = event.model_dump(mode="json")

                success = producer.publish(
                    topic=KAFKA_TOPIC,
                    event=event_dict,
                    key="eskom_national"
                )

                if success:
                    logger.info(
                        "poll_cycle_complete",
                        stage=event.stage,
                        next_poll_seconds=POLL_INTERVAL_SECONDS
                    )
                else:
                    logger.warning("poll_cycle_publish_failed")
            else:
                logger.warning("poll_cycle_no_data")

            for _ in range(POLL_INTERVAL_SECONDS):
                if shutdown_requested:
                    break
                time.sleep(1)

    finally:
        logger.info("eskom_ingestor_shutting_down")
        producer.close()


if __name__ == "__main__":
    run()