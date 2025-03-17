import jwt
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi_cache.decorator import cache
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis
from db.connect import get_session
from schemas.user import UserOut, UserDataTg, UserDataWeb
from db.operations import UserDO
from services.auth import (
    authentificate_user,
    create_access_token,
    create_refresh_token,
    get_hash_password,
    get_current_user,
    create_email_confirmation_token,
    verify_email_confirmation_token,
)
from schemas.token import Token, RefreshTokenRequest
from utils.redis_connect import get_redis
from utils.send_email import send_confirmation_email
from utils.rmq_producer import publish_confirmations
from utils.cache_manager import request_key_builder
from config import settings


router = APIRouter(prefix="/users", tags=["Users"])


# Роутер для регистрации пользователя
@router.post("/register/")
async def register(
    user_data: UserDataWeb | UserDataTg,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_session),
    redis: Redis = Depends(get_redis),
):
    confirmation_token = create_email_confirmation_token(user_data.email)
    db_user = await UserDO.get_by_email(
        email=user_data.email,
        session=session,
    )

    if db_user:
        update_fields = {}
        if (
            isinstance(user_data, UserDataWeb)
            and db_user.tg_id
            and not db_user.hashed_password
        ):
            update_fields["hashed_password"] = (
                get_hash_password(user_data.password)
            )
        elif (
            isinstance(user_data, UserDataTg)
            and db_user.hashed_password
            and not db_user.tg_id
        ):
            update_fields["tg_id"] = user_data.tg_id

        if update_fields:
            update_fields["email"] = user_data.email
            await redis.hset(
                f"confirm:{confirmation_token}",
                mapping=update_fields
            )
            await redis.expire(f"confirm:{confirmation_token}", 30*60)
        else:
            raise HTTPException(
                status_code=400,
                detail="User already registered"
            )
    else:
        if isinstance(user_data, UserDataWeb):
            hashed_password = get_hash_password(user_data.password)
            await redis.hset(
                f"confirm:{confirmation_token}",
                mapping={
                    "email": user_data.email,
                    "hashed_password": hashed_password,
                },
            )
        elif isinstance(user_data, UserDataTg):
            await redis.hset(
                f"confirm:{confirmation_token}", mapping=user_data.__dict__
            )
        await redis.expire(f"confirm:{confirmation_token}", 30*60)
    background_tasks.add_task(
        send_confirmation_email,
        user_data.email,
        confirmation_token,
    )
    return JSONResponse(
        content={"message": "Check your email to confirm registration."},
        status_code=200,
    )


# Роутер подтверждения почты по токену
@router.get("/confirm-email/{token}/")
async def confirmation_email(
    token: str,
    session: AsyncSession = Depends(get_session),
    redis: Redis = Depends(get_redis),
):
    email = verify_email_confirmation_token(token)
    user_data = await redis.hgetall(f"confirm:{token}")

    if not email or not user_data:
        raise HTTPException(
            status_code=400,
            detail="Invalid or expired token",
        )

    db_user = await UserDO.get_by_email(
        email=user_data["email"],
        session=session,
    )

    if db_user and db_user.hashed_password and db_user.tg_id:
        raise HTTPException(
            status_code=400,
            detail="Email already confirmed",
        )

    if not db_user:
        await UserDO.add(session=session, **user_data)
    else:
        if "hashed_password" in user_data:
            await UserDO.update(
                session=session,
                id=db_user.id,
                **{"hashed_password": user_data["hashed_password"]},
            )
        if "tg_id" in user_data:
            await UserDO.update(
                session=session,
                id=db_user.id,
                **{"tg_id": user_data["tg_id"]},
            )

    await redis.delete(f"confirm:{token}")

    if "hashed_password" in user_data:
        access_token = create_access_token(
            data={"email": user_data["email"]},
            secret_key=settings.SECRET_KEY,
        )
        refresh_token = create_refresh_token(
            data={"email": user_data["email"]},
            secret_key=settings.SECRET_KEY,
        )
        return JSONResponse(
            content={
                "message": "Email successfully confirmed!",
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer",
            },
            status_code=200,
        )
    if "tg_id" in user_data:
        await publish_confirmations(
            {
                "event": "user_confirmed",
                "email": user_data["email"],
                "tg_id": user_data["tg_id"],
            }
        )
        return JSONResponse(
            content={"message": "Email successfully confirmed!"},
            status_code=200,
        )


# Роутер входа пользователя
@router.post("/login/")
async def login_user(
    user_web: UserDataWeb,
    session: AsyncSession = Depends(get_session),
):
    user = await authentificate_user(
        user_web.email,
        user_web.password,
        session,
        )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(
        data={"email": user.email}, secret_key=settings.SECRET_KEY
    )
    refresh_token = create_refresh_token(
        data={"email": user.email}, secret_key=settings.SECRET_KEY
    )
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
    )


# Роутер выхода пользователя
@router.post("/logout/")
async def logout_user(
    user: UserOut = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    return JSONResponse(
        content={"message": "Successfully logged out"},
        status_code=200,
    )


# Роутер профиля пользователя
@router.get("/profile/", response_model=UserOut)
@cache(expire=60, key_builder=request_key_builder)
async def get_profile(user: UserOut = Depends(get_current_user)):
    return user


# Роутер обновления access токена
@router.post("/token/refresh/")
async def refresh_access_token(
    token_data: RefreshTokenRequest,
    session: AsyncSession = Depends(get_session),
):
    invalid_refresh_token_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid refresh token",
    )

    try:
        payload = jwt.decode(
            token_data.refresh_token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        email = payload.get("email")
        if email is None:
            raise invalid_refresh_token_exception
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has expired",
        )
    except jwt.PyJWTError:
        raise invalid_refresh_token_exception

    new_access_token = create_access_token(
        data={"email": email},
        secret_key=settings.SECRET_KEY,
    )
    return {"access_token": new_access_token, "token_type": "bearer"}
