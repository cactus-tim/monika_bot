import asyncio
import re
from aiogram.filters import CommandStart
from aiogram import Router, F
from aiogram.types import Message, FSInputFile
from errors.handlers import safe_send_message
from aiogram.exceptions import TelegramForbiddenError, TelegramBadRequest
from aiogram.utils.deep_linking import create_start_link

from instance import bot, logger
from database.crud import *

router = Router()


welcome_text = """
Спасибо за заказ🤍

Несколько простых правил, которые позволят максимально насладиться клубникой в шоколаде🍓

- Десерт хранится в течение 24 часов. Рекомендуем употребить в первые 12 часов. 
- Хранить клубнику в шоколаде необходимо в холодильнике. 
- Если вы любите нежный, чуть подтаявший шоколад, рекомендуем после холодильника подержать клубнику при комнатной температуре в течение 15 минут.
- Для любителей «похрустеть», можно смело пробовать сразу. Шоколад может трескаться во время употребления, это нормальное состояние для шоколада. 
*при длительном хранении в холодильнике (от 6ч) клубника может дать сок, это тоже нормально, так как сочная ягода дышит. 

Приятного аппетита✨
<a href="https://t.me/monika_spb_berry">MONIKA 🍓</a>.
"""


@router.message(CommandStart())
async def cmd_start(message: Message):
    user = await get_user(message.from_user.id)
    if not user:
        await create_user(message.from_user.id)
    photo = FSInputFile("monika_main_photo.jpeg")
    await bot.send_photo(
        chat_id=message.from_user.id,
        photo=photo,
        caption=welcome_text,
        parse_mode="HTML"
    )
