import logging
import logging.config
from sqlalchemy import select, desc, func
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from db.models import (
    User,
    Product,
    Order,
    OrderItem,
    Category,
    Delivery,
    Size,
    ProductSize,
)
from utils.logger import logging_config


logging.config.dictConfig(logging_config)
logger = logging.getLogger("db_operations")


class BaseDO:
    """Базовый класс с операциями к БД"""

    model = None

    @classmethod
    async def get_all(cls, session: AsyncSession):
        """Получить все элементы из БД"""
        try:
            logger.info(f"Fetching all records for {cls.model.__name__}")
            query = select(cls.model)
            result = await session.execute(query)
            return result.scalars().all()
        except Exception as e:
            logger.error(
                f"An error occurred while fetching all records for "
                f"{cls.model.__name__}: {e}",
            )
            raise e

    @classmethod
    async def get_by_id(cls, session: AsyncSession, id: int):
        """Получить элементы по id или вернуть None если нет"""
        try:
            logger.info(f"Fetching {cls.model.__name__} with id {id}")
            query = select(cls.model).where(cls.model.id == id)
            result = await session.execute(query)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(
                f"An error occurred while fetching "
                f"{cls.model.__name__} with id {id}: {e}",
            )
            raise e

    @classmethod
    async def add(cls, session: AsyncSession, **values):
        """Добавить объект в БД"""
        new_instance = cls.model(**values)
        session.add(new_instance)
        try:
            await session.commit()
            logger.info(f"Added new {cls.model.__name__}")
        except Exception as e:
            await session.rollback()
            logger.error(f"Error adding {cls.model.__name__}: {e}")
            raise e
        return new_instance

    @classmethod
    async def update(cls, session: AsyncSession, id: int, **values):
        """Изменить элементы для id"""
        logger.info(f"Updating {cls.model.__name__} with id {id}")
        instance = await cls.get_by_id(session, id)
        if not instance:
            logger.warning(f"{cls.model.__name__} with id {id} not found")
            return None

        for key, value in values.items():
            setattr(instance, key, value)

        try:
            await session.commit()
            logger.info(f"Updated {cls.model.__name__} with id {id}")
        except Exception as e:
            await session.rollback()
            logger.error(f"Error updating {cls.model.__name__}: {e}")
            raise e
        return instance

    @classmethod
    async def delete(cls, session: AsyncSession, id: int):
        """Удалить по id"""
        logger.info(f"Deleting {cls.model.__name__} with id {id}")
        try:
            data = await cls.get_by_id(session=session, id=id)
            if data:
                await session.delete(data)
                await session.commit()
                logger.info(f"Deleted {cls.model.__name__} with id {id}")
        except Exception as e:
            await session.rollback()
            logger.error(f"Error deleting {cls.model.__name__}: {e}")
            raise e


class UserDO(BaseDO):
    """Класс c операциями для модели User"""

    model = User

    @classmethod
    async def get_by_email(cls, email: str, session: AsyncSession):
        """Получить элементы user по email"""
        try:
            logger.info("Fetching User by email")
            query = select(cls.model).where(cls.model.email == email)
            result = await session.execute(query)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(
                f"An error occurred while fetching User by email: {e}",
            )
            raise e

    @classmethod
    async def get_by_tg_id(cls, tg_id: str, session: AsyncSession):
        """Получить элементы user по tg_id"""
        try:
            logger.info("Fetching User by Telegram ID")
            query = select(cls.model).where(cls.model.tg_id == tg_id)
            result = await session.execute(query)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(
                f"An error occurred while fetching User by Telegram ID: {e}",
            )
            raise e


class CategoryDO(BaseDO):
    """Класс c операциями для модели Category"""

    model = Category


