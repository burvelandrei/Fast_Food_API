import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from environs import Env
from db.connect import get_session
from schemas.user import UserOut, UserDataTg, UserDataWeb
from db.operations import UserDO, RefreshTokenDO
from services.auth import (
    authentificate_user,
    create_access_token,
    create_refresh_token,
    get_hash_password,
    get_current_user,
)
from schemas.token import Token, RefreshTokenRequest

env = Env()
env.read_env()


SECRET_KEY = env("SECRET_KEY")
ALGORITHM = "HS256"

router = APIRouter(prefix="/users", tags=["Users"])


# Роутер регистрации пользователя
@router.post("/register/")
async def register(
    user_data: UserDataWeb | UserDataTg, session: AsyncSession = Depends(get_session)
):
    db_user = await UserDO.get_by_email(email=user_data.email, session=session)

    if db_user:
        update_fields = {}
        # Добавляем пароль пользователю если он ещё не зарегестрирован по веб но зарегистрирован по Тг
        if (
            isinstance(user_data, UserDataWeb)
            and db_user.tg_id
            and not db_user.hashed_password
        ):
            update_fields["hashed_password"] = get_hash_password(user_data.password)
        # Добавляем tg_id пользователю если он ещё не зарегестрирован по Тг через бота но зарегистрирован по веб
        elif (
            isinstance(user_data, UserDataTg)
            and db_user.hashed_password
            and not db_user.tg_id
        ):
            update_fields["tg_id"] = user_data.tg_id

        if update_fields:
            await UserDO.update(session=session, id=db_user.id, **update_fields)
        else:
            raise HTTPException(status_code=400, detail="User already registered")
    else:
        # Добавляем пользователя в зависимости от типа регистрации (веб или Тг)
        if isinstance(user_data, UserDataWeb):
            hashed_password = get_hash_password(user_data.password)
            db_user = await UserDO.add(
                session=session, email=user_data.email, hashed_password=hashed_password
            )
        elif isinstance(user_data, UserDataTg):
            db_user = await UserDO.add(session=session, **user_data.__dict__)
    # Пользователю веб возвращаем access и refresh токены
    if isinstance(user_data, UserDataWeb):
        access_token = create_access_token(data={"email": user_data.email})
        refresh_token = create_refresh_token(data={"email": user_data.email})
        await RefreshTokenDO.add(
            session=session, user_id=db_user.id, refresh_token=refresh_token
        )
        return Token(
            access_token=access_token, refresh_token=refresh_token, token_type="bearer"
        )
    # Пользователю Тг возвращаем ответ об успешной регистрации
    return JSONResponse(
        content={"message": "User is registered"},
        status_code=201,
    )


# Роутер входа пользователя
@router.post("/login/")
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


# Роутер выхода пользователя
@router.post("/logout/")
async def logout_user(
    user: UserOut = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    await RefreshTokenDO.delete_by_user_id(session=session, user_id=user.id)

    return JSONResponse(
        content={"message": "Successfully logged out"},
        status_code=200,
    )


# Роутер обновления access токена
@router.post("/token/refresh/")
async def refresh_access_token(
    token_data: RefreshTokenRequest,
    session: AsyncSession = Depends(get_session),
):
    invalid_refresh_token_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
    )

    try:
        payload = jwt.decode(
            token_data.refresh_token, SECRET_KEY, algorithms=[ALGORITHM]
        )
        email = payload.get("email")
        if email is None:
            raise invalid_refresh_token_exception

        db_refresh_token = await RefreshTokenDO.get_by_refresh_token(
            refresh_token=token_data.refresh_token, session=session
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
