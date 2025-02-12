import asyncio
import logging

from environs import Env
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram_dialog import setup_dialogs
from aiogram.fsm.storage.redis import RedisStorage, DefaultKeyBuilder


env = Env()
env.read_env()


# Настраиваем логгер
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Функция конфигурирования и запуска бота
async def main() -> None:

    # Выводим в консоль информацию о начале запуска
    logger.info("Starting BOTV")

    # Инициализируем бот, редис и диспетчер
    bot: Bot = Bot(
        token=env("BOT_TOKEN"), default=DefaultBotProperties(parse_mode="HTML")
    )
    storage = RedisStorage.from_url(
        f'redis://{env("REDIS_HOST")}:{env("REDIS_PORT")}/0',
        key_builder=DefaultKeyBuilder(with_destiny=True),
    )
    dp: Dispatcher = Dispatcher(storage=storage)

    # Регистриуем роутеры в диспетчере
    dp.include_router()
    setup_dialogs(dp)

    # Пропускаем накопившиеся апдейты и запускаем polling
    await bot.delete_webhook(drop_pending_updates=True)
    try:
        await dp.start_polling(bot)
    except Exception as e:
        logging.error(f"[Exception] - {e}", exc_info=True)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
