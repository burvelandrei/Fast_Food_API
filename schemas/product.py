from typing import List
from decimal import Decimal, ROUND_HALF_UP
from pydantic import BaseModel, Field, computed_field
from utils.s3_utils import check_file_exists


STATIC_DIR = "static/products/"


class SizeOut(BaseModel):
    id: int
    name: str


class ProductSizeOut(BaseModel):
    id: int
    size: SizeOut
    price: Decimal
    discount: int

    # Поле для вычисления финальной суммы (сумма * скидку)
    @computed_field
    def final_price(self) -> Decimal:
        discount_decimal = Decimal(self.discount) / Decimal(100)
        final_price = self.price - (self.price * discount_decimal)
        return final_price.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


class ProductOut(BaseModel):
    id: int
    name: str
    description: str | None
    photo_name: str
    product_sizes: List[ProductSizeOut]

    # Поле для формирования пути на фото продукта (если оно есть в s3 иначе None)
    @computed_field
    def photo_url(self) -> str | None:
        photo_path = f"{STATIC_DIR}{self.photo_name}"
        return f"/{photo_path}" if check_file_exists(key=photo_path) else None


class ProductCreate(BaseModel):
    name: str
    description: str | None
    price: float = Field(ge=0)
    discount: int = Field(ge=0, le=100)
