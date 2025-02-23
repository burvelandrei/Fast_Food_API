from pydantic import BaseModel, EmailStr
from typing import List


class UserOut(BaseModel):
    id: int
    username: str
    tg_id: str | None
    email: EmailStr | None

    class Config:
        from_attributes = True


class UserCreateTg(BaseModel):
    username: str
    tg_id: str


class UserCreateWeb(BaseModel):
    username: str
    email: EmailStr
    password: str