from typing import List
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from pydantic import BaseModel, computed_field
from utils.s3_utils import check_file_exists
from config import settings


class SizeOut(BaseModel):
    id: int
    name: str


class ProductSizeOut(BaseModel):
    size: SizeOut
    price: Decimal
    discount: int
    created_at: datetime
    updated_at: datetime

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
    created_at: datetime
    updated_at: datetime

    # Поле для формирования пути на фото продукта (если оно есть в s3 иначе None)
    @computed_field
    def photo_path(self) -> str | None:
        photo_path = f"{settings.STATIC_DIR}/products/{self.photo_name}"
        return f"/{photo_path}" if check_file_exists(file_path=photo_path) else None