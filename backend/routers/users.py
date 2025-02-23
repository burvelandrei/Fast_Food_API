from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated
from db.connect import get_session
from schemas.user import UserOut, UserCreateTg, UserCreateWeb
from db.operations import UserDO
from dependencies import verify_api_key
from services.auth import (
    authentificate_user,
    create_access_token,
    create_refresh_token,
    get_hash_password,
)
from schemas.token import Token


router = APIRouter(prefix="/users", tags=["Users"])


@router.post("/", response_model=UserOut)
async def create_user_tg(
    user_tg: UserCreateTg,
    session: AsyncSession = Depends(get_session),
    api_key: str = Depends(verify_api_key),
):
    new_user = await UserDO.add(session=session, **user_tg.__dict__)
    return new_user


@router.post("/register", response_model=UserOut)
async def register(
    user_web: UserCreateWeb, session: AsyncSession = Depends(get_session)
):
    db_user = await UserDO.get_by_email(email=user_web.email, session=session)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_password = get_hash_password(user_web.password)
    new_user = await UserDO.add(
        session=session,
        **{
            "username": user_web.username,
            "hashed_password": hashed_password,
            "email": user_web.email,
        }
    )
    return new_user


@router.post("/login")
async def login_user(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    session: AsyncSession = Depends(get_session),
):
    user = await authentificate_user(form_data.username, form_data.password, session)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user.email})
    refresh_token = create_refresh_token(data={"sub": user.email})
    return Token(
        access_token=access_token, refresh_token=refresh_token, token_type="bearer"
    )
