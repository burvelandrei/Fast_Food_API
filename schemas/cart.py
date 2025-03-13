from typing import List
from decimal import Decimal
from pydantic import BaseModel, Field, computed_field
from schemas.product import ProductOut


class CartItemOut(BaseModel):
    product: ProductOut
    quantity: int

    @computed_field
    def total_price(self) -> Decimal:
        return self.product.final_price * self.quantity


class CartOut(BaseModel):
    cart_items: List[CartItemOut] = []

    @computed_field
    def total_amount(self) -> Decimal:
        return sum(item.total_price for item in self.cart_items) or Decimal("0.00")


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
