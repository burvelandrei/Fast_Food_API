import os
from decimal import Decimal
from pydantic import BaseModel, Field, computed_field
from services.s3_utils import check_file_exists


STATIC_DIR = "static/products/"


class ProductOut(BaseModel):
    id: int
    name: str
    description: str | None
    price: float
    discount: int
    photo_name: str

    # Поле для формирования пути на фото продукта (если оно есть в s3 иначе None)
    @computed_field
    def photo_url(self) -> str | None:
        photo_path = f"{STATIC_DIR}{self.photo_name}"
        return f"/{photo_path}" if check_file_exists(key=photo_path) else None

    # Поле для вычисления финальной суммы (сумма * скидку)
    @computed_field
    def final_price(self) -> Decimal:
        return self.price - (self.price * (self.discount / 100))


class ProductCreate(BaseModel):
    name: str
    description: str | None
    price: float = Field(ge=0)
    discount: int = Field(ge=0, le=100)
