import os
from pydantic import BaseModel, Field, computed_field


STATIC_DIR = "static/products/"


class ProductOut(BaseModel):
    id: int
    name: str
    description: str | None
    price: float
    discount: int

    @computed_field
    def image_url(self) -> str | None:
        image_path = f"{STATIC_DIR}product{self.id}.jpg"
        return (
            f"{STATIC_DIR}product{self.id}.jpg" if os.path.exists(image_path) else None
        )


class ProductCreate(BaseModel):
    name: str
    description: str | None
    price: float = Field(ge=0)
    discount: int = Field(ge=0, le=100)
