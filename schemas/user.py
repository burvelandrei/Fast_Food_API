from pydantic import BaseModel, EmailStr, Field
from datetime import datetime


class UserOut(BaseModel):
    id: int
    tg_id: str | None
    email: EmailStr | None
    created_at: datetime
    updated_at: datetime


class UserDataTg(BaseModel):
    email: EmailStr
    tg_id: str


class UserDataWeb(BaseModel):
    email: EmailStr
    password: str = Field(
        min_length=8,
        description="Password must be more than 8 characters",
    )
