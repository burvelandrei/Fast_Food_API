import aio_pika
import json
import logging
import logging.config
from utils.logger import logging_config
from config import settings


logging.config.dictConfig(logging_config)
logger = logging.getLogger("rabbit_producer")


# Функция для публикации в rabbitmq информации об успешном подтверждении почты
async def publish_confirmations(event_data: dict):
    try:
        connection = await aio_pika.connect_robust(
            f"amqp://{settings.RMQ_USER}:{settings.RMQ_PASSWORD}@"
            f"{settings.RMQ_HOST}:{settings.RMQ_PORT}/"
        )
        channel = await connection.channel()
        await channel.default_exchange.publish(
            aio_pika.Message(body=json.dumps(event_data).encode()),
            routing_key="user_confirmations",
        )
        await connection.close()
        logger.info("Message published")
    except Exception as e:
        logger.error(
            f"Failed to publish message to RabbitMQ: {e}",
            exc_info=True,
        )
