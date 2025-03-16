import pytest
import pytest_asyncio
import asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from redis.asyncio import Redis
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from main import app
from db.models import Base
from db.connect import get_session
from config import settings


# Настройки PostgreSQL (локальная БД)
TEST_DATABASE_URL = (
    f"postgresql+asyncpg://{settings.TEST_DB_USER}:{settings.TEST_DB_PASSWORD}@"
    f"{settings.TEST_DB_HOST}:{settings.TEST_DB_PORT}/{settings.TEST_DB_NAME}"
)
engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestingSessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False)


@pytest.fixture(scope="session")
def event_loop():
    """
    Используем общий event loop
    """
    loop = asyncio.get_event_loop()
    yield loop


@pytest_asyncio.fixture(scope="session", autouse=True)
async def prepare_database():
    """Фикстура для БД, создаёт и удаляет таблицы"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def test_session():
    """Фикстура для сессии"""
    async with TestingSessionLocal() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def test_cache_manager():
    """Фикстура для тестового кэша"""
    redis = Redis(
        host=settings.TEST_REDIS_HOST,
        port=settings.TEST_REDIS_PORT,
        decode_responses=False,
    )
    FastAPICache.init(
        RedisBackend(redis),
        prefix="test-cache",
    )
    await redis.flushdb()
    yield redis
    await redis.flushdb()
    await redis.aclose()




@pytest_asyncio.fixture
async def client(test_session):
    """Подмена зависимостей и тестовый клиент"""

    app.dependency_overrides[get_session] = lambda: test_session

    async with AsyncClient(
        transport=ASGITransport(app),
        base_url="http://test",
    ) as ac:
        yield ac
