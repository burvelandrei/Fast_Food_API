from fastapi import APIRouter, Depends
from fastapi_cache.decorator import cache
from sqlalchemy.ext.asyncio import AsyncSession
from db.connect import get_session
from schemas.category import CategoryOut
from db.operations import CategoryDO
from utils.cache_manager import request_key_builder


router = APIRouter(prefix="/category", tags=["Category"])


# Роутер получения всех категорий
@router.get("/", response_model=list[CategoryOut])
@cache(expire=60, key_builder=request_key_builder)
async def get_category(
    session: AsyncSession = Depends(get_session),
):
    category = await CategoryDO.get_all(session=session)
    return category
