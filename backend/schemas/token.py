from pydantic import BaseModel, EmailStr


class TokenData(BaseModel):
    email: EmailStr | None
    tg_id: str | None


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str