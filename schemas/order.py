from pydantic import BaseModel
from datetime import datetime
from decimal import Decimal
from typing import List
from schemas.product import ProductOut


class OrderItemOut(BaseModel):
    product_id: int
    name: str
    quantity: int
    total_price: Decimal


class OrderOut(BaseModel):
    id: int
    order_items: List[OrderItemOut]
    total_amount: Decimal
    created_at: datetime