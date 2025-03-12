from typing import List
from datetime import datetime
from decimal import Decimal
from sqlalchemy import ForeignKey, DECIMAL, Enum
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from schemas.order import OrderStatus


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    tg_id: Mapped[str] = mapped_column(unique=True, nullable=True)
    email: Mapped[str] = mapped_column(nullable=False)
    hashed_password: Mapped[str] = mapped_column(nullable=False, default="")
    is_admin: Mapped[bool] = mapped_column(nullable=False, default=False)

    orders: Mapped[List["Order"]] = relationship(
        back_populates="user", cascade="all, delete"
    )

    def __repr__(self):
        return str(self.id)


class Category(Base):
    __tablename__ = "category"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(nullable=False)

    products: Mapped[List["Product"]] = relationship(
        back_populates="category", cascade="all, delete"
    )

    def __repr__(self):
        return f"{self.id} - {self.name}"


class Product(Base):
    __tablename__ = "product"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(nullable=False)
    description: Mapped[str] = mapped_column(nullable=True)
    price: Mapped[Decimal] = mapped_column(DECIMAL(10, 2), nullable=False)
    discount: Mapped[int] = mapped_column(nullable=False, default=0)
    photo_name: Mapped[str] = mapped_column(nullable=False)
    category_id: Mapped[int] = mapped_column(
        ForeignKey("category.id", ondelete="CASCADE")
    )

    category: Mapped["Category"] = relationship(back_populates="products")

    def __repr__(self):
        return f"{self.id} - {self.name}"


class Order(Base):
    __tablename__ = "order"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"))
    total_amount: Mapped[Decimal] = mapped_column(DECIMAL(10, 2), nullable=False)
    status: Mapped[str] = mapped_column(
        Enum(OrderStatus, name="orderstatus", create_type=True),
        default=OrderStatus.processing,
    )
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow().replace(microsecond=0))

    user: Mapped["User"] = relationship(back_populates="orders")
    order_items: Mapped[List["OrderItem"]] = relationship(
        back_populates="order", cascade="all, delete"
    )

    def __repr__(self):
        return str(self.id)


class OrderItem(Base):
    __tablename__ = "order_item"

    order_id: Mapped[int] = mapped_column(
        ForeignKey("order.id", ondelete="CASCADE"), primary_key=True
    )
    product_id: Mapped[int] = mapped_column(nullable=False, primary_key=True)
    name: Mapped[str] = mapped_column(nullable=False)
    quantity: Mapped[int] = mapped_column(nullable=False)
    total_price: Mapped[Decimal] = mapped_column(DECIMAL(10, 2), nullable=False)

    order: Mapped["Order"] = relationship(back_populates="order_items")

    def __repr__(self):
        return str(self.name)
