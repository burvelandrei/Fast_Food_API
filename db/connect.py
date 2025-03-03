from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from environs import Env


env = Env()
env.read_env()


DATABASE_URL = (
    f"postgresql+asyncpg://{env("DB_USER")}:{env("DB_PASSWORD")}@"
    f"{env("DB_HOST")}:{env("DB_PORT")}/{env("DB_NAME")}"
)


engine = create_async_engine(url=DATABASE_URL, echo=False)


AsyncSessionLocal = async_sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False
)

# Функция для получения объекта сессии
async def get_session():
    async with AsyncSessionLocal() as session:
        yield session
