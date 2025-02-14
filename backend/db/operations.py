from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from db.models import User, Product, Order, OrderItem


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


class ProductDO(BaseDO):
    model = Product


class OrderDO(BaseDO):
    model = Order


class OrderItemDO(BaseDO):
    model = OrderItem
