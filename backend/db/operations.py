from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from db.models import User, Product, Order, OrderItem, Category, RefreshToken


class BaseDO:

    model = None

    @classmethod
    async def get_all(cls, session: AsyncSession):
        query = select(cls.model)
        result = await session.execute(query)
        return result.scalars().all()

    @classmethod
    async def get_by_id(cls, session: AsyncSession, id: int):
        query = select(cls.model).where(cls.model.id == id)
        result = await session.execute(query)
        return result.scalar_one_or_none()

    @classmethod
    async def add(cls, session: AsyncSession, **values):
        new_instance = cls.model(**values)
        session.add(new_instance)
        try:
            await session.commit()
        except Exception as e:
            await session.rollback()
            raise e
        return new_instance

    @classmethod
    async def update(cls, session: AsyncSession, id: int, **values):
        instance = await cls.get_by_id(session, id)
        if not instance:
            return None

        for key, value in values.items():
            setattr(instance, key, value)

        try:
            await session.commit()
        except Exception as e:
            await session.rollback()
            raise e
        return instance

    @classmethod
    async def delete(cls, session: AsyncSession, id: int):
        try:
            data = cls.get_by_id(session=session, id=id)
            if data:
                await session.delete(data)
                await session.commit()
        except Exception as e:
            await session.rollback()
            raise e


class UserDO(BaseDO):
    model = User

    @classmethod
    async def get_by_email(cls, email: str, session: AsyncSession):
        query = select(cls.model).where(cls.model.email == email)
        result = await session.execute(query)
        return result.scalar_one_or_none()


class RefreshTokenDO(BaseDO):
    model = RefreshToken


class CategoryDO(BaseDO):
    model = Category

    @classmethod
    async def get_all(cls, session: AsyncSession):
        query = select(cls.model).options(selectinload(cls.model.products))
        result = await session.execute(query)
        return result.scalars().all()


class ProductDO(BaseDO):
    model = Product

    @classmethod
    async def get_all(cls, category_id: int, session: AsyncSession):
        query = select(cls.model)
        if category_id:
            query = query.where(cls.model.category_id == category_id)
        result = await session.execute(query)
        return result.scalars().all()


class OrderItemDO(BaseDO):
    model = OrderItem

    @classmethod
    async def add_many(cls, order: int, session: AsyncSession, values: dict):
        for item in values:
            new_instance = cls.model(
                order_id=order.id,
                product_id=item["product_id"],
                quantity=item["quantity"],
            )
            session.add(new_instance)
        try:
            await session.commit()
        except Exception as e:
            await session.rollback()
            raise e


class OrderDO(BaseDO):
    model = Order

    @classmethod
    async def get_all(cls, user_id: int, session: AsyncSession):
        query = (
            select(cls.model)
            .where(cls.model.user_id == user_id)
            .options(
                selectinload(cls.model.order_items).selectinload(OrderItem.product)
            )
        )
        result = await session.execute(query)
        return result.scalars().all()

    @classmethod
    async def add(cls, user_id: int, session: AsyncSession, values: dict):
        new_instance = cls.model(user_id=user_id)
        session.add(new_instance)
        try:
            await session.flush()
            await OrderItemDO.add_many(
                order=new_instance, session=session, values=values
            )
            await session.commit()
        except Exception as e:
            await session.rollback()
            raise e
