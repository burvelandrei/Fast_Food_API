from typing import List
from decimal import Decimal
from pydantic import BaseModel, Field
from schemas.product import ProductOut


class CartItemOut(BaseModel):
    product: ProductOut
    quantity: int
    total_price: Decimal


class CartOut(BaseModel):
    cart_items: List[CartItemOut] = []
    total_amount: Decimal


class CartItemСreate(BaseModel):
    product_id: int
    quantity: int = Field(
        ge=1,
        description="Quantity must be at least 1",
    )


class CartItemModify(BaseModel):
    quantity: int = Field(
        ge=1,
        description="Quantity must be at least 1",
    )
