import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from factories import (
    CategoryFactory,
    ProductFactory,
    SizeFactory,
    ProductSizeFactory,
    WebUserFactory,
    TgUserFactory,
    CartFactory,
)
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
    return headers, user


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
    return headers, user


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
            await CartFactory.create_cart_item(
                test_redis=test_redis,
                user_id=user.id,
                product_id=product.id,
                size_id=size.id,
                quantity=5,
            )
            items.append((product.id, size.id))

    yield user.id, f"cart:{user.id}", items, headers, products, sizes

    await CartFactory.clear_cart(test_redis=test_redis, user_id=user.id)