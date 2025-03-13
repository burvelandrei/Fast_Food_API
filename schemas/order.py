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
    user_order_id: int
    order_items: List[OrderItemOut]
    total_amount: Decimal
    status: OrderStatus
    delivery: "DeliveryOut"
    created_at: datetime
    created_at_moscow: datetime

class DeliveryType(str, Enum):
    pickup = "pickup"
    courier = "courier"

class DeliveryCreate(BaseModel):
    delivery_type: DeliveryType
    delivery_address: str | None = None

class DeliveryOut(BaseModel):
    id: int
    order_id: int
    delivery_type: DeliveryType
    delivery_address: str | None