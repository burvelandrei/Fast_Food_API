import jwt
from fastapi import Request
from environs import Env
from db.connect import get_session
from db.operations import UserDO
from starlette.responses import RedirectResponse
from sqladmin.authentication import AuthenticationBackend
from db.connect import AsyncSessionLocal
from services.auth import verify_password, create_access_token, create_refresh_token
from admin.middllwares import CookieMiddleware
from starlette.middleware import Middleware

env = Env()
env.read_env()


SECRET_KEY_ADMIN = env("SECRET_KEY_ADMIN")
ALGORITHM = "HS256"


class JWTAuthBackend(AuthenticationBackend):
    """Класс аутентификации в sqladmin"""

    def __init__(self, secret_key):
        super().__init__(secret_key)
        self.middlewares = [
            Middleware(CookieMiddleware),
        ]

    async def login(self, request: Request):
        form = await request.form()
        email = form.get("email")
        password = form.get("password")

        if not email or not password:
            return False
        # Проверяем пользоваетля в БД и то что он является админом
        async with AsyncSessionLocal() as session:
            user = await UserDO.get_by_email(email=email, session=session)
            if (
                not user
                or not verify_password(password, user.hashed_password)
                or not user.is_admin
            ):
                return False

        access_token = create_access_token(
            data={"email": email},
            secret_key=SECRET_KEY_ADMIN,
        )
        refresh_token = create_refresh_token(
            data={"email": email},
            secret_key=SECRET_KEY_ADMIN,
        )
        # устанавливаем cookie в scope
        request.scope["set_cookie"](
            "access_token",
            access_token,
        )
        request.scope["set_cookie"](
            "refresh_token",
            refresh_token,
            max_age=7 * 24 * 60 * 60,
        )

        return True

    async def logout(self, request: Request):
        request.scope["set_cookie"]("access_token", "", max_age=0)
        request.scope["set_cookie"]("refresh_token", "", max_age=0)
        return False

    async def authenticate(self, request: Request):
        token = request.cookies.get("access_token")
        refresh_token = request.cookies.get("refresh_token")

        if not token:
            return False

        try:
            jwt.decode(token, SECRET_KEY_ADMIN, algorithms=[ALGORITHM])
            return True
        except jwt.ExpiredSignatureError:
            # если токен access истёк пробуем обновить через refresh
            if refresh_token:
                try:
                    payload = jwt.decode(
                        refresh_token, SECRET_KEY_ADMIN, algorithms=[ALGORITHM]
                    )
                    new_access_token = create_access_token(
                        data={"email": payload["email"]},
                        secret_key=SECRET_KEY_ADMIN,
                    )
                    request.session.update(
                        {"access_token": new_access_token},
                    )
                    return True
                except jwt.ExpiredSignatureError:
                    # если истёк refresh то отправляем на login
                    return False
            return False
        except jwt.PyJWTError:
            return False


admin_auth = JWTAuthBackend(secret_key=SECRET_KEY_ADMIN)
