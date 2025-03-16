from typing import List
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from pydantic import BaseModel, computed_field
from utils.s3_utils import check_file_exists_to_s3, get_last_modified_to_s3
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
    photo_name: str | None
    category_id: int
    product_sizes: List[ProductSizeOut]
    created_at: datetime
    updated_at: datetime

    # Поле для формирования пути на фото продукта c учётом последнего изменения
    # (если оно есть в s3 иначе None)
    @computed_field
    def photo_path(self) -> str | None:
        if self.photo_name:
            photo_path = f"{settings.STATIC_DIR}/products/{self.photo_name}"
            if check_file_exists_to_s3(file_path=photo_path):
                last_modifed = get_last_modified_to_s3(file_path=photo_path)
                photo_url = f"/{photo_path}?{last_modifed}"
                return photo_url
        return None
