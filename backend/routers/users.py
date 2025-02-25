from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated
from db.connect import get_session
from schemas.user import UserOut, UserDataTg, UserDataWeb
from db.operations import UserDO, RefreshTokenDO
from services.auth import (
    authentificate_user,
    create_access_token,
    create_refresh_token,
    get_hash_password,
    refresh_access,
    tg_relogin
)
from schemas.token import Token


router = APIRouter(prefix="/users", tags=["Users"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@router.post("/register")
async def register(user_web: UserDataWeb, session: AsyncSession = Depends(get_session)):
    db_user = await UserDO.get_by_email(email=user_web.email, session=session)
    if db_user:
        if db_user.tg_id and len(db_user.hashed_password) != 0:
            raise HTTPException(status_code=400, detail="User already registered")
        else:
            hashed_password = get_hash_password(user_web.password)
            changed_user = await UserDO.update(
                session=session, id=db_user.id, **{"hashed_password": hashed_password}
            )
            user = UserOut(changed_user)
    else:
        hashed_password = get_hash_password(user_web.password)
        new_user = await UserDO.add(
            session=session,
            **{
                "email": user_web.email,
                "hashed_password": hashed_password,
            }
        )
        user = UserOut(changed_user)
    access_token = create_access_token(data={"sub": user_web.email}, auth_type="web")
    refresh_token = create_refresh_token(data={"sub": user_web.email}, auth_type="web")
    await RefreshTokenDO.add(session=session, **{"user_id": user.id, "refresh_token": refresh_token, "auth_type": "web"})
    return Token(
        access_token=access_token, refresh_token=refresh_token, token_type="bearer"
    )


@router.post("/login")
async def login_user(
    user_web: UserDataWeb,
    session: AsyncSession = Depends(get_session),
):
    user = await authentificate_user(user_web.email, user_web.password, session)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user.email}, auth_type="web")
    refresh_token = create_refresh_token(data={"sub": user.email}, auth_type="web")
    return Token(
        access_token=access_token, refresh_token=refresh_token, token_type="bearer"
    )


@router.post("/tg_register")
async def tg_register(
    user_tg: UserDataTg, session: AsyncSession = Depends(get_session)
):
    db_user = await UserDO.get_by_email(email=user_tg.email, session=session)
    if db_user:
        if db_user.tg_id and len(db_user.hashed_password) != 0:
            raise HTTPException(status_code=400, detail="User already registered")
        else:
            changed_user = await UserDO.update(
                session=session, id=db_user.id, **{"tg_id": user_tg.tg_id}
            )
            user = UserOut(changed_user)

    else:
        new_user = await UserDO.add(session=session, **user_tg.__dict__)
        user = UserOut(changed_user)
    access_token = create_access_token(data={"sub": user_tg.email}, auth_type="tg")
    refresh_token = create_refresh_token(data={"sub": user_tg.email}, auth_type="tg")
    await RefreshTokenDO.add(session=session, **{"user_id": user.id, "refresh_token": refresh_token, "auth_type": "tg"})
    return Token(
        access_token=access_token,  refresh_token=refresh_token, token_type="bearer"
    )


@router.post("/token/refresh")
async def refresh_access_token(refresh_token: Annotated[str, Depends(oauth2_scheme)]):
    return await refresh_access(refresh_token)


@router.post("/token/tg_relogin")
async def tg_relogin_user(refresh_token: Annotated[str, Depends(oauth2_scheme)]):
    return await tg_relogin(refresh_token)
