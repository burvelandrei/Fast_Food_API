from typing import List
from datetime import datetime
from decimal import Decimal
from sqlalchemy import ForeignKey, DECIMAL, Enum, case, func
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
    column_property,
)
from schemas.order import OrderStatus, DeliveryType


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        default=func.date_trunc(
            "second",
            func.timezone(
                "Europe/Moscow",
                func.now(),
            ),
        ),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        default=func.date_trunc(
            "second",
            func.timezone(
                "Europe/Moscow",
                func.now(),
            ),
        ),
        onupdate=func.date_trunc(
            "second",
            func.timezone(
                "Europe/Moscow",
                func.now(),
            ),
        ),
        nullable=False,
    )


class Base(DeclarativeBase):
    pass


class User(Base, TimestampMixin):
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


class Product(Base, TimestampMixin):
    __tablename__ = "product"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(nullable=False)
    description: Mapped[str] = mapped_column(nullable=True)
    photo_name: Mapped[str] = mapped_column(nullable=True)
    category_id: Mapped[int] = mapped_column(
        ForeignKey("category.id", ondelete="CASCADE")
    )

    category: Mapped["Category"] = relationship(back_populates="products")
    product_sizes: Mapped[List["ProductSize"]] = relationship(
        "ProductSize", back_populates="product", cascade="all, delete"
    )

    def __repr__(self):
        return f"{self.id} - {self.name}"


class Size(Base):
    __tablename__ = "size"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(nullable=False, unique=True)

    size_products: Mapped[List["ProductSize"]] = relationship(
        "ProductSize", back_populates="size", cascade="all, delete"
    )

    def __repr__(self):
        return f"{self.name}"


class ProductSize(Base, TimestampMixin):
    __tablename__ = "product_size"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(
        ForeignKey("product.id", ondelete="CASCADE")
    )
    size_id: Mapped[int] = mapped_column(
        ForeignKey(
            "size.id",
            ondelete="CASCADE",
        )
    )
    price: Mapped[Decimal] = mapped_column(DECIMAL(10, 2), nullable=False)
    discount: Mapped[int] = mapped_column(nullable=False, default=0)

    product: Mapped["Product"] = relationship(
        "Product",
        back_populates="product_sizes",
    )
    size: Mapped["Size"] = relationship(
        "Size",
        back_populates="size_products",
    )

    def __repr__(self):
        return f"{self.size.name} - {self.price} - {self.discount}"


class Order(Base, TimestampMixin):
    __tablename__ = "order"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey(
            "user.id",
            ondelete="CASCADE",
        )
    )
    user_order_id: Mapped[int] = mapped_column(nullable=False)
    total_amount: Mapped[Decimal] = mapped_column(
        DECIMAL(10, 2),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        Enum(OrderStatus, name="orderstatus", create_type=True),
        default=OrderStatus.CREATED,
    )

    status_sort = column_property(
        case(
            (status == OrderStatus.CREATED, 1),
            (status == OrderStatus.COOKING, 2),
            (status == OrderStatus.READY, 3),
            (status == OrderStatus.DELIVERING, 4),
            (status == OrderStatus.COMPLETED, 5),
            else_=6,
        )
    )

    user: Mapped["User"] = relationship(back_populates="orders")
    order_items: Mapped[List["OrderItem"]] = relationship(
        back_populates="order", cascade="all, delete"
    )
    delivery: Mapped["Delivery"] = relationship(
        uselist=False,
        back_populates="order",
        cascade="all, delete",
    )

    def __repr__(self):
        return str(self.id)


class OrderItem(Base):
    __tablename__ = "order_item"

    order_id: Mapped[int] = mapped_column(
        ForeignKey("order.id", ondelete="CASCADE"), primary_key=True
    )
    product_id: Mapped[int] = mapped_column(nullable=False, primary_key=True)
    size_id: Mapped[int] = mapped_column(nullable=False, primary_key=True)
    name: Mapped[str] = mapped_column(nullable=False)
    size_name: Mapped[str] = mapped_column(nullable=False)
    quantity: Mapped[int] = mapped_column(nullable=False)
    total_price: Mapped[Decimal] = mapped_column(
        DECIMAL(10, 2),
        nullable=False,
    )

    order: Mapped["Order"] = relationship(back_populates="order_items")

    def __repr__(self):
        return str(self.name)


class Delivery(Base):
    __tablename__ = "delivery"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(
        ForeignKey(
            "order.id",
            ondelete="CASCADE",
        )
    )
    delivery_type: Mapped[str] = mapped_column(
        Enum(DeliveryType, name="deliverytype", create_type=True),
        default=DeliveryType.pickup,
    )
    delivery_address: Mapped[str] = mapped_column(nullable=True)

    order: Mapped["Order"] = relationship(back_populates="delivery")

    def __repr__(self):
        return str(self.id)
