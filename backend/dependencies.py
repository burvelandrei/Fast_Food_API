from redis.asyncio import Redis
from fastapi import Depends, HTTPException
from fastapi.security import APIKeyHeader
from environs import Env
from sqlalchemy.ext.asyncio import AsyncSession
from db.connect import get_session


env = Env()
env.read_env()


api_key_header = APIKeyHeader(name="X-API-Key")


async def verify_api_key(api_key: str = Depends(api_key_header)):
    if api_key != env("API_KEY_BOT"):
        raise HTTPException(status_code=403, detail="Invalid API key")
    return api_key


async def get_redis():
    redis = Redis(host=env("REDIS_HOST"), port=env("REDIS_PORT"), decode_responses=True)
    return redis