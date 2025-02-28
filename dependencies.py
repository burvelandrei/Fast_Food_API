from redis.asyncio import Redis
from fastapi import Depends, HTTPException
from fastapi.security import APIKeyHeader
from environs import Env
from sqlalchemy.ext.asyncio import AsyncSession
from db.connect import get_session


env = Env()
env.read_env()


async def get_redis():
    redis = Redis(host=env("REDIS_HOST"), port=env("REDIS_PORT"), decode_responses=True)
    return redis