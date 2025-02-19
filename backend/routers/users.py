from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from db.connect import get_session
from schemas.user import UserOut, UserCreateTg
from db.operations import UserDO
from dependencies import verify_api_key


router = APIRouter(prefix="/users", tags=["Users"])


@router.post("/", response_model=UserOut)
async def create_user_tg(
    user_tg: UserCreateTg,
    session: AsyncSession = Depends(get_session),
    api_key: str = Depends(verify_api_key),
):
    new_user = await UserDO.add(session=session, **user_tg.__dict__)
    return new_user