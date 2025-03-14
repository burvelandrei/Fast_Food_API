from typing import List
from decimal import Decimal, ROUND_HALF_UP
from pydantic import BaseModel, Field, computed_field
from utils.s3_utils import check_file_exists
from config import settings


class ProductCartOut(BaseModel):
    id: int
    name: str
    description: str | None
    photo_name: str
    size_id: int
    size_name: str
    price: Decimal
    discount: int

    # Поле для вычисления финальной суммы (сумма * скидку)
    @computed_field
    def final_price(self) -> Decimal:
        discount_decimal = Decimal(self.discount) / Decimal(100)
        final_price = self.price - (self.price * discount_decimal)
        return final_price.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    # Поле для формирования пути на фото продукта (если оно есть в s3 иначе None)
    @computed_field
    def photo_path(self) -> str | None:
        photo_path = f"{settings.STATIC_DIR}/products/{self.photo_name}"
        return f"/{photo_path}" if check_file_exists(file_path=photo_path) else None


class CartItemOut(BaseModel):
    product: ProductCartOut
    quantity: int

    @computed_field
    def total_price(self) -> Decimal:
        return self.product.final_price * self.quantity


class CartOut(BaseModel):
    cart_items: List[CartItemOut] = []

    @computed_field
    def total_amount(self) -> Decimal:
        return sum(item.total_price for item in self.cart_items) or Decimal("0.00")


class CartItemCreate(BaseModel):
    product_id: int
    size_id: int
    quantity: int = Field(
        ge=1,
        description="Quantity must be at least 1",
    )


class CartItemModify(BaseModel):
    quantity: int = Field(
        ge=1,
        description="Quantity must be at least 1",
    )
