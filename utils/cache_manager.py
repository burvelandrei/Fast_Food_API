from fastapi import FastAPI
from contextlib import asynccontextmanager
from utils.redis_connect import get_redis
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend


@asynccontextmanager
async def lifespan(_:FastAPI):
    redis_client = await get_redis()
    FastAPICache.init(RedisBackend(redis_client), prefix="fastapi-cache")
    yield