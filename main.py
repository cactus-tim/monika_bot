import asyncio

from aiogram import Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from confige import BotConfig
from handlers import user, admin
from instance import bot
from database.models import async_main


def register_routers(dp: Dispatcher) -> None:
    dp.include_routers(admin.router, user.router)


async def main() -> None:
    await async_main()

    config = BotConfig(
        admin_ids=[],
        welcome_message=""
    )
    dp = Dispatcher(storage=MemoryStorage())
    dp["config"] = config

    register_routers(dp)

    try:
        await asyncio.gather(
            dp.start_polling(bot, skip_updates=True),
        )
    except Exception as _ex:
        print(f'Exception: {_ex}')


if __name__ == '__main__':
    asyncio.run(main())
