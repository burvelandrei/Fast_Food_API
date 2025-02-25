from pydantic import BaseModel, EmailStr
from typing import List


class UserOut(BaseModel):
    id: int
    tg_id: str | None
    email: EmailStr | None

    class Config:
        from_attributes = True


class UserDataTg(BaseModel):
    email: EmailStr
    tg_id: str


class UserDataWeb(BaseModel):
    email: EmailStr
    password: str