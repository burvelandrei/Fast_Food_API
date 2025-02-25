from typing import List
from datetime import datetime
from sqlalchemy import ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    tg_id: Mapped[str] = mapped_column(unique=True, nullable=True)
    email: Mapped[str] = mapped_column(nullable=False)
    hashed_password: Mapped[str] = mapped_column(nullable=False, default="")

    orders: Mapped[List["Order"]] = relationship(
        back_populates="user", cascade="all, delete"
    )


class Category(Base):
    __tablename__ = "category"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(nullable=False)

    products: Mapped[List["Product"]] = relationship(
        back_populates="category", cascade="all, delete"
    )


class Product(Base):
    __tablename__ = "product"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(nullable=False)
    description: Mapped[str] = mapped_column(nullable=True)
    price: Mapped[float] = mapped_column(nullable=False)
    discount: Mapped[int] = mapped_column(nullable=False, default=0)
    category_id: Mapped[int] = mapped_column(
        ForeignKey("category.id", ondelete="CASCADE")
    )

    order_items: Mapped[List["OrderItem"]] = relationship(
        back_populates="product", cascade="all, delete"
    )
    category: Mapped["Category"] = relationship(back_populates="products")


class Order(Base):
    __tablename__ = "order"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"))
    total_price: Mapped[float] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    user: Mapped["User"] = relationship(back_populates="orders")
    order_items: Mapped[List["OrderItem"]] = relationship(
        back_populates="order", cascade="all, delete"
    )


class OrderItem(Base):
    __tablename__ = "order_item"

    order_id: Mapped[int] = mapped_column(
        ForeignKey("order.id", ondelete="CASCADE"), primary_key=True
    )
    product_id: Mapped[int] = mapped_column(
        ForeignKey("product.id", ondelete="CASCADE"), primary_key=True
    )
    quantity: Mapped[int] = mapped_column(nullable=False)

    order: Mapped["Order"] = relationship(back_populates="order_items")
    product: Mapped["Product"] = relationship(back_populates="order_items")
