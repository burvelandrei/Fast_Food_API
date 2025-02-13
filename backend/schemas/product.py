from pydantic import BaseModel, Field


class ProductOut(BaseModel):
    id: int
    name: str
    description: str | None
    price: float
    discount: int

    class Config:
        from_attributes = True


class ProductCreate(BaseModel):
    name: str
    description: str | None
    price: float = Field(ge=0)
    discount: int = Field(ge=0, le=100)
