import json
import logging
import pika
from main import app, Product, db 


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def handle_product_created(data: dict) -> None:
    """Insert a new product row, skip if it already exists (idempotent)."""
    with app.app_context():
        # SQLAlchemy 2.0-style lookup
        existing = db.session.get(Product, data["id"])
        if existing:
            logger.info("product_created: product %s already exists — skipping", data["id"])
            return

        product = Product()
        product.id     = data["id"]
        product.title  = data["title"]
        product.image  = data.get("image", "")
        product.likes  = data.get("likes", 0)

        db.session.add(product)
        db.session.commit()
        logger.info("product_created: inserted product %s ('%s')", product.id, product.title)


def handle_product_updated(data: dict) -> None:
    """
    Update an existing product.  If the row doesn't exist yet (consumer DB is
    behind), insert it so the databases stay consistent.
    """
    with app.app_context():
        product = db.session.get(Product, data["id"])   # SQLAlchemy 2.0 API

        if product is None:
            # The consumer DB doesn't have this product yet — create it.
            logger.warning(
                "product_updated: product %s not found locally — inserting instead",
                data["id"],
            )
            product = Product()
            product.id = data["id"]
            db.session.add(product)

        product.title = data.get("title", product.title)
        product.image = data.get("image", product.image)
        product.likes = data.get("likes", product.likes)

        db.session.commit()
        logger.info("product_updated: synced product %s ('%s')", product.id, product.title)


def handle_product_deleted(data: dict) -> None:
    with app.app_context():
        product = db.session.get(Product, data["id"])
        if product is None:
            logger.warning("product_deleted: product %s not found — already gone", data["id"])
            return

        db.session.delete(product)
        db.session.commit()
        logger.info("product_deleted: removed product %s", data["id"])


# ── Event router ──────────────────────────────────────────────────────────────

HANDLERS = {
    "product_created": handle_product_created,
    "product_updated": handle_product_updated,
    "product_deleted": handle_product_deleted,
}


def callback(ch, method, properties, body: bytes) -> None:
    try:
        payload = json.loads(body)
        logger.info("Received: %s", payload)

        event = payload.get("event")
        data  = payload.get("data", payload)  # fallback: treat whole payload as data

        handler = HANDLERS.get(event)
        if handler is None:
            logger.warning("No handler registered for event '%s'", event)
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return

        handler(data)
        ch.basic_ack(delivery_tag=method.delivery_tag)

    except Exception as exc:
        logger.exception("Failed to process message: %s", exc)
        # Reject without requeue — prevents poison-message infinite loop.
        # Change to requeue=True if you want retry behaviour.
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)


def main() -> None:
    params = pika.URLParameters("amqps://kmyhyinc:2A1RjChfIOBnbQhNLEorkQUKRO0JLyMa@capybara.lmq.cloudamqp.com/kmyhyinc")
    params.heartbeat = 60
    params.blocked_connection_timeout = 300

    connection = pika.BlockingConnection(params)
    channel    = connection.channel()

    # Declare all queues the consumer cares about
    for queue_name in HANDLERS:
        channel.queue_declare(queue=queue_name, durable=True)

    # Fair dispatch — don't give a worker more than 1 unacked message at a time
    channel.basic_qos(prefetch_count=1)

    for queue_name in HANDLERS:
        channel.basic_consume(queue=queue_name, on_message_callback=callback)

    logger.info("Consumer ready — waiting for messages")
    channel.start_consuming()


if __name__ == "__main__":
    main()