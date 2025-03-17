from pydantic_settings import BaseSettings
from pydantic import ConfigDict


class Settings(BaseSettings):
    SERVER_HOST: str
    SERVER_PORT: int

    SECRET_KEY: str
    SECRET_KEY_ADMIN: str
    SECRET_KEY_EMAIL: str
    SECRET_KEY_BOT: str
    ALGORITHM: str = "HS256"

    STATIC_DIR: str = "static"

    S3_HOST: str
    S3_BACKET: str
    S3_ACCESS_KEY: str
    S3_SECRET_KEY: str

    DB_USER: str
    DB_PASSWORD: str
    DB_HOST: str
    DB_PORT: int
    DB_NAME: str

    REDIS_HOST: str
    REDIS_PORT: int

    MAIL_USERNAME: str
    MAIL_PASSWORD: str
    MAIL_FROM: str
    MAIL_PORT: int
    MAIL_SERVER: str

    RMQ_HOST: str
    RMQ_PORT: int
    RMQ_PLAGIN_PORT: int
    RMQ_USER: str
    RMQ_PASSWORD: str

    TEST_DB_USER: str
    TEST_DB_PASSWORD: str
    TEST_DB_HOST: str
    TEST_DB_PORT: int
    TEST_DB_NAME: str

    TEST_REDIS_HOST: str
    TEST_REDIS_PORT: int

    model_config = ConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = Settings()
