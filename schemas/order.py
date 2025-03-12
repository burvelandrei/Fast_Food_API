from pydantic import BaseModel
from datetime import datetime
from decimal import Decimal
from typing import List
from enum import Enum

class OrderStatus(str, Enum):
    processing = "processing"
    completed = "completed"

class OrderItemOut(BaseModel):
    product_id: int
    name: str
    quantity: int
    total_price: Decimal


class OrderOut(BaseModel):
    id: int
    order_items: List[OrderItemOut]
    total_amount: Decimal
    status: OrderStatus
    created_at: datetime