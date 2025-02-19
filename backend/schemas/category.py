from pydantic import BaseModel
from typing import List
from schemas.product import ProductOut


class CategoryOut(BaseModel):
    id: int
    name: str
    products: List[ProductOut]

    class Config:
        from_attributes = True


class CategoryCreate(BaseModel):
    name: str