import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from factories import CategoryFactory, ProductFactory, SizeFactory, ProductSizeFactory


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