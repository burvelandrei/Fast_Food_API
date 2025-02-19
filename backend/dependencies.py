from fastapi import Depends, HTTPException
from fastapi.security import APIKeyHeader
from environs import Env
from sqlalchemy.ext.asyncio import AsyncSession
from db.connect import get_session


env = Env()
env.read_env()


API_KEY_BOT = env("API_KEY_BOT")

api_key_header = APIKeyHeader(name="X-API-Key")


async def verify_api_key(api_key: str = Depends(api_key_header)):
    if api_key != API_KEY_BOT:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return api_key