class ProductDO(BaseDO):
    """Класс c операциями для модели Product"""

    model = Product

    @classmethod
    async def get_all(cls, session: AsyncSession):
        """Получение products"""
        try:
            logger.info("Fetching all products")
            query = select(cls.model).options(
                selectinload(cls.model.product_sizes)
                .selectinload(ProductSize.size)
            )
            result = await session.execute(query)
            return result.scalars().all()
        except Exception as e:
            logger.error(
                f"An error occurred while fetching products: {e}",
            )
            raise e

    @classmethod
    async def get_all_by_category_id(
        cls,
        category_id: int,
        session: AsyncSession,
    ):
        """Получение products для category_id"""
        try:
            logger.info(f"Fetching all products for category_id {category_id}")
            query = (
                select(cls.model)
                .where(cls.model.category_id == category_id)
                .options(
                    selectinload(cls.model.product_sizes)
                    .selectinload(ProductSize.size)
                )
            )
            result = await session.execute(query)
            return result.scalars().all()
        except Exception as e:
            logger.error(
                f"An error occurred while fetching products for category_id "
                f"{category_id}: {e}",
            )
            raise e

    @classmethod
    async def get_by_id(cls, product_id: int, session: AsyncSession):
        """Получаем продукт по product_id и size_id"""
        try:
            logger.info(f"Fetching product with id {product_id}")
            query = (
                select(cls.model)
                .where(cls.model.id == product_id)
                .options(
                    selectinload(cls.model.product_sizes)
                    .selectinload(ProductSize.size)
                )
            )
            result = await session.execute(query)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(
                f"An error occurred while fetching product with id "
                f"{product_id}: {e}",
            )
            raise e

    @classmethod
    async def get_by_photo_name(cls, photo_name: str, session: AsyncSession):
        """Получаем продукт по product_id и size_id"""
        try:
            logger.info(f"Fetching product with photo_name {photo_name}")
            query = select(cls.model).where(cls.model.photo_name == photo_name)
            result = await session.execute(query)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(
                f"An error occurred while fetching product with id "
                f"{photo_name}: {e}",
            )
            raise e

    @classmethod
    async def get_for_id_by_size_id(
        cls, product_id: int, size_id: int, session: AsyncSession
    ):
        """Получаем продукт по product_id и size_id"""
        try:
            logger.info(f"Fetching product with id {product_id} and size_id "
                        f"{size_id}")
            query = (
                select(ProductSize)
                .join(Product)
                .join(Size)
                .where(
                    ProductSize.product_id == product_id,
                    ProductSize.size_id == size_id,
                )
                .options(
                    selectinload(ProductSize.product),
                    selectinload(ProductSize.size),
                )
            )
            result = await session.execute(query)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(
                f"An error occurred while fetching product with id "
                f"{product_id} and size_id {size_id}: {e}",
            )
            raise e


class OrderItemDO(BaseDO):
    """Класс c операциями для модели OrderItem"""

    model = OrderItem

    @classmethod
    async def add_many_by_order(
        cls,
        order: Order,
        session: AsyncSession,
        values: dict,
    ):
        """Добавление order_items для order"""
        logger.info(f"Adding multiple order items for order {order.id}")
        for item in values.cart_items:
            new_instance = cls.model(
                order_id=order.id,
                product_id=item.product.id,
                name=item.product.name,
                size_id=item.product.size_id,
                size_name=item.product.size_name,
                quantity=item.quantity,
                total_price=item.total_price,
            )
            session.add(new_instance)
        try:
            await session.flush()
            logger.info(f"Added order items for order {order.id}")
        except Exception as e:
            logger.error(f"Error adding order items: {e}")
            raise e


class DeliveryDO(BaseDO):
    """Класс c операциями для модели Delivery"""

    model = Delivery

    @classmethod
    async def add_by_order(
        cls, order: Order, session: AsyncSession, delivery_data: Delivery
    ):
        """Добавление delivery info для order"""
        logger.info(f"Adding delivery info for order {order.id}")
        new_instance = cls.model(
            order_id=order.id,
            delivery_type=delivery_data.delivery_type,
            delivery_address=delivery_data.delivery_address,
        )
        session.add(new_instance)
        try:
            await session.flush()
            logger.info(f"Added delivery info for order {order.id}")
        except Exception as e:
            logger.error(f"Error adding delivery info: {e}")
            raise e


