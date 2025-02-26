from pydantic import BaseModel
from datetime import datetime
from typing import List
from schemas.product import ProductOut


class OrderItemOut(BaseModel):
    quantity: int
    product: ProductOut


class OrderOut(BaseModel):
    id: int
    user_id: int
    created_at: datetime
    order_items: List[OrderItemOut]