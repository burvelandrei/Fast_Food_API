import factory
import json
from faker import Faker
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from db.models import Category, Product, Size, ProductSize, User
from schemas.cart import CartItemCreate
from services.auth import get_hash_password

fake = Faker()


class AsyncSQLAlchemyModelFactory(factory.Factory):
    """Асинхронная фабрика для моделей"""

    class Meta:
        abstract = True

    @classmethod
    async def create_async(cls, session: AsyncSession, **kwargs):
        obj = cls.build(**kwargs)
        session.add(obj)
        await session.commit()
        await session.refresh(obj)
        return obj


class CategoryFactory(AsyncSQLAlchemyModelFactory):
    """Фабрика для модели Category"""

    class Meta:
        model = Category

    name = factory.LazyAttribute(lambda _: fake.word())


class SizeFactory(AsyncSQLAlchemyModelFactory):
    """Фабрика для модели Size"""

    class Meta:
        model = Size

    name = factory.LazyAttribute(lambda _: fake.word())


class ProductFactory(AsyncSQLAlchemyModelFactory):
    """Фабрика для модели Product"""

    class Meta:
        model = Product

    name = factory.LazyAttribute(lambda _: fake.word())
    description = factory.LazyAttribute(lambda _: fake.text())
    photo_name = factory.LazyAttribute(lambda _: fake.file_name(extension="jpg"))
    category = None
    category_id = factory.LazyAttribute(lambda o: o.category.id if o.category else None)


class ProductSizeFactory(AsyncSQLAlchemyModelFactory):
    """Фабрика для модели ProductSize"""

    class Meta:
        model = ProductSize

    product_id = factory.SubFactory(ProductFactory)
    size_id = factory.SubFactory(SizeFactory)
    price = factory.LazyAttribute(lambda _: Decimal(fake.random_number(digits=2)))
    discount = factory.LazyAttribute(lambda _: fake.random_int(min=0, max=100))


class WebUserFactory(AsyncSQLAlchemyModelFactory):
    """Фабрика для пользователей, зарегистрированных через апи"""

    class Meta:
        model = User

    email = factory.Faker("email")
    hashed_password = factory.LazyFunction(lambda: get_hash_password("testpassword"))
    is_admin = False


class TgUserFactory(AsyncSQLAlchemyModelFactory):
    """Фабрика для пользователей, зарегистрированных через бота"""

    class Meta:
        model = User

    tg_id = factory.Faker("uuid4")
    email = factory.Faker("email")
    hashed_password = ""
    is_admin = False


class CartFactory:
    """Фабрика для создания корзины"""

    @staticmethod
    async def create_cart_item(
        test_redis,
        user_id: int,
        product_id: int,
        size_id: int,
        quantity: int,
    ) -> tuple[str, str]:

        cart_item = CartItemCreate(
            product_id=product_id,
            size_id=size_id,
            quantity=quantity,
        )
        cart_key = f"cart:{user_id}"
        cart_item_id = f"{product_id}:{size_id}"
        await test_redis.hset(cart_key, cart_item_id, json.dumps(cart_item.dict()))
        return cart_key, cart_item_id

    @staticmethod
    async def clear_cart(test_redis, user_id: int):
        """Очищает корзину пользователя"""
        cart_key = f"cart:{user_id}"
        await test_redis.delete(cart_key)