import aio_pika
import json
from config import settings


# Функция для публикации в rabbitmq информации об успешном подтверждении почты
async def publish_confirmations(event_data: dict):
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
