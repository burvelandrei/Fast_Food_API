from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from db.connect import get_session
from schemas.category import CategoryOut
from db.operations import CategoryDO
from dependencies import verify_api_key


router = APIRouter(prefix="/category", tags=["Category"])


@router.get("/", response_model=list[CategoryOut])
async def get_category(
    session: AsyncSession = Depends(get_session),
    api_key: str = Depends(verify_api_key),
):
    category = await CategoryDO.get_all(session=session)
    return category
