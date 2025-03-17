import pytest_asyncio
import random
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from factories import (
    CategoryFactory,
    ProductFactory,
    SizeFactory,
    ProductSizeFactory,
    WebUserFactory,
    TgUserFactory,
    CartFactory,
    OrderFactory,
    OrderItemFactory,
    DeliveryFactory,
)
from db.models import Order
from services.auth import create_access_token
from config import settings


@pytest_asyncio.fixture
async def category(test_session: AsyncSession):
    """Создаёт тестовые категории."""
    categories = [
        await CategoryFactory.create_async(session=test_session) for _ in range(3)
    ]
    yield categories


@pytest_asyncio.fixture(autouse=True)
async def products_with_sizes(test_session: AsyncSession):
    """Создает два продукта с размерами"""
    categories = [
        await CategoryFactory.create_async(session=test_session) for _ in range(2)
    ]
    products = []
    sizes = [await SizeFactory.create_async(session=test_session) for i in range(3)]
    product_sizes = []

    for i in range(2):
        product = await ProductFactory.create_async(
            session=test_session,
            category=categories[i],
        )
        for size in sizes:
            product_size = await ProductSizeFactory.create_async(
                session=test_session,
                product_id=product.id,
                size_id=size.id,
            )
            product_sizes.append(product_size)
        products.append(product)

    yield products, sizes, product_sizes
    for product in products:
        await test_session.delete(product)
    for size in sizes:
        await test_session.delete(size)
    for category in categories:
        await test_session.delete(category)
    await test_session.commit()


@pytest_asyncio.fixture
async def web_user(test_session: AsyncSession):
    """
    Создаёт тестового пользователя, зарегистрированного через апи
    """
    user = await WebUserFactory.create_async(session=test_session)
    yield user
    await test_session.rollback()


@pytest_asyncio.fixture
async def tg_user(test_session: AsyncSession):
    """
    Создаёт тестового пользователя, зарегистрированного через бота
    """
    user = await TgUserFactory.create_async(session=test_session)
    yield user
    await test_session.rollback()


@pytest_asyncio.fixture
async def auth_headers_web(test_session: AsyncSession):
    """
    Фикстура для создания заголовков c access токеном апи
    """
    user = await WebUserFactory.create_async(session=test_session)
    access_token = create_access_token(
        data={"email": user.email},
        secret_key=settings.SECRET_KEY,
    )

    headers = {"Authorization": f"Bearer {access_token}"}
    yield headers, user
    await test_session.rollback()


@pytest_asyncio.fixture
async def auth_headers_tg(test_session: AsyncSession):
    """
    Фикстура для создания заголовков c access токеном бота
    """
    user = await TgUserFactory.create_async(session=test_session)
    access_token = create_access_token(
        data={"email": user.email},
        secret_key=settings.SECRET_KEY_BOT,
    )

    headers = {"Authorization": f"Bearer {access_token}"}
    yield headers, user
    await test_session.rollback()


@pytest_asyncio.fixture
async def empty_cart(
    test_redis,
    auth_headers_web,
    products_with_sizes,
):
    """
    Фикстура, создающая пустую корзину для пользователя.
    """
    headers, user = auth_headers_web
    products, sizes, _ = products_with_sizes
    items = []

    yield user.id, f"cart:{user.id}", items, headers, products, sizes

    await CartFactory.clear_cart(test_redis=test_redis, user_id=user.id)


@pytest_asyncio.fixture
async def cart_with_items(test_redis, auth_headers_web, products_with_sizes):
    """
    Фикстура, создающая корзину с элементами для пользователя.
    """
    headers, user = auth_headers_web
    products, sizes, _ = products_with_sizes
    items = []

    for product in products[:2]:
        for size in sizes[:2]:
            quantity = random.randint(1, 10)
            await CartFactory.create_cart_item(
                test_redis=test_redis,
                user_id=user.id,
                product_id=product.id,
                size_id=size.id,
                quantity=quantity,
            )
            items.append((product.id, size.id, quantity))

    yield user.id, f"cart:{user.id}", items, headers, products, sizes

    await CartFactory.clear_cart(test_redis=test_redis, user_id=user.id)


@pytest_asyncio.fixture
async def order_with_items(
    test_session,
    auth_headers_web,
    products_with_sizes,
):
    """
    Фикстура, создающая заказ с товарами из products_with_sizes
    """
    headers, user = auth_headers_web
    products, sizes, _ = products_with_sizes

    orders = []
    for _ in range(5):
        max_user_order_id_query = select(func.max(Order.user_order_id)).where(
            Order.user_id == user.id
        )
        result = await test_session.execute(max_user_order_id_query)
        max_user_order_id = result.scalar() or 0
        order = await OrderFactory.create_async(
            session=test_session,
            user_id=user.id,
            user_order_id=max_user_order_id + 1,
        )
        orders.append(order)
        order_items = []
        for product in products[:2]:
            for size in sizes[:2]:
                quantity = random.randint(1, 5)
                order_item = await OrderItemFactory.create_async(
                    order_id=order.id,
                    product_id=product.id,
                    size_id=size.id,
                    quantity=quantity,
                    session=test_session,
                )
                order_items.append(order_item)
        delivery = await DeliveryFactory.create_async(
            session=test_session, order_id=order.id
        )

    await test_session.commit()

    yield orders

    for order in orders:
        await test_session.delete(order)

    await test_session.commit()
