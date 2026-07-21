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
    "am",
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
       "minet",
    "seks",
    "sikihsamiz",
    "kotimga",
    "amimga",
    "oneni",
    "qoto",
    "sik",
    "ам",
    "сикади",
    "жалаб",
    "минет",
    "анал",
    "котогим",
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
        INSERT INTO users(user_id, full_name, username)
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

        result = await db.execute("""
            INSERT INTO groups(chat_id, title)
            VALUES($1, $2)
            ON CONFLICT (chat_id)
            DO NOTHING
        """,
        chat.id,
        chat.title
        )

        return result == "INSERT 0 1"



# ================= START =================


@dp.message(Command("start"))
async def start(message: Message):

    await save_user(message.from_user)

    await message.answer(
        "🛡 Moderator Bot ishga tushdi!"
    )


    if message.chat.type == "private":

        await bot.send_message(
            OWNER_ID,
            f"""
🆕 Yangi foydalanuvchi

👤 Ism: {message.from_user.full_name}
🆔 ID: {message.from_user.id}
📛 Username: @{message.from_user.username or "yo'q"}
"""
        )



# ================= BOT GURUHGA QO'SHILGANDA =================


@dp.my_chat_member()
async def bot_added(event: ChatMemberUpdated):

    if event.chat.type not in ("group", "supergroup"):
        return


    if event.new_chat_member.status in (
        "member",
        "administrator"
    ):

        new = await save_group(event.chat)


        if new:

            await bot.send_message(
                OWNER_ID,
                f"""
🆕 Bot yangi guruhga qo'shildi

👥 Guruh:
{event.chat.title}

🆔 ID:
{event.chat.id}
"""
            )



# ================= ELON YUBORISH (TEXT + PHOTO + VIDEO + DOCUMENT) =================


async def send_to_groups(message: Message):

    async with pool.acquire() as db:

        groups = await db.fetch(
            "SELECT chat_id FROM groups"
        )


    success = 0
    failed = 0


    for group in groups:

        chat_id = group["chat_id"]


        try:

            # RASM
            if message.photo:

                await bot.send_photo(
                    chat_id=chat_id,
                    photo=message.photo[-1].file_id,
                    caption=message.caption
                )


            # VIDEO
            elif message.video:

                await bot.send_video(
                    chat_id=chat_id,
                    video=message.video.file_id,
                    caption=message.caption
                )


            # HUJJAT
            elif message.document:

                await bot.send_document(
                    chat_id=chat_id,
                    document=message.document.file_id,
                    caption=message.caption
                )


            # MATN
            elif message.text:

                text = message.text.replace(
                    "/elon",
                    ""
                ).strip()


                await bot.send_message(
                    chat_id,
                    text
                )


            success += 1


        except Exception:

            failed += 1



    await message.answer(
        f"""
✅ E'lon yuborildi

📢 Guruhlar: {success}
❌ Xato: {failed}
"""
    )



# Oddiy matn uchun

@dp.message(Command("elon"))
async def text_elon(message: Message):

    if message.from_user.id != OWNER_ID:
        return

    await send_to_groups(message)



# Rasm, video, document uchun

@dp.message(F.photo | F.video | F.document)
async def media_elon(message: Message):

    if message.from_user.id != OWNER_ID:
        return

    await send_to_groups(message)



# ================= MODERATOR =================


@dp.message(F.text)
async def moderator(message: Message):

    if message.chat.type not in (
        "group",
        "supergroup"
    ):
        return


    # Har qanday guruhni saqlash
    new = await save_group(message.chat)


    if new:

        await bot.send_message(
            OWNER_ID,
            f"""
🆕 Yangi guruh aniqlandi

👥 {message.chat.title}

🆔 {message.chat.id}
"""
        )


    await save_user(message.from_user)



    member = await bot.get_chat_member(
        message.chat.id,
        message.from_user.id
    )


    if member.status in (
        "administrator",
        "creator"
    ):
        return



    text = message.text.lower()


    clean = re.sub(
        r"\s+",
        "",
        text
    )


    for word in BLACKLIST:

        if word in text:

            await message.delete()


            warn = await message.answer(
                f"🚫 {message.from_user.full_name}, taqiqlangan so'z!"
            )


            await asyncio.sleep(5)

            await warn.delete()

            return



    if LINK_PATTERN.search(clean):

        await message.delete()


        warn = await message.answer(
            f"🚫 {message.from_user.full_name}, link yuborish mumkin emas!"
        )


        await asyncio.sleep(5)

        await warn.delete()



# ================= RUN =================


async def main():

    await init_db()

    await dp.start_polling(bot)



if __name__ == "__main__":

    asyncio.run(main())
