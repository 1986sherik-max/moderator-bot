import asyncio
import os
import re
import asyncpg

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, ChatMemberUpdated


TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")

OWNER_ID = 711427177


bot = Bot(token=TOKEN)
dp = Dispatcher()

pool = None


LINK_PATTERN = re.compile(
    r"(https?://|www\.|t\.me|telegram\.me|@\w+|[a-zA-Z0-9_-]+\.(ru|com|uz))",
    re.IGNORECASE
)


BLACKLIST = [
    "minet",
    "porno",
    "kotmisan",
    "bukmeker",
    "jalab",
    "jallab",
    "kot",
    "aminga",
    "suka",
    "dalbayop",
    "suchara",
    "pidaraz",
    "ami",
    "qotagim",
]


# ================= DATABASE =================


async def init_db():

    global pool

    pool = await asyncpg.create_pool(DATABASE_URL)

    async with pool.acquire() as db:

        await db.execute("""
        CREATE TABLE IF NOT EXISTS users(
            user_id BIGINT PRIMARY KEY,
            full_name TEXT,
            username TEXT
        )
        """)


        await db.execute("""
        CREATE TABLE IF NOT EXISTS groups(
            chat_id BIGINT PRIMARY KEY,
            title TEXT
        )
        """)



async def save_user(user):

    async with pool.acquire() as db:

        await db.execute("""
        INSERT INTO users
        VALUES($1,$2,$3)
        ON CONFLICT(user_id)
        DO NOTHING
        """,
        user.id,
        user.full_name,
        user.username
        )



async def save_group(chat):

    async with pool.acquire() as db:

        check = await db.fetchrow(
            "SELECT chat_id FROM groups WHERE chat_id=$1",
            chat.id
        )


        if not check:

            await db.execute("""
            INSERT INTO groups
            VALUES($1,$2)
            """,
            chat.id,
            chat.title
            )

            return True


    return False
