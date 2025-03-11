import aio_pika
import json
from environs import Env


env = Env()
env.read_env()


# Функция для публикации в rabbitmq информации об успешном подтверждении почты
async def publish_confirmations(event_data: dict):
    connection = await aio_pika.connect_robust(
        f"amqp://{env('RMQ_USER')}:{env('RMQ_PASSWORD')}@localhost/"
    )
    channel = await connection.channel()
    await channel.default_exchange.publish(
        aio_pika.Message(body=json.dumps(event_data).encode()),
        routing_key="user_confirmations",
    )
    await connection.close()
