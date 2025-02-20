from pydantic import BaseModel, Field
from schemas.product import ProductOut


class OrderItemOut(BaseModel):
    quantity: int
    product: ProductOut


    class Config:
        from_attributes = True