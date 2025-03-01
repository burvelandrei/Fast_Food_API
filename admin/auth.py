import jwt
from datetime import datetime, timedelta
from fastapi import HTTPException, Depends, status, Request
from fastapi.responses import JSONResponse
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer
from environs import Env
from sqlalchemy.ext.asyncio import AsyncSession
from db.connect import get_session
from schemas.token import TokenData
from db.operations import UserDO
from starlette.responses import RedirectResponse
from sqladmin.authentication import AuthenticationBackend
from db.connect import AsyncSessionLocal
from sqlalchemy import select
from db.models import User
from services.auth import verify_password, create_access_token

env = Env()
env.read_env()


SECRET_KEY = env("SECRET_KEY")
ALGORITHM = "HS256"


class JWTAuthBackend(AuthenticationBackend):
    async def login(self, request: Request):
        form = await request.form()
        email = form.get("email")
        password = form.get("password")
        if not email or not password:
            return False
        async with AsyncSessionLocal() as session:
            user = await UserDO.get_by_email(email=email, session=session)
            if not user:
                return False
            if not verify_password(password, user.hashed_password):
                return False
            if not user.is_admin:
                return False
            access_token = create_access_token(data={"email": user.email})
            response = RedirectResponse(url="/admin", status_code=303)
            request.session["access_token"] = access_token
            return response

    async def logout(self, request: Request) -> RedirectResponse:
        if "access_token" in request.session:
            del request.session["access_token"]
        return RedirectResponse(url="/admin/login", status_code=303)

    async def authenticate(self, request: Request) -> bool:
        print(request.headers)
        token = request.session.get("access_token")
        if not token:
            return False
        try:
            jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return True
        except jwt.PyJWTError:
            return False


admin_auth = JWTAuthBackend(secret_key=SECRET_KEY)
