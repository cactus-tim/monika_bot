from aiogram import Router, types, Bot
import asyncio
from aiogram.types import ReplyKeyboardRemove, Message
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramBadRequest, TelegramRetryAfter, TelegramUnauthorizedError, TelegramNetworkError
from functools import wraps
from aiohttp import ClientConnectorError

from instance import logger, bot
from errors.errors import *


router = Router()


def db_error_handler(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Error404 as e:
            logger.exception(str(e))
            return None
        except DatabaseConnectionError as e:
            logger.exception(str(e))
            return None
        except Error409 as e:
            logger.exception(str(e))
            return None
        except Exception as e:
            logger.exception(f"Неизвестная ошибка: {str(e)}")
            return None
    return wrapper


async def safe_send_message(bott: Bot, recipient, text: str, reply_markup=ReplyKeyboardRemove(), retry_attempts=3, delay=5) -> Message:
    """Отправка сообщения с обработкой ClientConnectorError, поддержкой reply_markup и выбором метода отправки."""

    for attempt in range(retry_attempts):
        try:
            if isinstance(recipient, types.Message):
                msg = await recipient.answer(text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
            elif isinstance(recipient, types.CallbackQuery):
                msg = await recipient.message.answer(text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
            elif isinstance(recipient, int):
                msg = await bott.send_message(chat_id=recipient, text=text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
            else:
                raise TypeError(f"Неподдерживаемый тип recipient: {type(recipient)}")

            return msg

        except ClientConnectorError as e:
            logger.error(f"Ошибка подключения: {e}. Попытка {attempt + 1} из {retry_attempts}.")
            if attempt < retry_attempts - 1:
                await asyncio.sleep(delay)
            else:
                logger.error(f"Не удалось отправить сообщение после {retry_attempts} попыток.")
                return None
        except Exception as e:
            logger.error(str(e))
            return None
