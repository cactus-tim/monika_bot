import asyncio
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import (
    Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
)
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramForbiddenError, TelegramBadRequest

from instance import bot, logger
from database.crud import get_all_users, get_user, update_user
from errors.handlers import safe_send_message


router = Router()


@router.message(Command("add_admin"))
async def add_admin(message: Message, state: FSMContext):
    user = await get_user(message.from_user.id)
    if user.id != 483458201:
        return
    id = int(message.text.split(' ')[1])
    await update_user(id)


class Broadcast(StatesGroup):
    text = State()
    ask_photo = State()
    wait_photo = State()
    ask_link = State()
    wait_link_text = State()
    wait_link_url = State()


def yes_no_kb(prefix: str) -> InlineKeyboardMarkup:
    # prefix: 'photo' или 'link'
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="Да", callback_data=f"{prefix}:yes"),
        InlineKeyboardButton(text="Нет", callback_data=f"{prefix}:no"),
    ]])


def build_link_kb(text: str | None, url: str | None) -> InlineKeyboardMarkup | None:
    if not (text and url):
        return None
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=text, url=url)]
    ])


@router.message(Command("send_mes"))
async def cmd_send_mes(message: Message, state: FSMContext):
    user = await get_user(message.from_user.id)
    if not user.is_superuser:
        return

    await state.clear()
    await state.set_state(Broadcast.text)
    await safe_send_message(bot, message,"Введите текст сообщения для рассылки (HTML разрешён):")


@router.message(Broadcast.text, F.text.len() > 0)
async def got_text(message: Message, state: FSMContext):
    await state.update_data(text=message.html_text)
    await state.set_state(Broadcast.ask_photo)
    await safe_send_message(bot, message, "Добавить фото к сообщению?", reply_markup=yes_no_kb("photo"))


@router.message(Broadcast.text)
async def need_text(message: Message, state: FSMContext):
    await safe_send_message(bot, message, "Нужно отправить текст сообщения.")


@router.callback_query(Broadcast.ask_photo, F.data.in_(["photo:yes", "photo:no"]))
async def ask_photo_choice(cq: CallbackQuery, state: FSMContext):
    await cq.answer()
    if cq.data == "photo:yes":
        await state.set_state(Broadcast.wait_photo)
        await safe_send_message(bot, cq, "Отправьте фото одним сообщением (не файлом, а именно фото).")
    else:
        await state.update_data(photo_id=None)
        await state.set_state(Broadcast.ask_link)
        await safe_send_message(bot, cq, "Добавить кнопку-ссылку?", reply_markup=yes_no_kb("link"))


@router.message(Broadcast.wait_photo, F.photo)
async def got_photo(message: Message, state: FSMContext):
    file_id = message.photo[-1].file_id
    await state.update_data(photo_id=file_id)
    await state.set_state(Broadcast.ask_link)
    await safe_send_message(bot, message, "Добавить кнопку-ссылку?", reply_markup=yes_no_kb("link"))


@router.message(Broadcast.wait_photo)
async def need_photo(message: Message, state: FSMContext):
    await safe_send_message(bot, message, "Пожалуйста, отправьте фото (тип «фото», не документ).")


@router.callback_query(Broadcast.ask_link, F.data.in_(["link:yes", "link:no"]))
async def ask_link_choice(cq: CallbackQuery, state: FSMContext):
    await cq.answer()
    if cq.data == "link:yes":
        await state.set_state(Broadcast.wait_link_text)
        await safe_send_message(bot, cq, "Введите надпись на кнопке (текст кнопки):")
    else:
        await state.update_data(link_text=None, link_url=None)
        await do_broadcast(cq.message, state)


@router.message(Broadcast.wait_link_text, F.text.len() > 0)
async def got_link_text(message: Message, state: FSMContext):
    await state.update_data(link_text=message.text.strip())
    await state.set_state(Broadcast.wait_link_url)
    await safe_send_message(bot, message, "Отправьте ссылку (URL), например: https://example.com")


@router.message(Broadcast.wait_link_url, F.text.regexp(r"https?://\S+"))
async def got_link_url(message: Message, state: FSMContext):
    await state.update_data(link_url=message.text.strip())
    await do_broadcast(message, state)


@router.message(Broadcast.wait_link_url)
async def need_link(message: Message, state: FSMContext):
    await safe_send_message(bot, message, "Нужен корректный URL, например: https://example.com")


async def do_broadcast(origin_msg: Message, state: FSMContext):
    data = await state.get_data()
    text: str = data.get("text", "")
    photo_id: str | None = data.get("photo_id")
    link_text: str | None = data.get("link_text")
    link_url: str | None = data.get("link_url")

    kb = build_link_kb(link_text, link_url)

    sent = 0
    failed = 0

    await origin_msg.answer("Начинаю рассылку…")

    users = await get_all_users()

    for uid in users:
        try:
            if photo_id:
                await bot.send_photo(
                    chat_id=uid,
                    photo=photo_id,
                    caption=text,
                    parse_mode="HTML",
                    reply_markup=kb
                )
            else:
                await bot.send_message(
                    chat_id=uid,
                    text=text,
                    parse_mode="HTML",
                    reply_markup=kb
                )
            sent += 1
            await asyncio.sleep(0.03)
        except (TelegramForbiddenError, TelegramBadRequest) as e:
            failed += 1
            logger.warning(f"Broadcast to {uid} failed: {e!r}")
        except Exception as e:
            failed += 1
            logger.exception(f"Broadcast to {uid} unexpected error: {e!r}")

    await state.clear()
    await origin_msg.answer(f"Готово. Успешно: {sent}, ошибок: {failed}.")
