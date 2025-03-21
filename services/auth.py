import jwt
from datetime import datetime, timedelta
from fastapi import HTTPException, Depends, status
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer

from itsdangerous import URLSafeTimedSerializer
from sqlalchemy.ext.asyncio import AsyncSession
from db.connect import get_session
from schemas.token import TokenData
from db.operations import UserDO
from config import settings


ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def verify_password(plain_password, hashed_password):
    """Функция проверки захэшированного пароля"""
    return pwd_context.verify(plain_password, hashed_password)


def get_hash_password(password):
    """Функция хэширования пароля"""
    return pwd_context.hash(password)


async def authentificate_user(
    email: str, password: str, session: AsyncSession = Depends(get_session)
):
    """Функция проверки аутентификации польователя"""
    user = await UserDO.get_by_email(email=email, session=session)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


def create_access_token(data: dict, secret_key: str):
    """Функция создания access токена"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode,
        secret_key,
        algorithm=settings.ALGORITHM,
    )
    return encoded_jwt


def create_refresh_token(data: dict, secret_key: str):
    """Функция создания refresh токена"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode,
        secret_key,
        algorithm=settings.ALGORITHM,
    )
    return encoded_jwt


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_session),
):
    """Функция возврата юзера по access токену"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
    )
    expired_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token expired",
    )
    payload = None
    try:
        # Пробуем декодировать по secret_key веба
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
    except jwt.ExpiredSignatureError:
        raise expired_exception
    except jwt.PyJWTError:
        pass
    # Если не получилось декодировать через secret_key веба
    if not payload:
        try:
            # Пробуем декодировать по secret_key бота
            payload = jwt.decode(
                token,
                settings.SECRET_KEY_BOT,
                algorithms=[settings.ALGORITHM],
            )
        except jwt.ExpiredSignatureError:
            raise expired_exception
        except jwt.PyJWTError:
            raise credentials_exception
    email = payload.get("email")
    if not email:
        raise credentials_exception
    token_data = TokenData(email=email)
    # Проверяем пользователя в БД по email
    user = await UserDO.get_by_email(email=token_data.email, session=session)
    if user is None:
        raise credentials_exception
    return user


def create_email_confirmation_token(email: str):
    """Функция создания токена для подтверждения регистрации"""
    serializer = URLSafeTimedSerializer(settings.SECRET_KEY_EMAIL)
    return serializer.dumps(email, salt="email-confirm")


def verify_email_confirmation_token(token: str):
    """Функция проверки токена подтверждения регистрации"""
    serializer = URLSafeTimedSerializer(settings.SECRET_KEY_EMAIL)
    try:
        return serializer.loads(token, salt="email-confirm", max_age=30 * 60)
    except Exception:
        return None
