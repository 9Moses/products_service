import json
import time
import logging
import threading
import pika
import os
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Load .env (if present) so local environment secrets can be used
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

# ── Connection settings ───────────────────────────────────────────────────────
RABBITMQ_URL = os.environ.get('RABBITMQ_URL', 'amqps://kmyhyinc:2A1RjChfIOBnbQhNLEorkQUKRO0JLyMa@capybara.lmq.cloudamqp.com/kmyhyinc')
MAX_RETRIES = 5
RETRY_DELAY = 2       # seconds between retries (doubles each attempt)
HEARTBEAT = 60        # seconds — keeps idle connections alive
BLOCKED_TIMEOUT = 300 # seconds — drop connection if RabbitMQ is resource-blocked


# ── Thread-local connection pool ──────────────────────────────────────────────
# Each thread gets its own connection + channel so there are no concurrency
# issues (pika BlockingConnection is NOT thread-safe).
_local = threading.local()


def _get_connection_params() -> pika.ConnectionParameters:
    params = pika.URLParameters(RABBITMQ_URL)
    params.heartbeat = HEARTBEAT
    params.blocked_connection_timeout = BLOCKED_TIMEOUT
    return params


def _is_connection_open(conn) -> bool:
    """Return True only if the connection object exists and is genuinely open."""
    return (
        conn is not None
        and conn.is_open
        and not conn.is_closed
    )


def _is_channel_open(ch) -> bool:
    return ch is not None and ch.is_open


def _new_connection() -> pika.BlockingConnection:
    """Open a fresh BlockingConnection with retry/back-off."""
    delay = RETRY_DELAY
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            conn = pika.BlockingConnection(_get_connection_params())
            logger.info("RabbitMQ connection established (attempt %d)", attempt)
            return conn
        except pika.exceptions.AMQPConnectionError as exc:
            logger.warning(
                "RabbitMQ connection attempt %d/%d failed: %s",
                attempt, MAX_RETRIES, exc,
            )
            if attempt == MAX_RETRIES:
                raise
            time.sleep(delay)
            delay = min(delay * 2, 30)  # exponential back-off, cap at 30 s


def _get_channel() -> pika.adapters.blocking_connection.BlockingChannel:
    """
    Return a healthy (connection, channel) pair from thread-local storage,
    re-creating either if they have gone stale.
    """
    conn = getattr(_local, "connection", None)
    ch   = getattr(_local, "channel", None)

    # Re-open connection if lost
    if not _is_connection_open(conn):
        logger.info("RabbitMQ connection is closed — reconnecting…")
        conn = _new_connection()
        _local.connection = conn
        ch = None  # force channel re-creation below

    # Re-open channel if lost
    if not _is_channel_open(ch):
        logger.info("RabbitMQ channel is closed — reopening…")
        ch = conn.channel()
        _local.channel = ch

    return ch


# ── Public API ────────────────────────────────────────────────────────────────

def publish(event: str, data: dict) -> None:
    """
    Publish *data* to the default exchange using *event* as the routing key.

    Retries once on StreamLostError / channel-closed errors by dropping the
    stale connection and opening a fresh one — covers the case where the
    connection died silently while Django was idle.
    """
    body = json.dumps({"event": event, "data": data})
    properties = pika.BasicProperties(
        content_type="application/json",
        delivery_mode=2,  # persistent — survives RabbitMQ restarts
    )

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            ch = _get_channel()

            # Declare the queue idempotently so the producer never assumes
            # the consumer has already created it.
            ch.queue_declare(queue=event, durable=True)

            ch.basic_publish(
                exchange="",
                routing_key=event,
                body=body,
                properties=properties,
            )
            logger.debug("Published event '%s'", event)
            return

        except (
            pika.exceptions.StreamLostError,
            pika.exceptions.AMQPChannelError,
            pika.exceptions.AMQPConnectionError,
            pika.exceptions.ChannelClosedByBroker,
            pika.exceptions.ConnectionClosedByBroker,
        ) as exc:
            logger.warning(
                "Publish attempt %d/%d failed (%s: %s) — resetting connection",
                attempt, MAX_RETRIES, type(exc).__name__, exc,
            )
            # Nuke the stale objects so _get_channel() rebuilds from scratch
            _local.connection = None
            _local.channel = None

            if attempt == MAX_RETRIES:
                logger.error("All %d publish attempts exhausted for event '%s'", MAX_RETRIES, event)
                raise

            time.sleep(RETRY_DELAY * attempt)


def close() -> None:
    """Cleanly close the thread-local connection (call from app shutdown hooks)."""
    conn = getattr(_local, "connection", None)
    if _is_connection_open(conn):
        try:
            conn.close()
            logger.info("RabbitMQ connection closed")
        except Exception:
            pass
    _local.connection = None
    _local.channel = None