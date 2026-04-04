# src/main.py
# Data Validator service.
# Consumes raw events from Kafka, validates them,
# and routes to validated or dead-letter topics.

import os
import json
import signal
import sys
import uuid
from datetime import datetime, timezone
from kafka import KafkaConsumer, KafkaProducer
from kafka.errors import KafkaError
import structlog
from dotenv import load_dotenv
from validator import validate_eskom_event

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
KAFKA_BOOTSTRAP_SERVERS    = os.getenv("KAFKA_BOOTSTRAP_SERVERS")
SOURCE_TOPIC               = os.getenv("SOURCE_TOPIC", "eskom.generation.raw")
VALIDATED_TOPIC            = os.getenv("VALIDATED_TOPIC", "eskom.generation.validated")
DEAD_LETTER_TOPIC          = os.getenv("DEAD_LETTER_TOPIC", "eskom.generation.deadletter")
CONSUMER_GROUP_ID          = os.getenv("CONSUMER_GROUP_ID", "data-validator-group")

# ── Graceful shutdown ──────────────────────────────────────────────
shutdown_requested = False

def handle_shutdown(signum, frame):
    global shutdown_requested
    logger.info("shutdown_signal_received", signal=signum)
    shutdown_requested = True

signal.signal(signal.SIGTERM, handle_shutdown)
signal.signal(signal.SIGINT, handle_shutdown)


def validate_config():
    if not KAFKA_BOOTSTRAP_SERVERS:
        logger.error("missing_required_config",
                     missing=["KAFKA_BOOTSTRAP_SERVERS"])
        sys.exit(1)


def create_consumer() -> KafkaConsumer:
    return KafkaConsumer(
        SOURCE_TOPIC,
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS.split(","),
        group_id=CONSUMER_GROUP_ID,
        value_deserializer=lambda v: json.loads(v.decode("utf-8")),
        auto_offset_reset="earliest",
        enable_auto_commit=False,
        max_poll_records=10,
    )


def create_producer() -> KafkaProducer:
    return KafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS.split(","),
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        key_serializer=lambda k: k.encode("utf-8") if k else None,
        acks="all",
        retries=3,
    )


def publish_event(
    producer: KafkaProducer,
    topic: str,
    event: dict,
    key: str = None
) -> bool:
    try:
        future = producer.send(topic, value=event, key=key)
        future.get(timeout=10)
        return True
    except KafkaError as e:
        logger.error("publish_failed", topic=topic, error=str(e))
        return False


def run():
    validate_config()

    logger.info(
        "data_validator_starting",
        source_topic=SOURCE_TOPIC,
        validated_topic=VALIDATED_TOPIC,
        dead_letter_topic=DEAD_LETTER_TOPIC,
        consumer_group=CONSUMER_GROUP_ID,
    )

    consumer = create_consumer()
    producer = create_producer()

    try:
        while not shutdown_requested:
            # Poll for messages (wait up to 1 second)
            records = consumer.poll(timeout_ms=1000)

            if not records:
                continue

            for topic_partition, messages in records.items():
                for message in messages:
                    event = message.value

                    logger.info(
                        "event_received",
                        topic=message.topic,
                        partition=message.partition,
                        offset=message.offset,
                        event_id=event.get("event_id"),
                    )

                    # Validate the event
                    is_valid, error_reason = validate_eskom_event(event)

                    if is_valid:
                        # Add validation metadata
                        event["validated_at"] = datetime.now(
                            timezone.utc
                        ).isoformat()
                        event["validator_version"] = "1.0.0"

                        # Publish to validated topic
                        success = publish_event(
                            producer,
                            VALIDATED_TOPIC,
                            event,
                            key=event.get("event_id")
                        )

                        if success:
                            logger.info(
                                "event_validated",
                                event_id=event.get("event_id"),
                                stage=event.get("stage"),
                            )

                    else:
                        # Publish to dead-letter topic for investigation
                        dead_letter_event = {
                            "original_event": event,
                            "error_reason": error_reason,
                            "dead_lettered_at": datetime.now(
                                timezone.utc
                            ).isoformat(),
                            "dead_letter_id": str(uuid.uuid4()),
                        }

                        publish_event(
                            producer,
                            DEAD_LETTER_TOPIC,
                            dead_letter_event,
                            key=event.get("event_id")
                        )

                        logger.warning(
                            "event_dead_lettered",
                            event_id=event.get("event_id"),
                            error_reason=error_reason,
                        )

                    # Commit offset after processing
                    # This ensures we don't reprocess on restart
                    consumer.commit()

    finally:
        logger.info("data_validator_shutting_down")
        producer.flush()
        producer.close()
        consumer.close()


if __name__ == "__main__":
    run()