class OrderDO(BaseDO):
    """Класс c операциями для модели Order"""

    model = Order

    @classmethod
    async def get_all(cls, user_id: int, session: AsyncSession):
        """Получение всех orders для user_id"""
        try:
            logger.info(f"Fetching all Order for user ID {user_id}")
            query = (
                select(cls.model)
                .where(cls.model.user_id == user_id)
                .options(
                    selectinload(cls.model.order_items),
                    selectinload(cls.model.delivery),
                )
                .order_by(desc(cls.model.created_at))
            )
            result = await session.execute(query)
            return result.scalars().all()
        except Exception as e:
            logger.error(
                f"An error occurred while fetching orders for user ID "
                f"{user_id}: {e}",
            )
            raise e

    @classmethod
    async def get_all_by_status(
        cls,
        user_id: int,
        status: str,
        session: AsyncSession,
    ):
        """Получение всех orders для user_id по указанному статусу"""
        try:
            logger.info(f"Fetching all Order for user ID {user_id}")
            query = (
                select(cls.model)
                .where(cls.model.user_id == user_id)
                .where(cls.model.status == status)
                .options(
                    selectinload(cls.model.order_items),
                    selectinload(cls.model.delivery),
                )
                .order_by(desc(cls.model.created_at))
            )
            result = await session.execute(query)
            return result.scalars().all()
        except Exception as e:
            logger.error(
                f"An error occurred while fetching orders for user ID "
                f"{user_id}: {e}",
            )
            raise e

    @classmethod
    async def get_all_by_statuses(
        cls,
        user_id: int,
        statuses: List[str],
        session: AsyncSession,
    ):
        """Получение всех orders для user_id по указанным статусам"""
        try:
            logger.info(
                f"Fetching orders for user ID {user_id} with statuses: "
                f"{statuses}"
            )
            query = (
                select(cls.model)
                .where(cls.model.user_id == user_id)
                .where(cls.model.status.in_(statuses))
                .options(
                    selectinload(cls.model.order_items),
                    selectinload(cls.model.delivery),
                )
                .order_by(desc(cls.model.created_at))
            )
            result = await session.execute(query)
            orders = result.scalars().all()
            return orders
        except Exception as e:
            logger.error(
                f"Error fetching orders for user ID {user_id}: {e}",
                exc_info=True
            )
            raise

    @classmethod
    async def get_by_id(
        cls,
        order_id: int,
        user_id: int,
        session: AsyncSession,
    ):
        """Получение orders по order_id для указанного пользователя"""
        logger.info(
            f"Fetching order (ID: {order_id}) for user (ID: {user_id})"
        )
        try:
            query = (
                select(cls.model)
                .where(cls.model.id == order_id, cls.model.user_id == user_id)
                .options(
                    selectinload(cls.model.order_items),
                    selectinload(cls.model.delivery),
                )
            )
            result = await session.execute(query)
            order = result.scalar_one_or_none()
            return order
        except Exception as e:
            logger.exception(
                f"Error fetching order (ID: {order_id}) for user (ID: "
                f"{user_id}): {e}"
            )
            raise e

    @classmethod
    async def add(
        cls,
        user_id: int,
        session: AsyncSession,
        values: dict,
        delivery_data: Delivery,
    ):
        """Добавление order для user_id"""
        logger.info(f"Creating new order for user_id {user_id}")
        max_user_order_id_query = select(
            func.max(cls.model.user_order_id)
        ).where(
            cls.model.user_id == user_id
        )
        result = await session.execute(max_user_order_id_query)
        max_user_order_id = result.scalar() or 0
        new_instance = cls.model(
            user_id=user_id,
            total_amount=values.total_amount,
            user_order_id=max_user_order_id + 1,
        )
        session.add(new_instance)
        try:
            await session.flush()
            await OrderItemDO.add_many_by_order(
                order=new_instance, session=session, values=values
            )
            await DeliveryDO.add_by_order(
                order=new_instance,
                session=session,
                delivery_data=delivery_data,
            )
            await session.commit()
            logger.info("Added new Order")
        except Exception as e:
            await session.rollback()
            logger.error(f"Error adding Order: {e}")
            raise e
