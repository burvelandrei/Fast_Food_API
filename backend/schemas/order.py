from pydantic import BaseModel
from datetime import datetime
from typing import List
from schemas.order_item import OrderItemOut


class OrderOut(BaseModel):
    id: int
    user_id: int
    created_at: datetime
    order_items: List[OrderItemOut]

    class Config:
        from_attributes = True