from pydantic import BaseModel, EmailStr, Field


class UserOut(BaseModel):
    id: int
    tg_id: str | None
    email: EmailStr | None


class UserDataTg(BaseModel):
    email: EmailStr
    tg_id: str


class UserDataWeb(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)