import jwt
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from environs import Env
from typing import Annotated
from db.connect import get_session
from schemas.user import UserOut, UserDataTg, UserDataWeb
from db.operations import UserDO, RefreshTokenDO
from services.auth import (
    authentificate_user,
    create_access_token,
    create_refresh_token,
    get_hash_password,
)
from schemas.token import Token

env = Env()
env.read_env()


SECRET_KEY = env("SECRET_KEY")
ALGORITHM = "HS256"

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
            user = UserOut(**changed_user.__dict__)
    else:
        hashed_password = get_hash_password(user_web.password)
        new_user = await UserDO.add(
            session=session,
            **{
                "email": user_web.email,
                "hashed_password": hashed_password,
            }
        )
        user = UserOut(**new_user.__dict__)
    access_token = create_access_token(data={"email": user_web.email})
    refresh_token = create_refresh_token(data={"email": user_web.email})
    await RefreshTokenDO.add(
        session=session, **{"user_id": user.id, "refresh_token": refresh_token}
    )
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
    access_token = create_access_token(data={"email": user.email})
    refresh_token = create_refresh_token(data={"email": user.email})
    await RefreshTokenDO.update_refresh_token(
        session=session, user_id=user.id, refresh_token=refresh_token
    )
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
            await UserDO.update(
                session=session, id=db_user.id, **{"tg_id": user_tg.tg_id}
            )

    else:
        await UserDO.add(session=session, **user_tg.__dict__)
    return Response(content="User is registered", status_code=201)


@router.post("/token/refresh")
async def refresh_access_token(
    refresh_token: Annotated[str, Depends(oauth2_scheme)],
    session: AsyncSession = Depends(get_session),
):
    invalid_refresh_token_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
    )

    try:
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("email")
        if email is None:
            raise invalid_refresh_token_exception

        db_refresh_token = await RefreshTokenDO.get_by_refresh_token(
            refresh_token=refresh_token, session=session
        )
        if db_refresh_token is None:
            raise invalid_refresh_token_exception

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token has expired"
        )
    except jwt.PyJWTError:
        raise invalid_refresh_token_exception

    new_access_token = create_access_token(data={"email": email})
    return {"access_token": new_access_token, "token_type": "bearer"}
