# src/kafka_consumer.py
# Reads the latest validated event from Kafka.
# Used to serve the current status endpoint.

import json
from typing import Optional
from kafka import KafkaConsumer
import structlog

logger = structlog.get_logger(__name__)


def get_latest_validated_event(
    bootstrap_servers: str,
    topic: str = "eskom.generation.validated"
) -> Optional[dict]:
    """
    Reads the most recent validated event from Kafka.
    Uses a temporary consumer that reads from the end of the topic.
    """
    try:
        consumer = KafkaConsumer(
            topic,
            bootstrap_servers=bootstrap_servers.split(","),
            auto_offset_reset="latest",
            enable_auto_commit=False,
            consumer_timeout_ms=5000,
            value_deserializer=lambda v: json.loads(v.decode("utf-8")),
        )

        # Seek to end and get the last message
        consumer.poll(timeout_ms=1000)
        consumer.seek_to_end()

        # Go back one offset to read the latest message
        latest_event = None
        for partition in consumer.assignment():
            end_offset = consumer.end_offsets([partition])[partition]
            if end_offset > 0:
                consumer.seek(partition, end_offset - 1)
                for message in consumer:
                    latest_event = message.value
                    break

        consumer.close()

        if latest_event:
            logger.info(
                "latest_event_fetched",
                stage=latest_event.get("stage"),
                event_id=latest_event.get("event_id"),
            )

        return latest_event

    except Exception as e:
        logger.error("kafka_read_failed", error=str(e))
        return None