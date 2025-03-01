from redis.asyncio import Redis
from environs import Env


env = Env()
env.read_env()


async def get_redis():
    redis = Redis(host=env("REDIS_HOST"), port=env("REDIS_PORT"), decode_responses=True)
    return redis