from pydantic import BaseModel, Field


class OrderItemOut(BaseModel):
    order_id: int
    product_id: int
    quantity: int

    class Config:
        from_attributes = True


class OrderItemCreate(BaseModel):
    product_id: int
    quantity: int = Field(ge=0)