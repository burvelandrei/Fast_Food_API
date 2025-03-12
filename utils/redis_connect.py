from redis.asyncio import Redis
from config import settings


async def get_redis():
    redis = Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        decode_responses=False,
    )
    return redis
