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
from utils.redis_connect import get_redis
from config import settings


# Настройки PostgreSQL
TEST_DATABASE_URL = (
    f"postgresql+asyncpg://test_user:test_password@"
    f"localhost:5432/test_name"
)
engine = create_async_engine(TEST_DATABASE_URL, echo=True)
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
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
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
async def test_redis():
    """Фикстура для тестового редиса"""
    redis = Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        decode_responses=True,
    )
    await redis.flushdb()
    yield redis
    await redis.flushdb()
    await redis.aclose()


@pytest_asyncio.fixture(autouse=True)
def override_secret_keys():
    """
    Фикстура для переопределения SECRET_KEY на время тестов
    """
    original_keys = {
        "SECRET_KEY": settings.SECRET_KEY,
        "SECRET_KEY_EMAIL": settings.SECRET_KEY_EMAIL,
        "SECRET_KEY_BOT": settings.SECRET_KEY_BOT,
    }

    settings.SECRET_KEY = "test-secret-key"
    settings.SECRET_KEY_EMAIL = "test-secret-key-email"
    settings.SECRET_KEY_BOT = "test-secret-key-bot"

    yield

    settings.SECRET_KEY = original_keys["SECRET_KEY"]
    settings.SECRET_KEY_EMAIL = original_keys["SECRET_KEY_EMAIL"]
    settings.SECRET_KEY_BOT = original_keys["SECRET_KEY_BOT"]


@pytest_asyncio.fixture
async def client(test_session, test_redis):
    """Подмена зависимостей и тестовый клиент"""
    app.dependency_overrides[get_session] = lambda: test_session
    app.dependency_overrides[get_redis] = lambda: test_redis

    async with AsyncClient(
        transport=ASGITransport(app),
        base_url="http://test",
    ) as ac:
        yield ac
