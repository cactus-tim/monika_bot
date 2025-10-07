from sqlalchemy import select, and_

from database.models import User, async_session
from errors.errors import *
from errors.handlers import db_error_handler


@db_error_handler
async def get_user(tg_id: int):
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.id == tg_id))
        if user:
            return user
        else:
            return None


@db_error_handler
async def create_user(tg_id: int):
    async with async_session() as session:
        user = await get_user(tg_id)
        if not user:
            user_data = User(id=tg_id)
            session.add(user_data)
            await session.commit()
        else:
            raise Error409


@db_error_handler
async def get_all_users():
    async with async_session() as session:
        res = await session.execute(select(User.id))
        return [row[0] for row in res.all()]


@db_error_handler
async def update_user(user_id: int):
    async with async_session() as session:
        user = await get_user(user_id)
        user.is_superuser = True
        session.add(user)
        await session.commit()
