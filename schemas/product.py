import os
from decimal import Decimal
from pydantic import BaseModel, Field, computed_field


STATIC_DIR = "static/products/"


class ProductOut(BaseModel):
    id: int
    name: str
    description: str | None
    price: float
    discount: int

    # Поле для формирования пути на фото продукта
    @computed_field
    def image_url(self) -> str | None:
        image_path = f"{STATIC_DIR}product_{self.id}.jpg"
        return (
            f"{STATIC_DIR}product_{self.id}.jpg" if os.path.exists(image_path) else None
        )

    # Поле для вычисления финальной суммы (сумма * скидку)
    @computed_field
    def final_price(self) -> Decimal:
        return self.price - (self.price*(self.discount/100))


class ProductCreate(BaseModel):
    name: str
    description: str | None
    price: float = Field(ge=0)
    discount: int = Field(ge=0, le=100)
