import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from factories import (
    CategoryFactory,
    ProductFactory,
    SizeFactory,
    ProductSizeFactory,
    WebUserFactory,
    TgUserFactory,
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
    await test_session.rollback()


@pytest_asyncio.fixture
async def products_with_sizes(test_session: AsyncSession):
    """Создает два продукта с размерами"""
    products = []
    sizes = [await SizeFactory.create_async(session=test_session) for i in range(3)]
    product_sizes = []

    for i in range(2):
        product = await ProductFactory.create_async(session=test_session)
        for size in sizes:
            product_size = await ProductSizeFactory.create_async(
                session=test_session,
                product_id=product.id,
                size_id=size.id,
            )
            product_sizes.append(product_size)
        products.append(product)

    yield products, sizes, product_sizes
    await test_session.rollback()


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
