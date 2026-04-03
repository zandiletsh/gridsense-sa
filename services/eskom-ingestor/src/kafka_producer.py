import json
import uuid
from datetime import datetime, timezone
from kafka import KafkaProducer
from kafka.errors import KafkaError
import structlog

logger = structlog.get_logger(__name__)


class GridSenseProducer:

    def __init__(self, bootstrap_servers: str):
        self.bootstrap_servers = bootstrap_servers
        self.producer = self._create_producer()
        logger.info(
            "kafka_producer_initialized",
            bootstrap_servers=bootstrap_servers
        )

    def _create_producer(self) -> KafkaProducer:
        return KafkaProducer(
            bootstrap_servers=self.bootstrap_servers.split(","),
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
            key_serializer=lambda k: k.encode("utf-8") if k else None,
            acks="all",
            retries=3,
            batch_size=16384,
            linger_ms=10,
            compression_type="gzip",
        )

    def publish(self, topic: str, event: dict, key: str = None) -> bool:
        try:
            event["published_at"] = datetime.now(timezone.utc).isoformat()
            event["message_id"] = str(uuid.uuid4())

            future = self.producer.send(topic, value=event, key=key)
            record_metadata = future.get(timeout=10)

            logger.info(
                "event_published",
                topic=topic,
                partition=record_metadata.partition,
                offset=record_metadata.offset,
                key=key,
            )
            return True

        except KafkaError as e:
            logger.error(
                "kafka_publish_failed",
                topic=topic,
                error=str(e),
                key=key,
            )
            return False

    def close(self):
        self.producer.flush()
        self.producer.close()
        logger.info("kafka_producer_closed")